"""
MCP Agent Monolith: A tool for generating and executing automated Playwright tests based on LLM-generated test plans.

This script provides functionality to:
1. Fetch a website's page source
2. Generate a test plan using an LLM (Anthropic or OpenAI)
3. Execute the test plan using a Playwright service
4. Analyze and report test results

Usage:
    python main.py <url> <test_description> [options]

Author: QE AI Agent Swarm Team
"""

import asyncio
import argparse
import json
import os
from typing import Dict, Any, Optional

import httpx
from mcp_agent.app import MCPApp
from mcp_agent.agents.agent import Agent
from mcp_agent.workflows.llm.augmented_llm_anthropic import AnthropicAugmentedLLM
from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM

# Configuration constants with default values
DEFAULT_PLAYWRIGHT_URL = "http://localhost:8000"  # URL for Playwright service
DEFAULT_OUTPUT_DIR = "output"                     # Directory to store test artifacts
DEFAULT_TIMEOUT = 300.0                           # Request timeout in seconds
DEFAULT_MAX_RETRIES = 1                           # Maximum retry attempts for API calls
DEFAULT_LLM_PROVIDER = "anthropic"                # Default LLM provider

# Initialize the MCP application
app = MCPApp(name="mcp-agent-mono")

class TestExecutionError(Exception):
    """Custom exception raised for errors during test execution.
    
    This helps distinguish between different types of errors during the test process
    and provides more specific error handling.
    """
    pass

async def fetch_page_source(client: httpx.AsyncClient, playwright_url: str, url: str, logger: Any) -> str:
    """Fetch the page source from the Playwright service.
    
    Args:
        client: HTTP client for making requests
        playwright_url: URL of the Playwright service
        url: Target website URL to fetch
        logger: Logger instance for recording events
        
    Returns:
        The page source HTML as a string
        
    Raises:
        TestExecutionError: If page source fetching fails
    """
    try:
        # Send a POST request to the Playwright service to navigate to the URL
        response = await client.post(f"{playwright_url}/navigate", json={"url": url})
        response.raise_for_status()
        page_source = response.text
        logger.info(f"200 :: Successfully fetched page source")
        return page_source
    except httpx.RequestError as e:
        # Handle network-related errors
        logger.error(f"400 :: Failed to fetch page source: {e}")
        raise TestExecutionError(f"Failed to fetch page source: {str(e)}")
    except httpx.HTTPStatusError as e:
        # Handle HTTP status errors (4xx, 5xx)
        logger.error(f"400 :: HTTP error: {e.response.status_code} - {e}")
        raise TestExecutionError(f"HTTP {e.response.status_code} error: {str(e)}")

async def generate_test_plan(llm: OpenAIAugmentedLLM, url: str, page_source: str, test_description: str, logger: Any) -> Dict[str, Any]:
    """Generate a test plan using the provided LLM.
    
    Args:
        llm: LLM instance for generating test plans
        url: Target website URL for testing
        page_source: HTML source of the target website
        test_description: Description of the test requirements
        logger: Logger instance for recording events
        
    Returns:
        A dictionary containing the generated test plan
        
    Raises:
        TestExecutionError: If JSON parsing fails
    """
    logger.info(f"Generating test plan for {url} using page source and description: {test_description}")
    
    # Prompt the LLM to generate a test plan based on the page source and requirements
    plan_result = await llm.generate_str(
        message=f"""Create a test plan for {url}
        using Playwright CSS selector rules like button:has-text("Submit") or #elementID
        ONLY using these list of elements {page_source}
        with the following requirements:
        {test_description}
        
        Before you start ensure the description is clear and concise and traslate into a sentece is Given When Then format.

        Return ONLY a JSON object with the following structure:
        {{
          "url": "https://devops1.com.au",
          "test_plan": {{
            "description": "Brief description of the test",
            "steps": [
                {{
                "action": "navigate|click|type|wait|waitForLoadState|scroll|check|screenshot",
                "selector": "CSS selector or XPath (not needed for navigate/wait actions)",
                "value": "Value for type actions or URL for navigate"
                }}
            ]
          }}
        }}
        
        Don't include anything else in your response - just the JSON.
        IMPORTANT: 
        - In Validations are required ensure the check action is used with the value as the expected result.
        - Do not deviate from the list of elements provided, if elements are not provided finish the workflow.
        - only return the JSON object with the test plan.
        - Do not include any explanations or additional text.
        - Do not include any code blocks or formatting.
        """
    )
    
    # Parse the JSON response from the LLM
    try:
        plan_json = json.loads(plan_result)
        return plan_json
    except json.JSONDecodeError as e:
        logger.error(f"400 :: Failed to decode JSON from LLM response: {e}")
        raise TestExecutionError(f"Failed to decode JSON from LLM response: {str(e)}")

