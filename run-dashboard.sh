#!/bin/bash
################################################################################
# FACELESS YOUTUBE - DASHBOARD STARTUP SCRIPT (Linux/macOS)
################################################################################
#
# Starts the React frontend dashboard
#
# Prerequisites:
#   - Node.js 18+
#   - npm installed
#   - Dependencies installed (npm install in dashboard/)
#
# Usage: bash run-dashboard.sh
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
echo "║           FACELESS YOUTUBE - DASHBOARD STARTUP                            ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if dashboard directory exists
if [ ! -d dashboard ]; then
    log_error "Dashboard directory not found at dashboard/"
    exit 1
fi

# Check if node_modules exists
if [ ! -d dashboard/node_modules ]; then
    log_warning "Dependencies not installed in dashboard/"
    echo ""
    log_info "Installing dependencies with npm install..."
    cd dashboard
    npm install
    if [ $? -ne 0 ]; then
        log_error "Failed to install dependencies"
        exit 1
    fi
    log_success "Dependencies installed"
    cd ..
else
    log_success "Dependencies found"
fi

log_success "Dashboard ready"
echo ""

# Navigate to dashboard
cd dashboard

# Start development server
log_info "Starting dashboard server on http://127.0.0.1:3000"
echo ""
log_info "Dashboard will open in your default browser automatically"
echo ""
log_warning "Press Ctrl+C to stop the server"
echo ""
echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo ""

npm start

exit 0
