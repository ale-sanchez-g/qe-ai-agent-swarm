"""
MCP Agent Planner: 
"""

import asyncio
import argparse
import json
import os
import time
from typing import Dict, Any, Optional

import httpx
from mcp_agent.app import MCPApp
from mcp_agent.agents.agent import Agent
from mcp_agent.workflows.llm.augmented_llm import RequestParams
from mcp_agent.workflows.llm.llm_selector import ModelPreferences
from mcp_agent.workflows.llm.augmented_llm_anthropic import AnthropicAugmentedLLM


# Configuration constants with default values

DEFAULT_LLM_PROVIDER = "anthropic"                # Default LLM provider

# Initialize the MCP application
app = MCPApp(name="mcp-agent-planner")

async def check_jira_projects():
    async with app.run() as agent_app:
        logger = agent_app.logger
        context = agent_app.context

        logger.info("Current config:", data=context.config.model_dump())

        jira_agent = Agent(
            name="JiraChecker",
            instruction="""
                You are an agent with access to JIRA and Confluence
                You will be provided with questions and task to complete as an Certified Agile Coach.
            """,
            server_names=["mcp-atlassian", "filesystem"]
        )

        async with jira_agent:
            logger.info("Connected to JIRA server, fetching projects...")
            result = await jira_agent.list_tools()
            logger.info("Tools available:", data=result.model_dump())

            # Check if the JIRA server is available
            if not result:
                logger.error("JIRA server is not available.")
                return
           
        async with jira_agent:
            logger.info("finder: Connected to server, calling list_tools...")
            result = await jira_agent.list_tools()
            logger.info("Tools available:", data=result.model_dump())

            # Connect to LLM
            llm = await jira_agent.attach_llm(AnthropicAugmentedLLM)

            result = await llm.generate_str(
                message="""
                Go to JIRA and review any open issues in projects SUP and MCP.
                """,
            )
            logger.info(f"Project results: {result}")

            #  Create subttasks for each Issue in the MCP project
            result = await llm.generate_str(
                message=f"""
                Given you are a Certified Agile Quality Engineer 
                review Task MCP-1 and create sub-tasks base on the following principles:

                1. Each sub-task should be a small
                manageable piece of work that can be completed in a short time frame.
                2. Each sub-task should be clearly defined and have a specific goal.
                3. Each sub-task should be independent and not rely on other tasks.
                4. Each sub-task should be testable and have clear acceptance criteria.
                5. Each sub-task should have a clear priority level.
                6. If the issues already have sub-tasks, only create new sub-tasks if they are necessary.

                
                IMPORTANT:
                - Do not create sub-tasks for issues that are already closed.
                - Do not create sub-tasks for issues that are not in the MCP project.
                - Only Create sub-tasks for Quality Engineering.
                    - Create a test approach as a sub-task, using Shift Left Testing and Testing Pyramid.
                    - Create an environment and test data strategy as a sub-task.
                    - Based on the test approach, individual test experiments with clear oobjectives, using the Scientific Method.
                - Do not create sub-tasks for issues that are not related to Quality Engineering.
                - Ensure to use the correct format when creating sub-tasks.
                """,
            )
            logger.info(f"Sub-tasks created: {result}")
            #  Create subttasks for each Issue in the SUP project

            # Multi-turn conversations - review the result
            result = await llm.generate_str(
                message=f"""
                Review the file {result} and search what issues have been raised for each project:
                
                Example:
                PROJECT ABC
                - ABC-123: Issue 1
                - ABC-456: Issue 2

                PROJECT DEF
                - DEF-123: Issue 1
                - DEF-456: Issue 2


                Provide a summary of the issues and their status in a markdown report.
                If you had any problems, please include them in the report.
                Save the report in the file system.
                IMPORTANT:
                - Do not include any personal information.
                - Do not include any sensitive information.
                - Do not include any confidential information.
                - Save with the time and date of the report.

                Create a separate file for with any errors or problems you had, with details of the error.
                Save the errors in the file system.
                Example:
                    ERRORS:
                    - Error 1: Description of the error
                      API call failed
                      Details: <details of the error>
                      Response: <response of the error>
                      Root cause: <root cause of the error>
                """,
            )
            logger.info(f"Project review: {result}")
            


if __name__ == "__main__":
    start = time.time()
    asyncio.run(check_jira_projects())
    end = time.time()
    t = end - start

    print(f"Total run time: {t:.2f}s")

