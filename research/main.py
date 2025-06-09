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
# Default LLM provider
DEFAULT_LLM_PROVIDER = "anthropic" 

# Research policy from policies folder
RESEARCH_POLICY = "./policies/market_research_policy.md"

# Initialize the MCP application
app = MCPApp(name="mcp-research-agent")

async def research_agent():
    async with app.run() as agent_app:
        logger = agent_app.logger
        context = agent_app.context

        logger.info("Current config:", data=context.config.model_dump())

        research_agent = Agent(
            name="ResearchAgent",
            instruction="""
                You are an agent specialized in conducting research on various topics.
                You will be provided with topics to research and will generate comprehensive reports.
                Your reports should include the latest information, key findings, and references.
                You will also have access to tools for fetching data and storing results.
                Ensure your reports are well-structured and informative.
                Use the tools available to gather information and generate reports.
                You can also use the filesystem to store your research reports.
            """,
            server_names=["fetch", "filesystem"]
        )

        async with research_agent:
            # Check if the research agent is available
            result = await research_agent.list_tools()
            logger.info("Tools available:", data=result.model_dump())

            # Connect to LLM
            llm = await research_agent.attach_llm(AnthropicAugmentedLLM)

            # Input topic for research
            topic = input("Enter the topic you want to research: ").strip()
            if not topic:
                logger.error("No topic provided for research.")
                return
            logger.info(f"Researching topic: {topic}")
            
            # Load research policy
            policy = RESEARCH_POLICY
            logger.info(f"Loading research policy from: {policy}")

            result = await llm.generate_str(
                message=f"""
                Conduct a detailed market research analysis on {topic}. Focus on their maturity, initiatives, challenges, and public statements related to:
	            
                1.	DevOps practices (e.g., CI/CD adoption, platform engineering, SRE, automation, release management, observability).
	            2.	Digital immunity (e.g., proactive resilience, chaos engineering, automated testing, incident response, security engineering, error budgets).

                Include the following in your analysis:
                    •	Last 12 months public announcements, blog posts, or whitepapers.
                    •	Partnerships or vendors used (e.g., LaunchDarkly, Datadog, GitHub, Azure DevOps, etc.).
                    •	Known use of AI/ML in engineering or ops.
                    •	Job postings that indicate internal capabilities or priorities.
                    •	Any known transformation programmes or digital strategies.

                Provide citations and URLs where applicable, summarise insights clearly, and identify gaps or opportunities where consulting support could be positioned.

                Follow the research policy {policy} and ensure that your report adheres to the guidelines provided.

                Use the example reports as a guide for structure and content, and save in the output directory.
                """,
            )
            logger.info(f"Project results: {result}")            

if __name__ == "__main__":
    start = time.time()
    asyncio.run(research_agent())
    end = time.time()
    t = end - start

    print(f"Total run time: {t:.2f}s")