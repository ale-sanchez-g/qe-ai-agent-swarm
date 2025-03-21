# MCP Agent Monolith

## Overview
The MCP Agent Monolith is an AI-powered test automation tool that uses Large Language Models (LLMs) to generate and execute automated tests on web applications. The system:

1. Takes a URL and test description as input
2. Analyzes the web page structure
3. Generates a comprehensive test plan with Playwright-compatible selectors
4. Executes the tests through a Playwright service
5. Provides test results and analysis

This tool bridges the gap between natural language test descriptions and executable test scripts, enabling QA teams to create automated tests without writing code.

## Prerequisites
- Python 3.12
- Required Python packages (can be installed via `pip`)
- Anthropic API Key
- Running Playwright service (on localhost:8000 by default)

## Installation
1. Create a virtual environment:
   ```sh
   python3 -m venv mcpagent
   ```
2. Activate the virtual environment:
   - On macOS/Linux:
     ```sh
     source mcpagent/bin/activate
     ```
   - On Windows:
     ```sh
     .\mcpagent\Scripts\activate
     ```
3. Install the required packages:
   ```sh
   pip install -r requirements.txt
   ```

## Running the MCP Puppet
1. Ensure you are in the `monolith` directory.
2. Run the puppet with a URL and natural language test description:

- HTML website with JavaScript
   ```sh
   python main.py https://devops1.com.au/ "As a user I want to navigate using the menu like click on services then on Anticipate, or Click on Engage, Hover on Accelerators and click on Cloud Acceleration"
   ```
   
- React Application

```sh
python main.py https://ale-sanchez-g.github.io/featureflags/ "User will test different mathematical calculations like 1+1=2 and 3-1=2 and check the result of each transaction then take a screenshot of each calculation. Test 5 different calculations, and 3 edge cases"
```
- Form

``` sh
python main.py https://templates.snapforms.com.au/form/2FnoQUKZdA/ "I want to be able to fill my Personal information form and submit"
```

- BDD

```sh
export test="
Feature: Classic calculator

Given I am a Classic users 
When I calculate 1+1 
Then I can confirm the calculation equates to 2 by validating the results section

NOTES: 
Ensure to test all calculations types, 
Run 5 different calculations
3 edge cases like division by 0, decimal points and large numbers
"

python main.py https://ale-sanchez-g.github.io/featureflags/ $test
```

## How It Works
1. The application connects to the specified website via a Playwright service
2. It captures the page structure and elements
3. Using Anthropic's LLM, it generates a JSON test plan with specific Playwright actions
4. The test plan is executed by the Playwright service
5. Results are captured and analyzed by the AI agent
6. Test artifacts are saved to the output folder

## Configuration
The agent loads its configuration from the `mcp_agent.config.yaml` file located in the same directory. Make sure to update the configuration file as needed.