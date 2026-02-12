# Makefile for MCP Planner Chat UI Docker deployment
.PHONY: help build deploy start stop restart logs status clean dev prod rebuild force-build

# Default target
help:
	@echo "MCP Planner Chat UI - Docker Deployment"
	@echo "======================================"
	@echo ""
	@echo "Available targets:"
	@echo "  make deploy       - Full deployment (build + start + health check)"
	@echo "  make build        - Build Docker image"
	@echo "  make rebuild      - Force rebuild without cache"
	@echo "  make force-build  - Force rebuild with unique tag"
	@echo "  make start        - Start application"
	@echo "  make stop         - Stop application"
	@echo "  make restart      - Restart application"
	@echo "  make logs         - Show application logs"
	@echo "  make status       - Check application status"
	@echo "  make clean        - Clean up Docker resources"
	@echo "  make dev          - Development deployment"
	@echo "  make prod         - Production deployment"
	@echo "  make setup        - Initial setup (copy config files)"
	@echo ""

# Setup configuration files
setup:
	@echo "Setting up configuration files..."
	@if [ ! -f .env ]; then \
		cp .env.example .env && \
		echo "Created .env file from template. Please edit with your API keys."; \
	fi
	@if [ ! -f mcp_agent.secrets.yaml ]; then \
		cp mcp_agent.secrets-example.yaml mcp_agent.secrets.yaml && \
		echo "Created secrets file from template. Please edit with your credentials."; \
	fi
	@echo "Setup complete!"

# Development deployment
dev: setup
	@echo "Starting development deployment..."
	./deploy.sh deploy

# Production deployment
prod: setup
	@echo "Starting production deployment..."
	docker-compose -f docker-compose.prod.yml up -d --build
	@echo "Production deployment complete!"
	@echo "Access your application at: http://localhost"

# Build Docker image
build:
	@echo "Building Docker image..."
	./deploy.sh build

# Force rebuild without cache
rebuild:
	@echo "Force rebuilding Docker image without cache..."
	docker-compose build --no-cache --pull
	@echo "Rebuild complete!"

# Force rebuild with unique tag
force-build:
	@echo "Force building with unique tag..."
	@BUILD_TAG=$$(date +%Y%m%d-%H%M%S)-$$(git rev-parse --short HEAD 2>/dev/null || echo "local") && \
	docker build --no-cache --pull -t planner-chat-ui:$$BUILD_TAG -t planner-chat-ui:latest . && \
	echo "Built image with tag: planner-chat-ui:$$BUILD_TAG"

# Deploy application
deploy: setup
	@echo "Deploying application..."
	./deploy.sh deploy

# Start application
start:
	@echo "Starting application..."
	./deploy.sh start

# Stop application
stop:
	@echo "Stopping application..."
	./deploy.sh stop

# Restart application
restart:
	@echo "Restarting application..."
	./deploy.sh restart

# Show logs
logs:
	@echo "Showing application logs..."
	./deploy.sh logs

# Check status
status:
	@echo "Checking application status..."
	./deploy.sh status

# Clean up
clean:
	@echo "Cleaning up Docker resources..."
	./deploy.sh clean

# Backup data
backup:
	@echo "Creating backup..."
	@mkdir -p backups
	@BACKUP_DIR="backups/$$(date +%Y%m%d_%H%M%S)" && \
	mkdir -p "$$BACKUP_DIR" && \
	cp -r output "$$BACKUP_DIR/" 2>/dev/null || true && \
	cp -r logs "$$BACKUP_DIR/" 2>/dev/null || true && \
	cp -r memory "$$BACKUP_DIR/" 2>/dev/null || true && \
	cp -r memory_index "$$BACKUP_DIR/" 2>/dev/null || true && \
	cp .env "$$BACKUP_DIR/" 2>/dev/null || true && \
	cp mcp_agent.secrets.yaml "$$BACKUP_DIR/" 2>/dev/null || true && \
	echo "Backup created in $$BACKUP_DIR"

# Check prerequisites
check:
	@echo "Checking prerequisites..."
	@command -v docker >/dev/null 2>&1 || { echo "Docker is not installed"; exit 1; }
	@docker info >/dev/null 2>&1 || { echo "Docker is not running"; exit 1; }
	@command -v docker-compose >/dev/null 2>&1 || docker compose version >/dev/null 2>&1 || { echo "Docker Compose is not available"; exit 1; }
	@echo "All prerequisites are met!"

# Development helpers
shell:
	@echo "Opening shell in container..."
	docker-compose exec planner-chat bash

tail:
	@echo "Following logs..."
	docker-compose logs -f planner-chat

ps:
	@echo "Showing container status..."
	docker-compose ps

# Health check
health:
	@echo "Checking application health..."
	@curl -f http://localhost:8000/health >/dev/null 2>&1 && \
		echo "✅ Application is healthy" || \
		echo "❌ Application is not responding"

# Update application
update:
	@echo "Updating application..."
	git pull
	make deploy

# Show application URLs
urls:
	@echo "Application URLs:"
	@echo "  Main Interface: http://localhost:8000"
	@echo "  Reports:        http://localhost:8000/reports"
	@echo "  API Docs:       http://localhost:8000/docs"
	@echo "  Health Check:   http://localhost:8000/health"
