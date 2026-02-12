# 🚀 MCP Planner Chat UI - Docker Deployment Summary

## Overview
This document provides a quick reference for deploying your MCP Planner Chat UI using Docker. The deployment has been fully automated and tested.

## 📁 Files Created

### Core Docker Files
- `Dockerfile` - Container definition with Python 3.12, Node.js, and all dependencies
- `docker-compose.yml` - Development deployment configuration
- `docker-compose.prod.yml` - Production deployment with nginx and Redis
- `.dockerignore` - Optimized build context exclusions

### Deployment Tools
- `deploy.sh` - Automated deployment script with health checks
- `Makefile` - Convenient make targets for common operations
- `test-docker-readiness.sh` - Pre-deployment validation script

### Configuration
- `.env.example` - Environment variables template
- `nginx.conf` - Production nginx configuration
- `docker-compose.monitoring.yml` - Optional monitoring stack

### Documentation
- `DOCKER_DEPLOYMENT.md` - Comprehensive deployment guide

## 🎯 Quick Start

```bash
# 1. Setup configuration
cp .env.example .env
# Edit .env with your ANTHROPIC_API_KEY

# 2. Deploy
./deploy.sh deploy

# 3. Access
open http://localhost:8000
```

## 🛠️ Available Commands

### Using the deployment script:
```bash
./deploy.sh deploy    # Full deployment
./deploy.sh build     # Build image only
./deploy.sh start     # Start containers
./deploy.sh stop      # Stop containers
./deploy.sh restart   # Restart containers
./deploy.sh logs      # View logs
./deploy.sh status    # Check status
./deploy.sh clean     # Clean up resources
```

### Using make:
```bash
make deploy           # Full deployment
make dev             # Development setup
make prod            # Production deployment
make setup           # Copy config files
make backup          # Backup data
make health          # Health check
make urls            # Show access URLs
```

### Using Docker Compose directly:
```bash
docker-compose up -d --build    # Start
docker-compose down             # Stop
docker-compose logs -f          # Follow logs
```

## 🌐 Access Points

After deployment, your application will be available at:

- **Main Chat Interface**: http://localhost:8000
- **Reports Interface**: http://localhost:8000/reports
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 🔧 Configuration

### Required Environment Variables
- `ANTHROPIC_API_KEY` - Your Anthropic API key (required)

### Optional Environment Variables
- `LAUNCHDARKLY_SDK_KEY` - For AI configuration management
- `DYNATRACE_ENDPOINT` - For observability
- `DYNATRACE_API_TOKEN` - For observability

### Secrets File
Edit `mcp_agent.secrets.yaml` with your actual credentials:
```bash
cp mcp_agent.secrets-example.yaml mcp_agent.secrets.yaml
# Edit the file with your API keys
```

## 📊 Monitoring

### Health Checks
```bash
curl http://localhost:8000/health
./deploy.sh status
make health
```

### Logs
```bash
./deploy.sh logs
docker-compose logs -f planner-chat
```

### Metrics (Optional)
Deploy monitoring stack:
```bash
docker-compose -f docker-compose.monitoring.yml up -d
```
Access Grafana at http://localhost:3000 (admin/admin123)

## 🏗️ Architecture

### Development Stack
- **Application**: FastAPI + WebSocket chat interface
- **Persistence**: Local volumes for data, logs, memory
- **Ports**: 8000 (HTTP)

### Production Stack
- **Load Balancer**: Nginx reverse proxy with SSL termination
- **Application**: FastAPI application container
- **Cache**: Redis for session management
- **Persistence**: Named Docker volumes
- **Monitoring**: Optional Prometheus + Grafana stack

## 🔒 Security

### Development
- Local file mounts for easy development
- Basic health checks
- Resource limits

### Production
- Read-only configuration mounts
- Nginx rate limiting and security headers
- SSL/TLS termination ready
- Resource constraints
- Named volumes for data persistence

## 🚀 Production Deployment

For production, use the dedicated configuration:

```bash
# Setup production environment
cp .env.example .env.prod
# Edit .env.prod with production values

# Deploy production stack
docker-compose -f docker-compose.prod.yml up -d --build

# Access via nginx
curl http://localhost/health
```

## 🐛 Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Check what's using port 8000
   lsof -i :8000
   # Or change port in docker-compose.yml
   ```

2. **Permission issues**
   ```bash
   sudo chown -R $USER:$USER output logs memory
   ```

3. **Container won't start**
   ```bash
   ./deploy.sh logs
   docker-compose ps
   ```

4. **Health check fails**
   ```bash
   curl -v http://localhost:8000/health
   ./deploy.sh status
   ```

### Debug Commands
```bash
# Enter container shell
docker-compose exec planner-chat bash

# Check container resources
docker stats planner-chat

# Rebuild and restart
./deploy.sh clean && ./deploy.sh deploy
```

## 📦 Data Persistence

The following directories are persisted:
- `./output` - Generated conversation files and reports
- `./logs` - Application logs
- `./memory` - Session memory databases  
- `./memory_index` - Vector database for RAG

## 🔄 Updates

To update the application:
```bash
# Pull latest code
git pull

# Redeploy
./deploy.sh deploy

# Or using make
make update
```

## 🆘 Support

For issues:
1. Check logs: `./deploy.sh logs`
2. Verify health: `./deploy.sh status`  
3. Run readiness test: `./test-docker-readiness.sh`
4. Review configuration files
5. Check Docker and system resources

## ✅ Validation

Before deployment, run the readiness test:
```bash
./test-docker-readiness.sh
```

This validates all required files and dependencies are in place.

---

**🎉 Your MCP Planner Chat UI is now ready for Docker deployment!**

For detailed information, see [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md).
