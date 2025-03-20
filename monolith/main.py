import asyncio
import argparse
import json
import httpx
from mcp_agent.app import MCPApp
from mcp_agent.agents.agent import Agent
from mcp_agent.workflows.llm.augmented_llm_anthropic import AnthropicAugmentedLLM

app = MCPApp(name="mcp-puppet")

# URL to the Playwright service
PLAYWRIGHT_URL = "http://localhost:8000"  # Change if accessing through Docker network

async def run_test_on_website(url: str, test_description: str):
    """Run tests on a website using the Playwright service based on a prompt."""
    async with app.run() as mcp_agent_app:
        logger = mcp_agent_app.logger
        
        # This agent can read the filesystem or fetch URLs and visit websites
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

        async with test_agent:
            # List available tools
            tools = await test_agent.list_tools()
            logger.info("Tools available:", data=tools)

            # Navigate to playwrigth service navigate path to get the page source
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(f"{PLAYWRIGHT_URL}/navigate", json={"url": url})                    
                    response.raise_for_status()
                    page_source = response.text
                    logger.info(f"200 :: Successfully fetched page source      {page_source}")
            except httpx.RequestError as e:
                logger.error(f"400 :: Failed to fetch page source: {e}")
                return {"error": f"Failed to fetch page source: {str(e)}"}
            except httpx.HTTPStatusError as e:
                logger.error(f"400 :: HTTP error: {e.response.status_code} - {e}")
                return {"error": f"HTTP {e.response.status_code} error: {str(e)}"}

    

            # Connect to Anthropic's LLM
            llm = await test_agent.attach_llm(AnthropicAugmentedLLM)

            # First, have the LLM generate a test plan based on the URL and description
            logger.info(f"Generating test plan for {url} ONLY using these list of elements {page_source} using Playwright selector rules with instructions: {test_description}")
            plan_result = await llm.generate_str(
                            message=f"""Create a test plan for {url}
                            using Playwright CSS selector rules like button:has-text("Submit") or #elementID
                            ONLY using these list of elements {page_source}
                            with the following requirements:
                            {test_description}
                            
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
                            - Do not deviate from the list of elements provided, if elements are not provided finish the workflow.
                            - only return the JSON object with the test plan.
                            - Do not include any explanations or additional text.
                            - Do not include any code blocks or formatting.
                            """
                        )
            # Save plan on filesystem
            logger.info(f"200 :: Test plan generated: {plan_result}")
            try:
                plan_json = json.loads(plan_result)
                with open("output/plan.json", "w") as f:

                    json.dump(plan_json, f, indent=2)
                logger.info("Test plan saved to output/plan.json")
            except json.JSONDecodeError as e:
                logger.error(f"400 :: Failed to decode JSON from LLM response: {e}")
                return {"error": f"Failed to decode JSON from LLM response: {str(e)}"}
            except Exception as e:
                logger.error(f"400 :: Failed to save test plan: {e}")
                return {"error": f"Failed to save test plan: {str(e)}"}
            # Check if the test plan is valid
            if not plan_json or "test_plan" not in plan_json:
                logger.error("Invalid test plan structure")
                return {"error": "Invalid test plan structure"}
            if "steps" not in plan_json["test_plan"]:
                logger.error("Test plan does not contain steps")
                return {"error": "Test plan does not contain steps"}
           
            # Execute the test plan using the Playwright service
            logger.info("Executing test plan with Playwright service")
            try:
                async with httpx.AsyncClient() as client:
                    # Debug the request payload with better formatting
                    logger.debug(f"Sending request to Playwright API at {PLAYWRIGHT_URL}/execute")
                    
                    # Add better error handling with retries
                    max_retries = 1
                    retry_count = 0
                    
                    # Get test plan from the output folder
                    with open("output/plan.json", "r") as f:
                        test_plan = json.load(f)

                    while retry_count <= max_retries:
                        try:
                            response = await client.post(
                                f"{PLAYWRIGHT_URL}/execute",
                                json=test_plan,
                                timeout=300.0  # Add timeout to avoid hanging
                            )
                            
                            # Log the response status
                            logger.debug(f"Received response with status code: {response.status_code}")
                            
                            if response.status_code == 422:
                                # Special handling for 422 errors - log the error details
                                error_details = response.json() if response.content else "No error details provided"
                                logger.error(f"Playwright API rejected the request with 422 Unprocessable Entity: {error_details}")
                                logger.error("This usually indicates invalid JSON structure or missing required fields.")
                                
                                # You could attempt to fix the request here if needed
                                if retry_count < max_retries:
                                    logger.info(f"Attempting to fix and retry request ({retry_count + 1}/{max_retries})")
                                    # For example, you could reformat the test_plan here
                                    # test_plan = {"test_plan": test_plan} # Example fix
                                    retry_count += 1
                                    continue
                                else:
                                    return {"error": f"Playwright API rejected the request: {error_details}"}
                            
                            # For other error codes, raise the exception to be caught below
                            response.raise_for_status()
                            
                            # Parse the results
                            results = response.json()
                            logger.info("Successfully executed test plan")
                            logger.debug(f"Raw results: {json.dumps(results, indent=2)}")
                            
                            # Have the LLM analyze the results
                            analysis = await llm.generate_str(
                                message=f"Create a markdown file in the output folder and Analyze these test results and provide a summary:\n{json.dumps(results, indent=2)}"
                            )
                            
                            logger.info(f"Test results analysis: {analysis}")
                            
                            return {
                                "test_plan": test_plan,
                                "results": results,
                                "analysis": analysis
                            }
                        
                        except httpx.TimeoutException:
                            logger.warning(f"Request timed out. Retry {retry_count + 1}/{max_retries}")
                            retry_count += 1
                            if retry_count > max_retries:
                                return {"error": "Request to Playwright API timed out after multiple attempts"}
                        
                        except httpx.HTTPStatusError as e:
                            # Handle other HTTP errors
                            logger.error(f"HTTP error: {e.response.status_code} - {e}")
                            
                            # Try to extract response content for better debugging
                            try:
                                error_content = e.response.json()
                                logger.error(f"Error response: {json.dumps(error_content, indent=2)}")
                            except Exception:
                                logger.error(f"Error response content: {e.response.text}")
                            
                            # Don't retry for client errors except specific cases
                            if 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                                return {"error": f"HTTP {e.response.status_code} error: {str(e)}"}
                            
                            retry_count += 1
                            if retry_count > max_retries:
                                return {"error": f"Failed after {max_retries} retries: {str(e)}"}
                            logger.info(f"Retrying request ({retry_count}/{max_retries})...")
                   
            except httpx.RequestError as e:
                logger.error(f"Request error: {e}")
                return {"error": f"Failed to execute test: {str(e)}"}
            except Exception as e:
                logger.error(f"Unexpected error during test execution: {e}", exc_info=True)
                return {"error": f"Unexpected error: {str(e)}"}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run website tests with Playwright")
    parser.add_argument("url", type=str, help="The URL to test")
    parser.add_argument("description", type=str, help="Description of what to test")
    args = parser.parse_args()

    result = asyncio.run(run_test_on_website(args.url, args.description))
