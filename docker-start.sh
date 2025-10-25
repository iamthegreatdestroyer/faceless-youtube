#!/bin/bash
################################################################################
# FACELESS YOUTUBE - ONE-CLICK DOCKER DEPLOYMENT
################################################################################
#
# Starts the entire Faceless YouTube platform using Docker Compose
#
# Features:
#   - One-command startup
#   - All services pre-configured
#   - Health checks for all services
#   - Automatic port mapping
#   - Volume management
#
# Usage: ./docker-start.sh
#
################################################################################

set -e

# Colors
GREEN='\033[92m'
YELLOW='\033[93m'
RED='\033[91m'
RESET='\033[0m'
BOLD='\033[1m'

# Helper functions
log_info() {
    echo -e "${BOLD}[INFO]${RESET} $*"
}

log_success() {
    echo -e "${BOLD}${GREEN}[✓]${RESET} $*"
}

log_error() {
    echo -e "${BOLD}${RED}[✗]${RESET} $*"
}

# Check Docker
log_info "Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    log_error "Docker not found. Please install Docker Desktop"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    log_error "Docker Compose not found. Please install Docker Desktop"
    exit 1
fi

log_success "Docker found: $(docker --version)"
log_success "Docker Compose found: $(docker-compose --version)"

# Check .env file
if [ ! -f ".env" ]; then
    log_error ".env file not found"
    log_info "Please run setup.sh or setup.bat first"
    exit 1
fi

log_success ".env configuration loaded"

# Start services
echo ""
log_info "Starting Faceless YouTube services..."
echo ""

docker-compose up -d

# Wait for services to be ready
log_info "Waiting for services to be healthy..."
sleep 5

# Check service health
log_info "Checking service status..."

# Check API
if docker-compose ps api 2>/dev/null | grep -q "Up"; then
    log_success "API server is running on http://127.0.0.1:8000"
else
    log_error "API server failed to start"
fi

# Check Dashboard
if docker-compose ps dashboard 2>/dev/null | grep -q "Up"; then
    log_success "Dashboard is running on http://127.0.0.1:3000"
else
    log_error "Dashboard failed to start"
fi

# Check Database
if docker-compose ps postgres 2>/dev/null | grep -q "Up"; then
    log_success "PostgreSQL is running on localhost:5432"
else
    log_error "PostgreSQL failed to start"
fi

# Check Redis
if docker-compose ps redis 2>/dev/null | grep -q "Up"; then
    log_success "Redis is running on localhost:6379"
else
    log_error "Redis failed to start"
fi

echo ""
log_success "All services started successfully!"
echo ""

echo "Access the application at:"
echo "  Dashboard: http://127.0.0.1:3000"
echo "  API Docs:  http://127.0.0.1:8000/docs"
echo ""
echo "Useful commands:"
echo "  View logs:      docker-compose logs -f"
echo "  Stop services:  docker-compose down"
echo "  View status:    docker-compose ps"
echo ""

exit 0
