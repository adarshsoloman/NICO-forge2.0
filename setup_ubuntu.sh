#!/bin/bash
#
# Rewat-Forge Ubuntu Setup Script
# ================================
# Automated setup for Ubuntu/Debian systems
#
# Usage: bash setup_ubuntu.sh
#

set -e  # Exit on error

echo "========================================================================"
echo "Rewat-Forge Ubuntu Setup"
echo "========================================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python 3.8+ is installed
echo "1. Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 is not installed${NC}"
    echo "Please install Python 3.8 or higher:"
    echo "  sudo apt update"
    echo "  sudo apt install python3 python3-pip python3-venv"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo -e "${RED}✗ Python $PYTHON_VERSION is installed, but Python 3.8+ is required${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python $PYTHON_VERSION detected${NC}"
echo ""

# Check if pip is installed
echo "2. Checking pip..."
if ! command -v pip3 &> /dev/null; then
    echo -e "${YELLOW}⚠ pip3 not found, installing...${NC}"
    sudo apt update
    sudo apt install -y python3-pip
fi
echo -e "${GREEN}✓ pip is available${NC}"
echo ""

# Create virtual environment
echo "3. Creating virtual environment..."
if [ -d ".venv" ]; then
    echo -e "${YELLOW}⚠ Virtual environment already exists${NC}"
    read -p "Do you want to recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf .venv
        python3 -m venv .venv
        echo -e "${GREEN}✓ Virtual environment recreated${NC}"
    else
        echo "Keeping existing virtual environment"
    fi
else
    python3 -m venv .venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi
echo ""

# Activate virtual environment
echo "4. Activating virtual environment..."
source .venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo ""

# Upgrade pip
echo "5. Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
echo -e "${GREEN}✓ pip upgraded${NC}"
echo ""

# Install dependencies
echo "6. Installing dependencies..."
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}✗ requirements.txt not found${NC}"
    exit 1
fi

pip install -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Verify installation
echo "7. Verifying installation..."
echo ""

# Check PyMuPDF
if python3 -c "import fitz" 2>/dev/null; then
    echo -e "${GREEN}  ✓ PyMuPDF (fitz)${NC}"
else
    echo -e "${RED}  ✗ PyMuPDF (fitz)${NC}"
fi

# Check requests
if python3 -c "import requests" 2>/dev/null; then
    echo -e "${GREEN}  ✓ requests${NC}"
else
    echo -e "${RED}  ✗ requests${NC}"
fi

# Check openai
if python3 -c "import openai" 2>/dev/null; then
    echo -e "${GREEN}  ✓ openai${NC}"
else
    echo -e "${RED}  ✗ openai${NC}"
fi

echo ""
echo "========================================================================"
echo "Setup Complete!"
echo "========================================================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Activate the virtual environment (if not already active):"
echo "   ${GREEN}source .venv/bin/activate${NC}"
echo ""
echo "2. Configure your settings in config.py:"
echo "   - Set LLM API keys (if using LLM verification)"
echo "   - Adjust WORKER_THREADS for your CPU"
echo "   - Customize regex patterns"
echo ""
echo "3. Test the installation:"
echo "   ${GREEN}python3 test_modules.py${NC}"
echo ""
echo "4. Run the pipeline:"
echo "   ${GREEN}python3 rewat_pipeline.py <english_pdf> <hindi_pdf>${NC}"
echo ""
echo "For more information, see:"
echo "  - README.md"
echo "  - UBUNTU_SETUP.md"
echo ""
echo "Happy extracting! 🚀"
echo ""
