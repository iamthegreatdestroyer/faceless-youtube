#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
STAGING_DIR="/opt/faceless-youtube-staging"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}✓${NC} $1"; }
log_warn() { echo -e "${YELLOW}⚠${NC} $1"; }
log_error() { echo -e "${RED}✗${NC} $1"; }

echo "===== PHASE 1: PRE-DEPLOYMENT VALIDATION ====="

if [ ! -f "$PROJECT_ROOT/.env.staging" ]; then
    log_error ".env.staging file not found"
    exit 1
fi
log_info ".env.staging file found"

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

echo "\n===== PHASE 2: PREPARE STAGING ENVIRONMENT ====="

mkdir -p "$STAGING_DIR"
log_info "Staging directory prepared: $STAGING_DIR"

cp -r "$PROJECT_ROOT"/* "$STAGING_DIR/" || {
    log_error "Failed to copy project files"
    exit 1
}
log_info "Project files copied to staging directory"

echo "\n===== PHASE 3: BUILD DOCKER IMAGES ====="
cd "$STAGING_DIR"

log_info "Building backend image..."
docker build -f Dockerfile.prod -t faceless-youtube-api:staging .

log_info "Building frontend image..."
docker build -f dashboard/Dockerfile.prod -t faceless-youtube-dashboard:staging ./dashboard

echo "\n===== PHASE 4: DEPLOY TO STAGING ====="
log_info "Starting staging environment..."
docker-compose -f docker-compose.staging.yml up -d

echo "\n===== PHASE 5: HEALTH CHECKS ====="
log_info "Waiting for services to become healthy..."

# Check API
for i in {1..30}; do
    if curl -f http://localhost:8000/health &> /dev/null; then
        log_info "API health check passed"
        break
    fi
    sleep 2
    if [ $i -eq 30 ]; then
        log_error "API failed health check"
        exit 1
    fi
done

# Check Dashboard
for i in {1..30}; do
    if curl -f http://localhost:3000 &> /dev/null; then
        log_info "Dashboard health check passed"
        break
    fi
    sleep 2
    if [ $i -eq 30 ]; then
        log_error "Dashboard failed health check"
        exit 1
    fi
done

echo "\n===== PHASE 6: RUN SMOKE TESTS ====="

docker-compose -f docker-compose.staging.yml run --rm api \
    pytest tests/smoke/ -v --tb=short || {
    log_error "Smoke tests failed"
    exit 1
}

echo "\n===== PHASE 7: PERFORMANCE BASELINE ====="
log_info "Running performance tests..."
docker-compose -f docker-compose.staging.yml run --rm api \
    pytest tests/performance/ -v --tb=short || true

echo "\n===== PHASE 8: DEPLOYMENT COMPLETE ====="
log_info "Staging deployment successful!"

echo "Access points:"
echo "  API: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo "  Dashboard: http://localhost:3000"

echo "Useful commands:"
echo "  View logs: docker-compose -f docker-compose.staging.yml logs -f"
echo "  Run tests: docker-compose -f docker-compose.staging.yml run api pytest tests/"
echo "  Stop: docker-compose -f docker-compose.staging.yml down"
