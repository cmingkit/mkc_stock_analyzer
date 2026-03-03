#!/bin/bash
# Stock Analyzer - Installation Script
# Version: 1.0
# Last Updated: 2026-03-01

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_ROOT/venv"
PYTHON_MIN_VERSION="3.9.0"

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

check_python_version() {
    log_info "Checking Python version..."
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 not found. Please install Python 3.9 or higher."
        exit 1
    fi
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    log_success "Python version: $PYTHON_VERSION"
}

create_venv() {
    if [ -d "$VENV_DIR" ]; then
        log_warning "Virtual environment already exists"
        return 0
    fi
    log_info "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    log_success "Virtual environment created"
}

activate_venv() {
    log_info "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
    log_success "Virtual environment activated"
}

install_dependencies() {
    log_info "Upgrading pip..."
    pip install --upgrade pip setuptools wheel
    
    log_info "Installing dependencies..."
    pip install -r "$PROJECT_ROOT/requirements.txt"
    log_success "Dependencies installed"
}

create_directories() {
    log_info "Creating project directories..."
    mkdir -p "$PROJECT_ROOT"/{src/{collectors,analyzers,reporters,utils},templates,static/{css,js,images}}
    mkdir -p "$PROJECT_ROOT"/{reports/{html,pdf,json},logs/archive,config,tests,scripts}
    
    # Create __init__.py files
    touch "$PROJECT_ROOT"/src/__init__.py
    touch "$PROJECT_ROOT"/src/collectors/__init__.py
    touch "$PROJECT_ROOT"/src/analyzers/__init__.py
    touch "$PROJECT_ROOT"/src/reporters/__init__.py
    touch "$PROJECT_ROOT"/src/utils/__init__.py
    touch "$PROJECT_ROOT"/tests/__init__.py
    
    # Create .gitkeep files for empty directories
    touch "$PROJECT_ROOT"/reports/html/.gitkeep
    touch "$PROJECT_ROOT"/reports/pdf/.gitkeep
    touch "$PROJECT_ROOT"/reports/json/.gitkeep
    
    log_success "Project directories created"
}

setup_config() {
    log_info "Setting up configuration files..."
    if [ -f "$PROJECT_ROOT/config/secrets.yaml.example" ] && \
       [ ! -f "$PROJECT_ROOT/config/secrets.yaml" ]; then
        cp "$PROJECT_ROOT/config/secrets.yaml.example" "$PROJECT_ROOT/config/secrets.yaml"
        log_success "Created config/secrets.yaml from template"
    fi
}

verify_environment() {
    log_info "Verifying installation..."
    python3 -c "import requests; print(f'  ✓ requests {requests.__version__}')" 2>/dev/null || true
    python3 -c "import pandas; print(f'  ✓ pandas {pandas.__version__}')" 2>/dev/null || true
    python3 -c "import jinja2; print(f'  ✓ Jinja2 {jinja2.__version__}')" 2>/dev/null || true
    log_success "Environment verification complete"
}

show_next_steps() {
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}   Installation Complete!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "Next Steps:"
    echo "  1. Configure API keys: vim $PROJECT_ROOT/config/secrets.yaml"
    echo "  2. Activate venv: source $VENV_DIR/bin/activate"
    echo "  3. Run: python src/main.py --help"
    echo ""
}

main() {
    echo -e "${GREEN}=== Stock Analyzer Setup ===${NC}"
    check_python_version
    create_venv
    activate_venv
    install_dependencies
    create_directories
    setup_config
    verify_environment
    show_next_steps
}

main "$@"
