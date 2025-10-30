#!/bin/bash
# Faceless YouTube - Desktop Application Builder (Linux/macOS)
# ============================================================
# 
# This script builds the PyQt6 desktop application into a standalone executable
# using PyInstaller. Works on Windows (via Git Bash), Linux, and macOS.
#
# Usage:
#   ./build_desktop_app.sh          # Build with default settings
#   ./build_desktop_app.sh --clean  # Clean build artifacts first
#   ./build_desktop_app.sh --help   # Show help
#
# Requirements:
#   - Python 3.13+
#   - venv activated with all dependencies installed
#   - PyInstaller installed (pip install pyinstaller)
#
# Output:
#   dist/faceless-youtube (executable or .app bundle)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "\n${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}  $1"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check for help flag
if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    echo "Faceless YouTube Desktop App Builder"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --clean     Remove build artifacts before building"
    echo "  --onefile   Build as single executable (slower, but portable)"
    echo "  --help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                 # Build with default settings"
    echo "  $0 --clean         # Clean build"
    echo "  $0 --onefile       # Build as single file"
    exit 0
fi

# Parse arguments
CLEAN_BUILD=false
ONEFILE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --clean)
            CLEAN_BUILD=true
            shift
            ;;
        --onefile)
            ONEFILE=true
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Get project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

print_header "FACELESS YOUTUBE - DESKTOP APP BUILDER"

# Check if Python is available
print_info "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 not found. Please install Python 3.13+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
print_success "Python $PYTHON_VERSION found"

# Check if venv is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    print_warning "Virtual environment not activated"
    print_info "Attempting to activate venv..."
    
    if [[ -f "venv/bin/activate" ]]; then
        source venv/bin/activate
        print_success "Virtual environment activated"
    elif [[ -f ".venv/bin/activate" ]]; then
        source .venv/bin/activate
        print_success "Virtual environment activated"
    else
        print_error "Could not find virtual environment"
        print_info "Please create one: python3 -m venv venv"
        exit 1
    fi
fi

# Check PyInstaller
print_info "Checking PyInstaller installation..."
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    print_warning "PyInstaller not found. Installing..."
    pip install PyInstaller
    print_success "PyInstaller installed"
else
    print_success "PyInstaller is installed"
fi

# Clean if requested
if [[ "$CLEAN_BUILD" == true ]]; then
    print_info "Cleaning build artifacts..."
    rm -rf build/ dist/ *.egg-info __pycache__ *.pyc
    print_success "Cleaned"
fi

# Prepare spec file path
SPEC_FILE="$PROJECT_ROOT/build_desktop_app.spec"

if [[ ! -f "$SPEC_FILE" ]]; then
    print_error "Spec file not found: $SPEC_FILE"
    exit 1
fi

print_info "Using spec file: $SPEC_FILE"

# Build command
print_header "BUILDING EXECUTABLE"

BUILD_ARGS="--noconfirm --clean"

if [[ "$ONEFILE" == true ]]; then
    print_info "Building as single file (this may take longer)..."
    BUILD_ARGS="$BUILD_ARGS --onefile"
else
    print_info "Building with directory structure (faster)..."
fi

# Show build info
echo "Build command:"
echo "  pyinstaller $BUILD_ARGS $SPEC_FILE"
echo ""

# Run PyInstaller
if pyinstaller $BUILD_ARGS "$SPEC_FILE"; then
    print_success "Build completed successfully!"
    
    # Show output information
    echo ""
    echo "Output location:"
    
    if [[ "$ONEFILE" == true ]]; then
        echo "  dist/faceless-youtube (executable)"
        OUTPUT_FILE="$PROJECT_ROOT/dist/faceless-youtube"
    else
        echo "  dist/faceless-youtube/ (application directory)"
        OUTPUT_FILE="$PROJECT_ROOT/dist/faceless-youtube/"
    fi
    
    if [[ -f "$OUTPUT_FILE" ]] || [[ -d "$OUTPUT_FILE" ]]; then
        print_success "Executable ready at: $OUTPUT_FILE"
        
        # Show file size
        if [[ -f "$OUTPUT_FILE" ]]; then
            SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)
            print_info "Executable size: $SIZE"
        fi
    fi
    
    echo ""
    echo "Next steps:"
    echo "  1. Test the application: $OUTPUT_FILE"
    echo "  2. If you want to package it as an installer, run:"
    echo "     ./create_installer.sh (Windows)"
    echo "     Or use NSIS/Inno Setup to create installer"
    
else
    print_error "Build failed. Check output above for details."
    exit 1
fi

echo ""
print_header "BUILD COMPLETE"
