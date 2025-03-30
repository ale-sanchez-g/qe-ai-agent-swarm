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
                Save the report in the file system.
                """,
            )
            logger.info(f"Project review: {result}")
            


if __name__ == "__main__":
    start = time.time()
    asyncio.run(check_jira_projects())
    end = time.time()
    t = end - start

    print(f"Total run time: {t:.2f}s")

