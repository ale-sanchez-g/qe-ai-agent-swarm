#!/bin/bash
# Simple test script to verify Docker deployment readiness

echo "🧪 Testing Docker deployment readiness..."

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

TESTS_PASSED=0
TESTS_FAILED=0

test_pass() {
    echo -e "${GREEN}✅ PASS:${NC} $1"
    ((TESTS_PASSED++))
}

test_fail() {
    echo -e "${RED}❌ FAIL:${NC} $1"
    ((TESTS_FAILED++))
}

test_warn() {
    echo -e "${YELLOW}⚠️  WARN:${NC} $1"
}

# Test 1: Check if Dockerfile exists
if [ -f "Dockerfile" ]; then
    test_pass "Dockerfile exists"
else
    test_fail "Dockerfile not found"
fi

# Test 2: Check if docker-compose.yml exists
if [ -f "docker-compose.yml" ]; then
    test_pass "docker-compose.yml exists"
else
    test_fail "docker-compose.yml not found"
fi

# Test 3: Check if requirements.txt exists
if [ -f "requirements.txt" ]; then
    test_pass "requirements.txt exists"
else
    test_fail "requirements.txt not found"
fi

# Test 4: Check if main application file exists
if [ -f "plannerChat.py" ]; then
    test_pass "plannerChat.py exists"
else
    test_fail "plannerChat.py not found"
fi

# Test 5: Check if templates directory exists
if [ -d "templates" ]; then
    test_pass "templates directory exists"
    
    # Check for essential templates
    if [ -f "templates/chat.html" ]; then
        test_pass "chat.html template exists"
    else
        test_fail "chat.html template not found"
    fi
else
    test_fail "templates directory not found"
fi

# Test 6: Check if static directory exists
if [ -d "static" ]; then
    test_pass "static directory exists"
else
    test_warn "static directory not found (will be created during deployment)"
fi

# Test 7: Check configuration files
if [ -f "mcp_agent.config.yaml" ]; then
    test_pass "mcp_agent.config.yaml exists"
else
    test_fail "mcp_agent.config.yaml not found"
fi

if [ -f "mcp_agent.secrets-example.yaml" ]; then
    test_pass "mcp_agent.secrets-example.yaml exists"
else
    test_fail "mcp_agent.secrets-example.yaml not found"
fi

# Test 8: Check if .env.example exists
if [ -f ".env.example" ]; then
    test_pass ".env.example exists"
else
    test_fail ".env.example not found"
fi

# Test 9: Check deployment script
if [ -f "deploy.sh" ] && [ -x "deploy.sh" ]; then
    test_pass "deploy.sh exists and is executable"
else
    test_fail "deploy.sh not found or not executable"
fi

# Test 10: Check Docker prerequisites
if command -v docker &> /dev/null; then
    test_pass "Docker is installed"
    
    if docker info &> /dev/null; then
        test_pass "Docker is running"
    else
        test_fail "Docker is not running"
    fi
else
    test_fail "Docker is not installed"
fi

# Test 11: Check Docker Compose
if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
    test_pass "Docker Compose is available"
else
    test_fail "Docker Compose is not available"
fi

# Summary
echo
echo "📊 Test Summary:"
echo "  Passed: $TESTS_PASSED"
echo "  Failed: $TESTS_FAILED"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed! Ready for Docker deployment.${NC}"
    echo
    echo "Next steps:"
    echo "  1. cp .env.example .env"
    echo "  2. Edit .env with your API keys"
    echo "  3. ./deploy.sh deploy"
    exit 0
else
    echo -e "${RED}🚨 Some tests failed. Please fix the issues before deploying.${NC}"
    exit 1
fi
