#!/bin/bash
set -e

# Deployment script for MCP Planner Chat UI
# This script automates the Docker deployment process

echo "🚀 Starting MCP Planner Chat UI deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed and running
check_docker() {
    print_status "Checking Docker installation..."
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    if ! docker info &> /dev/null; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    
    print_success "Docker is installed and running"
}

# Check if Docker Compose is available
check_docker_compose() {
    print_status "Checking Docker Compose..."
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not available. Please install Docker Compose."
        exit 1
    fi
    print_success "Docker Compose is available"
}

# Check environment configuration
check_environment() {
    print_status "Checking environment configuration..."
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            print_warning ".env file not found. Copying from .env.example..."
            cp .env.example .env
            print_warning "Please edit .env file with your actual API keys before continuing."
            echo "Required variables:"
            echo "  - ANTHROPIC_API_KEY (required)"
            echo "  - LAUNCHDARKLY_SDK_KEY (optional)"
            echo "  - DYNATRACE_ENDPOINT (optional)"
            echo "  - DYNATRACE_API_TOKEN (optional)"
            read -p "Press Enter to continue after editing .env file..."
        else
            print_error ".env file not found and no .env.example available."
            exit 1
        fi
    fi
    
    # Check if required secrets file exists
    if [ ! -f "mcp_agent.secrets.yaml" ]; then
        if [ -f "mcp_agent.secrets-example.yaml" ]; then
            print_warning "mcp_agent.secrets.yaml not found. Copying from example..."
            cp mcp_agent.secrets-example.yaml mcp_agent.secrets.yaml
            print_warning "Please edit mcp_agent.secrets.yaml with your actual credentials."
            read -p "Press Enter to continue after editing secrets file..."
        else
            print_warning "mcp_agent.secrets.yaml not found. The application may not work correctly without proper credentials."
        fi
    fi
    
    print_success "Environment configuration checked"
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    directories=("output" "logs" "memory" "memory_index" "static/css" "static/js" "static/images" "templates")
    
    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            print_status "Created directory: $dir"
        fi
    done
    
    print_success "Directories created"
}

# Build Docker image
build_image() {
    print_status "Building Docker image..."
    
    if docker build -t planner-chat-ui:latest .; then
        print_success "Docker image built successfully"
    else
        print_error "Failed to build Docker image"
        exit 1
    fi
}

# Deploy with Docker Compose
deploy_compose() {
    print_status "Deploying with Docker Compose..."
    
    # Stop existing containers
    docker-compose down --remove-orphans 2>/dev/null || docker compose down --remove-orphans 2>/dev/null || true
    
    # Start new containers
    if docker-compose up -d 2>/dev/null || docker compose up -d 2>/dev/null; then
        print_success "Application deployed successfully"
    else
        print_error "Failed to deploy with Docker Compose"
        exit 1
    fi
}

# Check deployment health
check_health() {
    print_status "Checking deployment health..."
    
    max_attempts=30
    attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:8000/health &>/dev/null; then
            print_success "Application is healthy and responding"
            return 0
        fi
        
        echo -n "."
        sleep 2
        ((attempt++))
    done
    
    print_error "Health check failed after $max_attempts attempts"
    print_status "Checking container logs..."
    docker-compose logs planner-chat 2>/dev/null || docker compose logs planner-chat 2>/dev/null
    exit 1
}

# Show deployment information
show_info() {
    print_success "🎉 Deployment completed successfully!"
    echo
    echo "Access your application at:"
    echo "  Main Chat Interface: http://localhost:8000"
    echo "  Reports Interface:   http://localhost:8000/reports"
    echo "  API Documentation:   http://localhost:8000/docs"
    echo "  Health Check:        http://localhost:8000/health"
    echo
    echo "Management commands:"
    echo "  View logs:           docker-compose logs -f planner-chat"
    echo "  Stop application:    docker-compose down"
    echo "  Restart application: docker-compose restart"
    echo "  Update application:  ./deploy.sh"
    echo
}

# Parse command line arguments
ACTION=${1:-deploy}

case $ACTION in
    "deploy")
        check_docker
        check_docker_compose
        check_environment
        create_directories
        build_image
        deploy_compose
        check_health
        show_info
        ;;
    "build")
        check_docker
        build_image
        print_success "Build completed"
        ;;
    "start")
        check_docker
        check_docker_compose
        deploy_compose
        check_health
        show_info
        ;;
    "stop")
        print_status "Stopping application..."
        docker-compose down 2>/dev/null || docker compose down 2>/dev/null
        print_success "Application stopped"
        ;;
    "restart")
        print_status "Restarting application..."
        docker-compose restart 2>/dev/null || docker compose restart 2>/dev/null
        check_health
        print_success "Application restarted"
        ;;
    "logs")
        docker-compose logs -f planner-chat 2>/dev/null || docker compose logs -f planner-chat 2>/dev/null
        ;;
    "status")
        print_status "Checking application status..."
        docker-compose ps 2>/dev/null || docker compose ps 2>/dev/null
        if curl -f http://localhost:8000/health &>/dev/null; then
            print_success "Application is healthy"
        else
            print_warning "Application may not be healthy"
        fi
        ;;
    "clean")
        print_status "Cleaning up Docker resources..."
        docker-compose down --volumes --remove-orphans 2>/dev/null || docker compose down --volumes --remove-orphans 2>/dev/null
        docker image rm planner-chat-ui:latest 2>/dev/null || true
        print_success "Cleanup completed"
        ;;
    *)
        echo "Usage: $0 {deploy|build|start|stop|restart|logs|status|clean}"
        echo
        echo "Commands:"
        echo "  deploy   - Full deployment (build, start, health check)"
        echo "  build    - Build Docker image only"
        echo "  start    - Start application with Docker Compose"
        echo "  stop     - Stop application"
        echo "  restart  - Restart application"
        echo "  logs     - Show application logs"
        echo "  status   - Check application status"
        echo "  clean    - Clean up Docker resources"
        exit 1
        ;;
esac
