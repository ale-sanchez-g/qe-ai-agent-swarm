# Planner MCP Agent

## Overview

The Planner MCP Agent is a specialized component within the QE-AI-Agent-Swarm ecosystem designed to automate project management tasks by integrating with Jira and Confluence. This agent leverages the Model Context Protocol (MCP) to provide AI-powered project planning and issue tracking capabilities.

## Features

- Connects to Jira and Confluence via MCP protocol
- Retrieves and analyzes project issues and data
- Generates comprehensive project reports
- Supports multi-turn AI conversations for data analysis
- Saves report data to the filesystem for further processing

## Prerequisites

- Python 3.12 or higher
- Anthropic API key (for Claude LLM)
- Jira and Confluence access credentials
- Required Python packages (listed in `requirements.txt`)

## Installation

1. Ensure Python 3.12 is installed on your system
2. Set up a virtual environment:
```sh
python3 -m venv mcpagent
```

3. Activate the virtual environment:
   - On macOS/Linux:
```sh
source mcpagent/bin/activate
```
   - On Windows:
```sh
.\mcpagent\Scripts\activate
```

4. Install dependencies:
```sh
pip install -r requirements.txt
```

## Configuration

The planner agent uses two main configuration files:

1. `mcp_agent.config.yaml` - General configuration including:
   - MCP server settings
   - Execution engine configuration
   - Logger settings

2. `mcp_agent.secrets.yaml` - Contains sensitive credentials:
   - Anthropic API keys
   - Jira/Confluence access tokens
   - Server URLs

Make sure to create your own `mcp_agent.secrets.yaml` file based on the example file in the monolith folder:
```sh
cp ../monolith/mcp_agent.secrets-example.yaml mcp_agent.secrets.yaml
```
Then edit the file to add your actual credentials.

## Usage

To run the planner agent:

```sh
python main.py
```

The agent will:
1. Connect to your configured Jira instance
2. Retrieve relevant project issues
3. Generate reports in the `output` directory

## Output Files

The agent generates several output files:

- `output/project_issues/project_issues_report.md` - Detailed breakdown of project issues
- `output/jira_project_issues_report.md` - Comprehensive Jira project report
- `output/project_issues_summary.md` - Executive summary of project issues

## Architecture

The planner agent works as follows:
1. Initializes MCP client connections to both Atlassian services and LLM
2. Fetches raw project data from Jira
3. Processes this data through Claude LLM for analysis
4. Generates structured reports and insights
5. Saves reports to the local filesystem

## Extending the Agent

To extend the planner's functionality:
- Add new report types in the `main.py` file
- Create additional analysis workflows
- Configure more MCP integrations as needed

## Troubleshooting

Common issues and solutions:
- **Connection failures**: Check your credentials and network settings
- **Missing reports**: Ensure proper write permissions to the output directory
- **API rate limits**: Implement rate limiting in your requests

## License

This project is licensed under the terms included in the repository's LICENSE file.

