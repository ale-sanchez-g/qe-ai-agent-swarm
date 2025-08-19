# Research Agent

The Research Agent is part of the QE-AI-Agent-Swarm project, designed to conduct intelligent research and generate comprehensive reports on any topic using AI capabilities powered by the Model Context Protocol (MCP).

## Overview

This research module provides an AI-powered agent that can perform comprehensive research on any topic, gather information from multiple sources, analyze data, and generate detailed markdown reports. It's built on top of the MCP Agent framework and leverages Anthropic's Claude models for natural language understanding and generation.

## Features

- **Topic-Based Research**: Research any topic by providing it as a command line argument
- **Comprehensive Reports**: Generates detailed markdown reports with structured analysis
- **Multi-Source Research**: Gathers information from web sources using the fetch MCP server
- **AI-Powered Analysis**: Uses Claude models for intelligent analysis and synthesis
- **MCP Integration**: Leverages Model Context Protocol for enhanced capabilities
- **Automatic File Management**: Saves reports with timestamps in organized output directory
- **Configurable Logging**: Flexible logging system with console and file outputs
- **Containerized Deployment**: Ready-to-run Docker container
- **Async Architecture**: Built with asyncio for high-performance operations

## Quick Start

### Command Line Usage

```bash
# Basic usage - research a topic
python main.py "artificial intelligence"

# Specify output directory
python main.py "machine learning" --output /path/to/reports

# Research with shortened flag
python main.py "quantum computing" -o ./reports
```

### Example Output

When you run the research agent, it will:
1. Gather information from multiple web sources
2. Analyze and synthesize the findings
3. Generate a comprehensive markdown report
4. Save both a detailed report and a summary file

Example files generated:
- `research_report_artificial_intelligence_20241201_143022.md` - Full detailed report
- `research_summary_artificial_intelligence_20241201_143022.md` - Quick summary

## Prerequisites

### Local Development
- Python 3.11 or higher
- pip (Python package installer)

### Docker Deployment
- Docker Engine
- Docker Compose (optional)

## Project Structure

```
research/
├── main.py                    # Main application entry point
├── requirements.txt           # Python dependencies
├── dockerfile                 # Optimized Docker container configuration
├── .dockerignore             # Docker build context exclusions
├── mcp_agent.config.yaml     # Agent configuration
├── mcp_agent.secrets.yaml    # Secret configuration (not in repo)
├── schema/                    # Configuration schemas
│   └── mcp-agent.config.schema.json
└── mcpagent/                 # Virtual environment (local development)
```

## Configuration

### 1. Agent Configuration

The agent behavior is configured through `mcp_agent.config.yaml`:

```yaml
execution_engine: asyncio
logger:
  transports: [console]
  level: debug
  path: "logs/mcp-agent.jsonl"

mcp:
  servers:
    fetch:
      command: "uvx"
      args: ["mcp-server-fetch"]
    filesystem:
      command: "npx"
      args: ["-y", "@modelcontextprotocol/server-filesystem", "./output/"]

anthropic:
  default_model: "claude-3-5-haiku-20241022"
```

### 2. Secrets Configuration

Create `mcp_agent.secrets.yaml` with your API credentials:

```yaml
anthropic:
  api_key: "your-anthropic-api-key-here"
```

**⚠️ Important**: Never commit the secrets file to version control. Use `mcp_agent.secrets-example.yaml` as a template.

## Installation & Setup

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

### Local Development

1. **Clone and navigate to the research directory:**
   ```bash
   cd research
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv mcpagent
   source mcpagent/bin/activate  # On macOS/Linux
   ```

3. **Install dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Configure secrets:**
   ```bash
   cp mcp_agent.secrets-example.yaml mcp_agent.secrets.yaml
   # Edit mcp_agent.secrets.yaml with your API keys
   ```

5. **Run the application:**
   ```bash
   python main.py
   ```

### Docker Deployment

1. **Build the optimized Docker image:**
   ```bash
   docker build -t qe-research-agent .
   ```

2. **Create a secrets file:**
   ```bash
   cp mcp_agent.secrets-example.yaml mcp_agent.secrets.yaml
   # Edit with your API keys
   ```

3. **Run the container:**
   ```bash
   docker run -v $(pwd)/mcp_agent.secrets.yaml:/app/mcp_agent.secrets.yaml qe-research-agent
   ```

#### Docker Image Optimizations

The Dockerfile includes several optimizations for production use:

- **🔄 Multi-stage build**: Separates build dependencies from runtime
- **🏔️ Alpine Linux base**: Minimal footprint with security updates
- **👤 Non-root execution**: Enhanced security with dedicated user
- **🧹 Build context optimization**: `.dockerignore` excludes unnecessary files
- **📦 Layer caching**: Optimized for Docker layer reuse

**Image Size Comparison:**
- Traditional build: ~200-300MB
- Optimized build: ~50-100MB (up to 70% reduction)

#### Option 2: Using Docker Compose

Create a `docker-compose.yml` file:

