# QE-AI-Agent-Swarm Project Makefile
# Provides convenient targets for project maintenance and operations

.PHONY: help index components deploy test clean validate

# Default target
help:
	@echo "QE-AI-Agent-Swarm Project Commands"
	@echo "=================================="
	@echo ""
	@echo "📊 Project Maintenance:"
	@echo "  index       - Generate/update PROJECT_INDEX.md"
	@echo "  components  - List all project components"
	@echo "  stats       - Show project statistics"
	@echo "  validate    - Validate project structure"
	@echo ""
	@echo "🚀 Deployment Commands:"
	@echo "  deploy-planner    - Deploy the planner component"
	@echo "  deploy-monolith   - Run the monolith component"
	@echo "  deploy-research   - Deploy the research component"
	@echo ""
	@echo "🧪 Testing Commands:"
	@echo "  test-all     - Run all component tests"
	@echo "  test-planner - Test the planner component"
	@echo ""
	@echo "🧹 Cleanup Commands:"
	@echo "  clean        - Clean temporary files and caches"
	@echo "  clean-docker - Clean Docker containers and images"

# Generate project index
index:
	@echo "🔄 Generating project index..."
	@python3 scripts/generate_project_index.py
	@echo "✅ Project index updated in PROJECT_INDEX.md"

# List project components
components:
	@echo "📁 Project Components:"
	@echo "====================="
	@for dir in */; do \
		if [ -f "$$dir/README.md" ]; then \
			echo "✅ $$dir - Component with documentation"; \
		elif [ -f "$$dir/main.py" ] || [ -f "$$dir/plannerChat.py" ]; then \
			echo "🔧 $$dir - Component (missing README)"; \
		else \
			echo "📂 $$dir - Directory"; \
		fi; \
	done

# Show project statistics
stats:
	@echo "📊 Project Statistics:"
	@echo "====================="
	@echo "Python files: $$(find . -name '*.py' -not -path './*/mcpagent/*' -not -path './*/__pycache__/*' | wc -l | xargs)"
	@echo "Documentation files: $$(find . -name '*.md' | wc -l | xargs)"
	@echo "Configuration files: $$(find . -name '*.yaml' -o -name '*.yml' | wc -l | xargs)"
	@echo "Docker files: $$(find . -name 'Dockerfile*' -o -name 'docker-compose*' | wc -l | xargs)"
	@echo "Total directories: $$(find . -type d -not -path './*/mcpagent*' -not -path './*/__pycache__*' | wc -l | xargs)"

# Deploy planner component
deploy-planner:
	@echo "🚀 Deploying planner component..."
	@cd planner && ./deploy.sh deploy

# Run monolith component
deploy-monolith:
	@echo "🚀 Starting monolith component..."
	@echo "Usage: cd monolith && python main.py <URL> <test_description>"
	@echo "Example: cd monolith && python main.py https://example.com 'Test the homepage'"

# Deploy research component
deploy-research:
	@echo "🚀 Deploying research component..."
	@cd research && docker build -t qe-research-agent .
	@echo "✅ Research agent container built. Run: docker run -it qe-research-agent"

# Test all components
test-all: test-planner
	@echo "🧪 Running all tests..."

# Test planner component
test-planner:
	@echo "🧪 Testing planner component..."
	@cd planner && python -m pytest test_*.py -v || echo "⚠️  Tests not found or failed"

# Clean temporary files
clean:
	@echo "🧹 Cleaning temporary files..."
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -delete 2>/dev/null || true
	@find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleanup complete"

# Clean Docker containers and images
clean-docker:
	@echo "🧹 Cleaning Docker resources..."
	@docker system prune -f
	@echo "✅ Docker cleanup complete"

# Development setup for new contributors
setup:
	@echo "🔧 Setting up development environment..."
	@echo "1. Ensure Python 3.12+ is installed"
	@echo "2. Run component-specific setup:"
	@echo "   - Planner: cd planner && make setup"
	@echo "   - Monolith: cd monolith && pip install -r requirements.txt"
	@echo "   - Research: cd research && pip install -r requirements.txt"
	@echo "3. Update project index: make index"

# Quick status check
status:
	@echo "📋 Project Status:"
	@echo "=================="
	@echo "Git branch: $$(git branch --show-current 2>/dev/null || echo 'unknown')"
	@echo "Git status: $$(git status --porcelain | wc -l | xargs) changed files"
	@echo "Components with README:"
	@for dir in */; do \
		if [ -f "$$dir/README.md" ]; then \
			echo "  ✅ $$dir"; \
		fi; \
	done

# Validate project structure
validate:
	@echo "🔍 Validating project structure..."
	@python3 scripts/validate_structure.py