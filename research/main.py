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

# Initialize the MCP application
app = MCPApp(name="mcp-research-planner")

async def research_agent():
    async with app.run() as agent_app:
        logger = agent_app.logger
        context = agent_app.context

        logger.info("Current config:", data=context.config.model_dump())

if __name__ == "__main__":
    start = time.time()
    asyncio.run(research_agent())
    end = time.time()
    t = end - start

    print(f"Total run time: {t:.2f}s")