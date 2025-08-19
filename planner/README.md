# Planner MCP Agent - Interactive Chat UI

## Overview

The Planner MCP Agent is an advanced interactive chat interface built with FastAPI that provides AI-powered research and analysis capabilities. This component within the QE-AI-Agent-Swarm ecosystem leverages the Model Context Protocol (MCP) to enable real-time conversations with AI agents that have access to various tools and services.

## Features

- **Interactive Web Chat Interface**: Real-time chat UI with WebSocket communication
- **Conversation Memory Management**: Persistent conversation history with SQLite backend using LangChain
- **Multi-MCP Server Integration**: Connects to multiple MCP servers (Atlassian, filesystem, fetch)
- **LaunchDarkly AI Integration**: Dynamic AI configuration and feature flags with usage tracking
- **Session Management**: Multiple concurrent user sessions with unique conversation contexts
- **File Management**: Download and view generated reports through web interface
- **Real-time Status Updates**: Live processing indicators and system messages
- **Memory Operations**: Clear sessions, view history, and manage conversation data
- **OpenTelemetry Integration**: Comprehensive logging and observability with Dynatrace

## Prerequisites

- Python 3.12 or higher
- Anthropic API key (for Claude LLM)
- LaunchDarkly SDK key (optional, for AI configuration management)
- Access to MCP servers (Atlassian, filesystem, etc.)
- Required Python packages (listed in `requirements.txt`)

## Tech Stack

- **Backend**: FastAPI with WebSocket support
- **Frontend**: HTML/CSS/JavaScript with real-time chat interface
- **Memory**: LangChain with SQLite for conversation persistence
- **AI Integration**: Anthropic Claude models via MCP Agent framework
- **Feature Management**: LaunchDarkly for dynamic AI configuration
- **Observability**: OpenTelemetry with Dynatrace integration

## Installation

### Option 1: Docker Deployment (Recommended)

The easiest way to deploy the planner chat UI is using Docker:

```sh
# Quick start
cp .env.example .env  # Edit with your API keys
./deploy.sh deploy    # Automated deployment

# Or using make
make deploy
```

**Required Environment Variables:**
- `ANTHROPIC_API_KEY`: Your Anthropic API key (required)
- `LAUNCHDARKLY_SDK_KEY`: LaunchDarkly SDK key (optional)

**Access Points:**
- Main Chat Interface: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Reports Interface: http://localhost:8000/reports

For detailed Docker deployment instructions, see [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md).

### Option 2: Local Development Setup

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

The planner agent uses several configuration files:

### 1. Core Configuration (`mcp_agent.config.yaml`)
- **Execution Engine**: AsyncIO-based execution
- **MCP Server Settings**: Configuration for fetch and filesystem servers
- **OpenTelemetry**: Dynatrace integration for observability
- **Logger Settings**: Multi-transport logging (console, file, HTTP)
- **Anthropic Settings**: Default model configuration

### 2. Secrets Configuration (`mcp_agent.secrets.yaml`)
Create this file based on the example:
```sh
cp mcp_agent.secrets-example.yaml mcp_agent.secrets.yaml
```

Contains sensitive credentials:
- Anthropic API keys
- LaunchDarkly SDK keys
- MCP server credentials (Atlassian tokens if using Atlassian integration)

### 3. Environment Variables
Create a `.env` file for additional configuration:
```env
LAUNCHDARKLY_SDK_KEY=your_launchdarkly_key
ANTHROPIC_API_KEY=your_anthropic_key
```

## Usage

### Starting the Chat Interface

Run the interactive chat server:

```sh
python plannerChat.py
```

The application provides:
- **Main Chat Interface**: http://localhost:8000
- **Health Check**: http://localhost:8000/health  
- **Reports Interface**: http://localhost:8000/reports
- **WebSocket Endpoint**: ws://localhost:8000/ws

### Using the Chat Interface

1. **Start Conversations**: Open the web interface and begin chatting
2. **Real-time Responses**: AI processes requests with live status updates
3. **Session Management**: Each browser session maintains conversation context
4. **File Downloads**: Access generated reports through the reports interface

### Available Endpoints

- `GET /` - Main chat interface
- `GET /health` - Health check endpoint
- `GET /reports` - Reports viewing interface
- `GET /download/{filename}` - Download specific files
- `GET /list_reports` - List all available reports
- `GET /memory/sessions` - List active sessions
- `DELETE /memory/session/{session_id}` - Clear session memory
- `GET /memory/session/{session_id}/history` - View session history

## Output Files

The chat interface generates several types of output:

### Conversation Files
- `output/{session_id}_{uuid}.md` - Individual conversation responses
- Each file contains the user query and AI response for that interaction

### Memory Database
- `memory/{session_id}.db` - SQLite databases storing conversation history
- Persistent across sessions for conversation continuity

