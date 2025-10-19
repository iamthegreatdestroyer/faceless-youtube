#!/usr/bin/env bash
set -e

echo "🚀 Faceless YouTube Setup Wizard"
echo "================================"

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8 or higher."
    exit 1
fi

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

echo "📥 Installing setup wizard dependencies..."
pip install -r requirements-dev.txt

python3 scripts/setup_wizard.py
