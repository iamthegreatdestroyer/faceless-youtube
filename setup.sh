#!/bin/bash
################################################################################
# FACELESS YOUTUBE - ONE-CLICK INSTALLER (LINUX/MacOS)
################################################################################
#
# This script provides the complete setup experience for the
# Faceless YouTube Automation Platform on Linux and macOS systems.
#
# Features:
#   - Environment detection and validation
#   - Python and Node.js dependency checks
#   - Virtual environment setup
#   - Interactive configuration wizard
#   - Database initialization
#   - One-click startup options
#
# Date: October 25, 2025
################################################################################

set -e

# Color codes
GREEN='\033[92m'
YELLOW='\033[93m'
RED='\033[91m'
RESET='\033[0m'
BOLD='\033[1m'

# Project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Helper functions
log_info() {
    echo -e "${BOLD}[INFO]${RESET} $*"
}

log_success() {
    echo -e "${BOLD}${GREEN}[✓]${RESET} $*"
}

log_warning() {
    echo -e "${BOLD}${YELLOW}[⚠]${RESET} $*"
}

log_error() {
    echo -e "${BOLD}${RED}[✗]${RESET} $*"
}

separator() {
    echo ""
    echo "════════════════════════════════════════════════════════════════════════════"
    echo ""
}

# ============================================================================
# MAIN SETUP
# ============================================================================

clear
separator
echo -e "${BOLD}${GREEN}🚀  FACELESS YOUTUBE - ONE-CLICK INSTALLATION WIZARD  🚀${RESET}"
echo -e "${BOLD}Automating Security & Content Creation${RESET}"
separator

# ============================================================================
# STEP 1: CHECK SYSTEM REQUIREMENTS
# ============================================================================

log_info "Checking system requirements..."
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    log_error "Python 3 not found. Please install Python 3.11 or higher:"
    echo "  macOS: brew install python@3.11"
    echo "  Ubuntu/Debian: sudo apt-get install python3.11"
    echo "  CentOS/RHEL: sudo yum install python3.11"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
log_success "Python $PYTHON_VERSION found"

# Check Node.js
if ! command -v node &> /dev/null; then
    log_error "Node.js not found. Please install Node.js 18 or higher:"
    echo "  macOS: brew install node"
    echo "  Ubuntu/Debian: sudo apt-get install nodejs npm"
    echo "  CentOS/RHEL: sudo yum install nodejs npm"
    exit 1
fi

NODE_VERSION=$(node --version)
log_success "Node.js $NODE_VERSION found"

# Check npm
if ! command -v npm &> /dev/null; then
    log_error "npm not found"
    exit 1
fi

NPM_VERSION=$(npm --version)
log_success "npm $NPM_VERSION found"

# Check optional Docker
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | awk '{print $3}' | tr -d ',')
    log_success "Docker $DOCKER_VERSION available"
else
    log_warning "Docker not found (optional, some features will be unavailable)"
fi

echo ""

# ============================================================================
# STEP 2: CREATE VIRTUAL ENVIRONMENT
# ============================================================================

log_info "Setting up Python environment..."
echo ""

if [ ! -d "venv" ]; then
    log_info "Creating virtual environment..."
    python3 -m venv venv
    log_success "Virtual environment created"
else
    log_success "Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate
log_success "Virtual environment activated"
echo ""

# ============================================================================
# STEP 3: INSTALL DEPENDENCIES
# ============================================================================

log_info "Installing dependencies..."
echo ""

log_info "Installing Python dependencies..."
pip install -r requirements-dev.txt > /dev/null 2>&1 || {
    log_error "Failed to install Python dependencies"
    echo "Run: pip install -r requirements-dev.txt"
    exit 1
}
log_success "Python dependencies installed"

log_info "Installing Node.js dependencies..."
if [ -f "dashboard/package.json" ]; then
    cd dashboard
    npm install > /dev/null 2>&1 || {
        log_error "Failed to install Node.js dependencies"
        cd ..
        exit 1
    }
    log_success "Node.js dependencies installed"
    cd ..
else
    log_warning "dashboard/package.json not found, skipping npm install"
fi

echo ""

# ============================================================================
# STEP 4: CONFIGURATION WIZARD
# ============================================================================

log_info "Running configuration wizard..."
echo ""

python3 scripts/setup_wizard.py
if [ $? -ne 0 ]; then
    log_error "Setup wizard failed"
    exit 1
fi

echo ""

# ============================================================================
# STEP 5: COMPLETION
# ============================================================================

separator
echo -e "${BOLD}${GREEN}✓ SETUP COMPLETED SUCCESSFULLY${RESET}"
separator

echo ""
echo -e "${BOLD}NEXT STEPS:${RESET}"
echo ""
echo "1. Start the API server:"
echo "   python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --reload"
echo ""
echo "2. In another terminal, start the Dashboard:"
echo "   cd dashboard"
echo "   npm run dev"
echo ""
echo "3. Open your browser:"
echo "   http://127.0.0.1:3000"
echo ""
echo "Documentation: Check README.md for detailed setup instructions"
echo ""
separator

exit 0