```yaml
version: '3.8'
services:
  research-agent:
    build: .
    volumes:
      - ./mcp_agent.secrets.yaml:/app/mcp_agent.secrets.yaml
      - ./output:/app/output
    environment:
      - PYTHONUNBUFFERED=1
```

Run with:
```bash
docker-compose up --build
```

#### Option 3: Production Deployment

For production environments with enhanced security:

```bash
# Using environment variables for secrets
docker run \
  -e ANTHROPIC_API_KEY="your-key-here" \
  --read-only \
  --tmpfs /tmp \
  --user 1001:1001 \
  qe-research-agent

# Using the security-focused image
docker run \
  -e ANTHROPIC_API_KEY="your-key-here" \
  --security-opt no-new-privileges:true \
  --cap-drop ALL \
  qe-research-agent:secure
```

## Docker Best Practices

The containerized setup follows security and efficiency best practices:

### Build Optimization
- **Multi-stage builds** minimize final image size
- **Layer caching** reduces rebuild times
- **Alpine Linux** provides security with minimal footprint

### Security Features
- **Non-root user execution** (UID/GID 1001)
- **Minimal base image** reduces attack surface
- **Build context exclusions** via `.dockerignore`
- **Security-focused alternative** with additional hardening

### Performance
- **Optimized layer ordering** for cache efficiency
- **Minimal runtime dependencies** for faster starts
- **Async architecture** for concurrent operations

## Usage

### Basic Operation

The research agent initializes with the MCP framework and provides access to various AI capabilities:

```python
# The agent automatically loads configuration and connects to MCP servers
async with app.run() as agent_app:
    logger = agent_app.logger
    context = agent_app.context
    
    # Your research logic here
    logger.info("Research agent is running...")
```

### Extending Functionality

To add custom research capabilities:

1. **Create custom agents** by extending the base Agent class
2. **Add new MCP servers** in the configuration for additional tools
3. **Implement specific research workflows** in the main application loop

## Configuration Options

### Logging Configuration

- **Transports**: `[console, file]` - Choose output destinations
- **Level**: `debug`, `info`, `warning`, `error` - Set logging verbosity
- **Path**: Custom log file location and naming patterns

### MCP Servers

The agent can connect to various MCP servers for enhanced capabilities:

- **Fetch Server**: Web scraping and content retrieval
- **Filesystem Server**: File system operations
- **Custom Servers**: Add your own MCP-compatible tools

### Model Configuration

- **Provider**: Currently supports Anthropic (Claude models)
- **Model Selection**: Configure which specific model to use
- **Model Parameters**: Temperature, max tokens, etc. (extend configuration as needed)

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
   ```bash
   pip install -r requirements.txt
   ```

2. **API Key Issues**: Verify your Anthropic API key is correctly set
   ```bash
   # Check if secrets file exists and has correct format
   cat mcp_agent.secrets.yaml
   ```

3. **Docker Build Failures**: Ensure Docker has sufficient resources
   ```bash
   docker system prune  # Clean up Docker resources
   docker builder prune # Clean build cache if needed
   ```

4. **Large Image Sizes**: Use the optimized Dockerfile
   ```bash
   # Check image size
   docker images qe-research-agent
   
   # Use multi-stage build for optimization
   docker build -t qe-research-agent .
   ```

5. **Security Warnings**: Use the security-focused configuration
   ```bash
   # Build with security enhancements
   docker build -f dockerfile.secure -t qe-research-agent:secure .
   ```

4. **Permission Issues**: Make sure the output directory is writable
   ```bash
   chmod 755 output/
   ```

### Logs and Debugging

- Check application logs in `logs/mcp-agent.jsonl`
- Enable debug logging in configuration for detailed output
- Use `docker logs <container-id>` for containerized debugging

## Development

### Adding New Features

1. Extend the main application in `main.py`
2. Add new dependencies to `requirements.txt`
3. Update configuration schema if needed
4. Update Docker configurations if new system dependencies are required
5. Update this README with new features

### Docker Development

1. **Local development with hot reload:**
   ```bash
   docker run -v $(pwd):/app -it qe-research-agent /bin/sh
   ```

2. **Testing image optimizations:**
   ```bash
   # Compare image sizes
   docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
   ```

3. **Security scanning:**
   ```bash
   # Scan for vulnerabilities (if tools available)
   docker scout quickview qe-research-agent
   ```

### Testing

Run tests using:
```bash
python -m pytest  # If tests are added
```

## Contributing

1. Follow the existing code style and patterns
2. Update documentation for any new features
3. Ensure Docker builds successfully
4. Test both local and containerized deployments

## License

This project is part of the QE-AI-Agent-Swarm framework. See the main project LICENSE file for details.

## Support

For issues and questions:
- Check the main project documentation
- Review the configuration schema in `schema/`
- Examine logs for detailed error information
- Ensure all prerequisites are met

---

*This research agent is designed to be part of a larger AI agent swarm for quality engineering. See the main project README for the complete system architecture and roadmap.*
