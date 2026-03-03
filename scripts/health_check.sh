#!/bin/bash
# Stock Analyzer Health Check Script

PROJECT_ROOT="/Users/mkc/.openclaw/workspace/stock_analyzer"

echo "=== Stock Analyzer Health Check ==="
echo ""

# Check virtual environment
if [ -d "$PROJECT_ROOT/venv" ]; then
    echo "✓ Virtual environment exists"
else
    echo "✗ Virtual environment not found"
    exit 1
fi

# Check Python
source "$PROJECT_ROOT/venv/bin/activate"
PYTHON_VERSION=$(python3 --version)
echo "✓ $PYTHON_VERSION"

# Check dependencies
echo ""
echo "Dependencies:"
python3 -c "import requests; print('  ✓ requests')" 2>/dev/null || echo "  ✗ requests"
python3 -c "import pandas; print('  ✓ pandas')" 2>/dev/null || echo "  ✗ pandas"
python3 -c "import jinja2; print('  ✓ jinja2')" 2>/dev/null || echo "  ✗ jinja2"
python3 -c "import yaml; print('  ✓ yaml')" 2>/dev/null || echo "  ✗ yaml"
python3 -c "import loguru; print('  ✓ loguru')" 2>/dev/null || echo "  ✗ loguru"

# Check configuration
echo ""
echo "Configuration:"
if [ -f "$PROJECT_ROOT/config/settings.yaml" ]; then
    echo "  ✓ settings.yaml"
else
    echo "  ✗ settings.yaml not found"
fi

if [ -f "$PROJECT_ROOT/config/secrets.yaml" ]; then
    echo "  ✓ secrets.yaml"
else
    echo "  ⚠ secrets.yaml not found (create from example)"
fi

# Check main script
echo ""
echo "Application:"
if [ -f "$PROJECT_ROOT/src/main.py" ]; then
    echo "  ✓ main.py"
else
    echo "  ✗ main.py not found"
fi

echo ""
echo "=== Health Check Complete ==="