def save_test_plan(plan_json: Dict[str, Any], output_dir: str, logger: Any) -> None:
    """Save the test plan to a file.
    
    Args:
        plan_json: The test plan as a JSON object
        output_dir: Directory to save the test plan
        logger: Logger instance for recording events
        
    Raises:
        TestExecutionError: If saving fails
    """
    try:
        # Create the output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "plan.json")
        
        # Write the test plan to a JSON file
        with open(output_path, "w") as f:
            json.dump(plan_json, f, indent=2)
        logger.info(f"Test plan saved to {output_path}")
    except Exception as e:
        logger.error(f"400 :: Failed to save test plan: {e}")
        raise TestExecutionError(f"Failed to save test plan: {str(e)}")

def validate_test_plan(plan_json: Dict[str, Any], logger: Any) -> None:
    """Validate the test plan structure.
    
    Args:
        plan_json: The test plan to validate
        logger: Logger instance for recording events
        
    Raises:
        TestExecutionError: If validation fails
    """
    # Check that the plan has the required structure
    if not plan_json or "test_plan" not in plan_json:
        logger.error("Invalid test plan structure")
        raise TestExecutionError("Invalid test plan structure")
    
    # Check that the plan has steps
    if "steps" not in plan_json["test_plan"]:
        logger.error("Test plan does not contain steps")
        raise TestExecutionError("Test plan does not contain steps")

async def execute_test_plan(
    client: httpx.AsyncClient, 
    playwright_url: str, 
    test_plan: Dict[str, Any], 
    max_retries: int, 
    timeout: float,
    logger: Any
) -> Dict[str, Any]:
    """Execute the test plan using the Playwright service.
    
    Args:
        client: HTTP client for making requests
        playwright_url: URL of the Playwright service
        test_plan: Test plan to execute
        max_retries: Maximum number of retry attempts
        timeout: Request timeout in seconds
        logger: Logger instance for recording events
        
    Returns:
        A dictionary containing the test results
        
    Raises:
        TestExecutionError: If execution fails
    """
    logger.info("Executing test plan with Playwright service")
    logger.debug(f"Sending request to Playwright API at {playwright_url}/execute")
    
    retry_count = 0
    
    # Retry loop for handling transient errors
    while retry_count <= max_retries:
        try:
            # Send the test plan to the Playwright service for execution
            response = await client.post(
                f"{playwright_url}/execute",
                json=test_plan,
                timeout=timeout
            )
            
            logger.debug(f"Received response with status code: {response.status_code}")
            
            # Handle special case for 422 error (usually indicates JSON formatting issues)
            if response.status_code == 422:
                error_details = response.json() if response.content else "No error details provided"
                logger.error(f"Playwright API rejected the request with 422 Unprocessable Entity: {error_details}")
                
                if retry_count < max_retries:
                    logger.info(f"Attempting to retry request ({retry_count + 1}/{max_retries})")
                    retry_count += 1
                    continue
                else:
                    raise TestExecutionError(f"Playwright API rejected the request: {error_details}")
            
            # Check for other HTTP errors
            response.raise_for_status()
            
            # Parse the test results
            results = response.json()
            logger.info("Successfully executed test plan")
            logger.debug(f"Raw results: {json.dumps(results, indent=2)}")
            
            return results
        
        except httpx.TimeoutException:
            # Handle request timeout
            logger.warning(f"Request timed out. Retry {retry_count + 1}/{max_retries}")
            retry_count += 1
            if retry_count > max_retries:
                raise TestExecutionError("Request to Playwright API timed out after multiple attempts")
        
        except httpx.HTTPStatusError as e:
            # Handle HTTP errors
            logger.error(f"HTTP error: {e.response.status_code} - {e}")
            
            # Try to extract detailed error information from the response
            try:
                error_content = e.response.json()
                logger.error(f"Error response: {json.dumps(error_content, indent=2)}")
            except Exception:
                logger.error(f"Error response content: {e.response.text}")
            
            # Don't retry client errors (4xx) except for 429 (Too Many Requests)
            if 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                raise TestExecutionError(f"HTTP {e.response.status_code} error: {str(e)}")
            
            retry_count += 1
            if retry_count > max_retries:
                raise TestExecutionError(f"Failed after {max_retries} retries: {str(e)}")
            logger.info(f"Retrying request ({retry_count}/{max_retries})...")

async def analyze_results(llm: OpenAIAugmentedLLM, results: Dict[str, Any], logger: Any) -> str:
    """Analyze the test results using the LLM.
    
    Args:
        llm: LLM instance for analyzing results
        results: Test results to analyze
        logger: Logger instance for recording events
        
    Returns:
        A string containing the analysis
    """
    # Ask the LLM to analyze the test results
    analysis = await llm.generate_str(
        message=f"Create a markdown file in the output folder and Analyze these test results and provide a summary:\n{json.dumps(results, indent=2)}"
    )
    
    logger.info("Test results analyzed")
    return analysis

