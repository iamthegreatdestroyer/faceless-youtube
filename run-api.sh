#!/bin/bash
################################################################################
# FACELESS YOUTUBE - API STARTUP SCRIPT (Linux/macOS)
################################################################################
#
# Starts the FastAPI backend application
#
# Prerequisites:
#   - Python 3.11+
#   - Virtual environment created (venv/)
#   - Dependencies installed (pip install -r requirements.txt)
#
# Usage: bash run-api.sh
#
################################################################################

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

# Title
clear
echo ""
echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║             FACELESS YOUTUBE - API SERVER STARTUP                         ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if venv exists
if [ ! -d venv ]; then
    log_error "Virtual environment not found at venv/"
    echo ""
    log_info "Please run 'bash setup.sh' first"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate
if [ $? -ne 0 ]; then
    log_error "Failed to activate virtual environment"
    exit 1
fi

log_success "Virtual environment activated"

# Check if .env exists
if [ ! -f .env ]; then
    log_error "Configuration file not found (.env)"
    echo ""
    log_info "Please run 'bash setup.sh' first"
    exit 1
fi

log_success "Configuration loaded (.env)"
echo ""

# Start API
log_info "Starting API server on http://127.0.0.1:8000"
echo ""
echo "Documentation available at:"
echo "  - Swagger UI:  http://127.0.0.1:8000/docs"
echo "  - ReDoc:       http://127.0.0.1:8000/redoc"
echo ""
log_warning "Press Ctrl+C to stop the server"
echo ""
echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo ""

python -m uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000

exit 0