### Logs
- `logs/mcp-agent-{timestamp}.jsonl` - Structured application logs
- OpenTelemetry traces sent to configured Dynatrace endpoint

## Architecture

The planner agent architecture includes:

### Core Components
1. **FastAPI Application**: Web server with WebSocket support
2. **Connection Manager**: Handles multiple concurrent WebSocket connections
3. **Session Manager**: Manages conversation memory and persistence
4. **MCP Agent Integration**: Connects to various MCP servers for tool access
5. **LLM Integration**: Anthropic Claude models via MCP Agent framework

### Data Flow
1. **User Interface**: Web-based chat interface sends messages via WebSocket
2. **Session Management**: Each connection gets unique session ID and memory context
3. **Message Processing**: User messages processed through AI with conversation history
4. **Tool Access**: Agent can access MCP servers (filesystem, fetch, Atlassian)
5. **Response Generation**: AI responses streamed back via WebSocket
6. **Persistence**: Conversations saved to SQLite and output files generated

### Memory Management
- **LangChain Integration**: ConversationSummaryBufferMemory for efficient context management
- **Token Limit Management**: Automatically summarizes old conversations to stay within limits
- **Session Cleanup**: Background thread removes expired sessions after 24 hours
- **Persistent Storage**: SQLite databases maintain conversation history across restarts

## Extending the Agent

To extend the planner's functionality:

### Adding New MCP Servers
1. Update `mcp_agent.config.yaml` to include new server configurations
2. Add server names to the agent initialization in `plannerChat.py`
3. Update secrets file if authentication is required

### Custom Chat Features
1. **New Endpoints**: Add FastAPI routes for additional functionality
2. **WebSocket Commands**: Extend the WebSocket message handling for new actions
3. **Memory Enhancements**: Modify `memory_manager.py` for custom memory behaviors
4. **UI Extensions**: Update HTML templates and static files for new interface features

### LaunchDarkly Integration
1. **Feature Flags**: Add new flags for experimental features
2. **AI Configuration**: Modify AI prompts and models through LaunchDarkly
3. **A/B Testing**: Implement testing for different AI behaviors

### Observability Extensions
1. **Custom Metrics**: Add OpenTelemetry metrics for specific features
2. **Trace Enhancement**: Include additional trace data for debugging
3. **Dashboard Creation**: Build Dynatrace dashboards for monitoring

## Troubleshooting

### Common Issues and Solutions

#### Connection Issues
- **WebSocket Failures**: Check browser console for connection errors
- **MCP Server Timeouts**: Verify MCP server configurations and network connectivity
- **LaunchDarkly Initialization**: Check SDK key and network access

#### Memory and Performance
- **High Memory Usage**: Session cleanup runs every hour, consider adjusting cleanup interval
- **Slow Responses**: Check OpenTelemetry traces in Dynatrace for bottlenecks
- **Database Locks**: Ensure SQLite files in `memory/` directory have proper permissions

#### Configuration Problems
- **Missing Environment Variables**: Verify `.env` file contains required keys
- **Invalid YAML**: Validate configuration files with YAML linters
- **API Key Issues**: Check Anthropic API key validity and rate limits

#### Debugging Steps
1. **Check Logs**: Review `logs/mcp-agent-{timestamp}.jsonl` for detailed error information
2. **Health Endpoint**: Use `/health` endpoint to verify service status
3. **Browser Developer Tools**: Check WebSocket connection and console errors
4. **OpenTelemetry Traces**: Use Dynatrace to analyze request flows and performance

## Development

### Project Structure
```
planner/
├── plannerChat.py              # Main FastAPI application
├── memory_manager.py           # Conversation memory management
├── mcp_agent.config.yaml       # Core configuration
├── mcp_agent.secrets.yaml      # Sensitive credentials
├── requirements.txt            # Python dependencies
├── templates/                  # Jinja2 HTML templates
│   ├── chat.html              # Main chat interface
│   └── reports.html           # Reports viewing page
├── static/                     # Static web assets
│   ├── css/                   # Stylesheets
│   └── js/                    # JavaScript files
├── memory/                     # SQLite conversation databases
├── output/                     # Generated conversation files
└── logs/                      # Application logs
```

### Key Dependencies
- **mcp-agent**: Core MCP framework
- **fastapi**: Web framework with WebSocket support
- **langchain**: Conversation memory management
- **langchain-anthropic**: Anthropic AI integration
- **launchdarkly-server-sdk**: Feature flag management
- **uvicorn**: ASGI server for FastAPI

### Running in Development
1. Install dependencies: `pip install -r requirements.txt`
2. Set up configuration files (see Configuration section)
3. Run with auto-reload: `uvicorn plannerChat:app --reload --host 0.0.0.0 --port 8000`

## License

This project is licensed under the terms included in the repository's LICENSE file.

