#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}✓${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

# Phase 1: Pre-deployment validation
echo "===== PHASE 1: PRE-DEPLOYMENT VALIDATION ====="

if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed"
    exit 1
fi
log_info "Docker installed"

if ! command -v docker-compose &> /dev/null; then
    log_error "docker-compose is not installed"
    exit 1
fi
log_info "docker-compose installed"

# Phase 2: Start services
echo ""
echo "===== PHASE 2: START TEST ENVIRONMENT ====="

cd "$PROJECT_ROOT"

log_info "Starting test services..."
docker-compose -f docker-compose.test.yml up -d

# Phase 3: Run tests
# The test-runner container's entrypoint handles waiting for services
echo ""
echo "===== PHASE 3: RUN TESTS ====="

log_info "Running tests with coverage..."
docker-compose -f docker-compose.test.yml run test-runner pytest tests/ \
    --cov=src \
    --cov-report=html \
    --cov-report=term \
    --tb=short \
    -v

TEST_RESULT=$?

# Phase 4: Generate coverage report
echo ""
echo "===== PHASE 4: COVERAGE REPORT ====="

if [ $TEST_RESULT -eq 0 ]; then
    log_info "Tests passed!"
    log_info "Coverage report generated in htmlcov/index.html"
else
    log_error "Tests failed"
fi

# Phase 5: Cleanup
echo ""
echo "===== PHASE 5: CLEANUP ====="

log_info "Bringing down test environment..."
docker-compose -f docker-compose.test.yml down

exit $TEST_RESULT