# MCP Planner Chat UI

This application provides a web-based chat interface for interacting with your LLM (Large Language Model) and MCP (Model Context Protocol) agents.

## Features

- Real-time chat interface with the LLM
- WebSocket-based communication for instant responses
- Markdown rendering for formatted LLM responses
- System status updates and notifications
- Ability to run analysis tasks through the UI
- Download and manage generated reports

## Setup Instructions

1. Install the required dependencies:

```bash
cd planner
pip install -r requirements.txt
```

2. Ensure your MCP agent configuration is properly set up in `mcp_agent.config.yaml` and `mcp_agent.secrets.yaml`.

3. Run the application:

```bash
python plannerChat.py
```

4. Open your browser and navigate to:

```
http://localhost:8000
```

## Using the Chat Interface

1. The interface will automatically connect to the WebSocket server.
2. Type your message in the input box at the bottom of the screen.
3. Press Enter or click the Send button to send your message.
4. The LLM will process your request and respond in the chat window.

## Running Analysis Tasks

You can trigger predefined analysis tasks by sending specific commands:

- To run the Confluence analysis: Type "/run_analysis" in the chat

## Viewing Reports

Generated reports are saved in the `output` directory. You can view a list of available reports by visiting:

```
http://localhost:8000/list_reports
```

And download a specific report using:

```
http://localhost:8000/download/{filename}
```

## Architecture

The application consists of:

- A FastAPI web server for handling HTTP requests
- WebSocket endpoints for real-time communication
- Integration with the MCP Agent for accessing tools and services
- Connection to LLM services (Anthropic Claude) for generating responses

## Customization

You can customize the behavior by:

1. Modifying the agent instructions in the `process_message` function
2. Changing the available MCP servers in the agent initialization
3. Updating the UI templates in the `templates` directory
4. Customizing the CSS styles in the `static/css` directory

## Troubleshooting

- If you encounter connection issues, ensure your API keys are correctly set in `mcp_agent.secrets.yaml`
- Check the console logs for detailed error messages
- Verify that the required servers are running and accessible
