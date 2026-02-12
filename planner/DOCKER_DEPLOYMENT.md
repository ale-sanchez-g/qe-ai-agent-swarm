# MCP Planner Chat UI - Docker Deployment Guide

This document provides comprehensive instructions for deploying the MCP Planner Chat UI using Docker.

## Quick Start

1. **Copy environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Edit environment variables:**
   ```bash
   nano .env  # or your preferred editor
   ```
   Add your API keys:
   - `ANTHROPIC_API_KEY` (required)
   - `LAUNCHDARKLY_SDK_KEY` (optional)

3. **Deploy:**
   ```bash
   ./deploy.sh
   ```

4. **Access the application:**
   - Main Interface: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Prerequisites

- Docker (20.10+)
- Docker Compose (v2.0+)
- curl (for health checks)

## Configuration

### Environment Variables

Create a `.env` file from the template:

```bash
cp .env.example .env
```

Required variables:
- `ANTHROPIC_API_KEY`: Your Anthropic API key for Claude LLM

Optional variables:
- `LAUNCHDARKLY_SDK_KEY`: For AI configuration management
- `DYNATRACE_ENDPOINT`: For observability
- `DYNATRACE_API_TOKEN`: For observability

### Secrets Configuration

The application uses `mcp_agent.secrets.yaml` for sensitive configuration. Copy the example:

```bash
cp mcp_agent.secrets-example.yaml mcp_agent.secrets.yaml
```

Edit the file with your actual credentials.

## Deployment Options

### Option 1: Using the Deployment Script (Recommended)

The deployment script automates the entire process:

```bash
# Full deployment
./deploy.sh deploy

# Available commands
./deploy.sh build      # Build image only
./deploy.sh start      # Start containers
./deploy.sh stop       # Stop containers
./deploy.sh restart    # Restart containers
./deploy.sh logs       # View logs
./deploy.sh status     # Check status
./deploy.sh clean      # Clean up resources
```

### Option 2: Manual Docker Compose

```bash
# Build and start
docker-compose up -d --build

# Stop
docker-compose down

# View logs
docker-compose logs -f planner-chat

# Check status
docker-compose ps
```

### Option 3: Docker Run (Basic)

```bash
# Build image
docker build -t planner-chat-ui .

# Run container
docker run -d \
  --name planner-chat \
  -p 8000:8000 \
  -e ANTHROPIC_API_KEY=your_key_here \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/memory:/app/memory \
  planner-chat-ui
```

## File Structure

The Docker deployment creates and manages these directories:

```
planner/
├── Dockerfile              # Container definition
├── docker-compose.yml      # Multi-container setup
├── .dockerignore           # Files to exclude from build
├── deploy.sh               # Automated deployment script
├── .env.example            # Environment template
├── .env                    # Your environment variables (create this)
├── output/                 # Generated conversation files
├── logs/                   # Application logs
├── memory/                 # Session memory databases
├── memory_index/           # Long-term memory index
├── static/                 # Web assets
└── templates/              # HTML templates
```

## Container Architecture

### Main Container: `planner-chat`
- **Base Image**: python:3.12-slim-bookworm
- **Port**: 8000
- **Volumes**: Persistent storage for data, logs, and configuration
- **Health Check**: Automated health monitoring
- **Resources**: 2GB memory limit, 1 CPU limit

### Optional: Redis Container
Uncomment the Redis service in `docker-compose.yml` for enhanced session management:

```yaml
redis:
  image: redis:7-alpine
  ports:
    - "6379:6379"
  volumes:
    - redis_data:/data
```

## Persistent Data

The following directories are mounted as volumes to persist data:

- `./output` → `/app/output` - Conversation files and reports
- `./logs` → `/app/logs` - Application logs
- `./memory` → `/app/memory` - Session memory databases
- `./memory_index` → `/app/memory_index` - Vector database for RAG
- `./rag` → `/app/rag` - Knowledge base files

## Monitoring and Health Checks

### Built-in Health Check
The container includes an automated health check:
```bash
curl -f http://localhost:8000/health
```

### Manual Health Check
```bash
# Check container status
docker-compose ps

# Check application health
curl http://localhost:8000/health

# View recent logs
docker-compose logs --tail=50 planner-chat
```

### Access Points
- **Main Chat**: http://localhost:8000
- **Reports**: http://localhost:8000/reports  
- **API Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health

## Troubleshooting

### Common Issues

1. **Container won't start**
   ```bash
   # Check logs
   docker-compose logs planner-chat
   
   # Check environment
   cat .env
   ```

2. **Application not responding**
   ```bash
   # Check health
   curl http://localhost:8000/health
   
   # Restart container
   docker-compose restart planner-chat
   ```

3. **Permission issues**
   ```bash
   # Fix directory permissions
   sudo chown -R $USER:$USER output logs memory memory_index
   ```

4. **Port already in use**
   ```bash
   # Check what's using port 8000
   lsof -i :8000
   
   # Change port in docker-compose.yml
   ports:
     - "8001:8000"  # Use different host port
   ```

### Log Analysis

```bash
# View all logs
docker-compose logs planner-chat

# Follow logs in real-time
docker-compose logs -f planner-chat

# View specific log file
docker-compose exec planner-chat cat logs/mcp-agent-*.jsonl
```

### Container Debugging

```bash
# Enter container shell
docker-compose exec planner-chat bash

# Check container resources
docker stats planner-chat

# Inspect container configuration
docker inspect planner-chat
```

## Production Deployment

### Security Considerations

1. **Environment Variables**: Use Docker secrets or external secret management
2. **Reverse Proxy**: Place behind nginx or traefik
3. **SSL/TLS**: Enable HTTPS termination
4. **Network**: Use custom Docker networks
5. **Updates**: Implement blue-green deployment

### Reverse Proxy Example (nginx)

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Resource Scaling

Adjust resources in `docker-compose.yml`:

```yaml
deploy:
  resources:
    limits:
      memory: 4G      # Increase for large conversations
      cpus: '2.0'     # Increase for better performance
    reservations:
      memory: 1G
      cpus: '1.0'
```

## Backup and Recovery

### Backup Script

```bash
#!/bin/bash
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup persistent data
cp -r output "$BACKUP_DIR/"
cp -r logs "$BACKUP_DIR/"
cp -r memory "$BACKUP_DIR/"
cp -r memory_index "$BACKUP_DIR/"
cp .env "$BACKUP_DIR/"
cp mcp_agent.secrets.yaml "$BACKUP_DIR/"

echo "Backup created in $BACKUP_DIR"
```

### Recovery

```bash
# Stop application
./deploy.sh stop

# Restore data
cp -r backups/20240815_120000/* ./

# Restart application
./deploy.sh start
```

## Updates and Maintenance

### Update Application

```bash
# Pull latest code
git pull

# Rebuild and deploy
./deploy.sh deploy
```

### Clean Up

```bash
# Remove old containers and images
./deploy.sh clean

# Clean Docker system
docker system prune -f
```

## Support

For issues and questions:
1. Check the logs: `./deploy.sh logs`
2. Verify health: `./deploy.sh status`
3. Review configuration files
4. Check Docker and system resources

## License

This deployment configuration is part of the QE AI Agent Swarm project and follows the same license terms.