async def get_llm_instance(agent: Agent, llm_provider: str) -> OpenAIAugmentedLLM:
    """Get an instance of the selected LLM provider.
    
    Args:
        agent: Agent to attach the LLM to
        llm_provider: Name of the LLM provider to use
        
    Returns:
        An instance of the selected LLM
    """
    # Select the appropriate LLM provider based on the configuration
    if llm_provider.lower() == "anthropic":
        return await agent.attach_llm(AnthropicAugmentedLLM)
    elif llm_provider.lower() == "openai":
        return await agent.attach_llm(OpenAIAugmentedLLM)
    else:
        # Default to Anthropic if provider is not recognized
        return await agent.attach_llm(AnthropicAugmentedLLM)

async def run_test_on_website(
    url: str, 
    test_description: str, 
    playwright_url: str = DEFAULT_PLAYWRIGHT_URL,
    output_dir: str = DEFAULT_OUTPUT_DIR,
    timeout: float = DEFAULT_TIMEOUT,
    max_retries: int = DEFAULT_MAX_RETRIES,
    llm_provider: str = DEFAULT_LLM_PROVIDER
) -> Dict[str, Any]:
    """Run tests on a website using the Playwright service based on a prompt.
    
    This is the main function that orchestrates the entire testing process.
    
    Args:
        url: Target website URL to test
        test_description: Description of the test requirements
        playwright_url: URL of the Playwright service
        output_dir: Directory to save test artifacts
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts for API calls
        llm_provider: LLM provider to use (anthropic or openai)
        
    Returns:
        A dictionary containing the test plan, results, and analysis
    """
    # Start the MCP application
    async with app.run() as mcp_agent_app:
        logger = mcp_agent_app.logger
        
        # Create a test automation agent
        test_agent = Agent(
            name="tester",
            instruction="""You are a Test Automation Expert. 
                You can create test plans based on a given URL and description.
                Important:
                - Focus on creating detailed step-by-step test plans that can be executed by a Playwright testing service.
                - When traslating from Actions to JSON only use these actions: navigate, click, type, wait, waitForLoadState, scroll, check, screenshot
                - The test plans should be JSON objects with a description and array of steps.
                - Review existing test analysis and results to improve your test plans from the output folder.
                """,
            server_names=["fetch", "filesystem"]
        )

        try:
            # Start the test agent
            async with test_agent:
                # List available tools
                tools = await test_agent.list_tools()
                logger.info("Tools available:", data=tools)

                # Create HTTP client for API calls
                async with httpx.AsyncClient() as client:
                    # Fetch page source
                    page_source = await fetch_page_source(client, playwright_url, url, logger)
                    
                    # Connect to the specified LLM
                    llm = await get_llm_instance(test_agent, llm_provider)
                    
                    # Generate test plan
                    plan_json = await generate_test_plan(llm, url, page_source, test_description, logger)
                    
                    # Save the test plan
                    save_test_plan(plan_json, output_dir, logger)
                    
                    # Validate the test plan
                    validate_test_plan(plan_json, logger)
                    
                    # Execute the test plan
                    results = await execute_test_plan(
                        client, 
                        playwright_url, 
                        plan_json, 
                        max_retries, 
                        timeout,
                        logger
                    )
                    
                    # Analyze the results
                    analysis = await analyze_results(llm, results, logger)
                    
                    # Return the complete test data
                    return {
                        "test_plan": plan_json,
                        "results": results,
                        "analysis": analysis
                    }
                    
        except TestExecutionError as e:
            # Handle test execution errors
            logger.error(f"Test execution error: {e}")
            return {"error": str(e)}
        except Exception as e:
            # Handle unexpected errors
            logger.error(f"Unexpected error: {e}", exc_info=True)
            return {"error": f"Unexpected error: {str(e)}"}

# Script entry point
if __name__ == "__main__":
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description="Run website tests with Playwright")
    parser.add_argument("url", type=str, help="The URL to test")
    parser.add_argument("description", type=str, help="Description of what to test")
    parser.add_argument("--playwright-url", type=str, default=DEFAULT_PLAYWRIGHT_URL, 
                        help=f"Playwright service URL (default: {DEFAULT_PLAYWRIGHT_URL})")
    parser.add_argument("--output-dir", type=str, default=DEFAULT_OUTPUT_DIR,
                        help=f"Directory for output files (default: {DEFAULT_OUTPUT_DIR})")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT,
                        help=f"Request timeout in seconds (default: {DEFAULT_TIMEOUT})")
    parser.add_argument("--max-retries", type=int, default=DEFAULT_MAX_RETRIES,
                        help=f"Maximum number of retry attempts (default: {DEFAULT_MAX_RETRIES})")
    parser.add_argument("--llm-provider", type=str, default=DEFAULT_LLM_PROVIDER, choices=["anthropic", "openai"],
                        help=f"LLM provider to use (default: {DEFAULT_LLM_PROVIDER})")
    
    # Parse command line arguments
    args = parser.parse_args()

    # Run the test and get the results
    result = asyncio.run(run_test_on_website(
        args.url, 
        args.description,
        args.playwright_url,
        args.output_dir,
        args.timeout,
        args.max_retries,
        args.llm_provider
    ))
