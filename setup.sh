#!/usr/bin/env bash
#
# Scanifest Destiny - Setup Script (macOS/Linux)
#

set -e

echo "============================================"
echo "  Scanifest Destiny - Setup"
echo "============================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR] Python 3 is not installed or not in PATH.${NC}"
    echo "Please install Python 3.10+ from https://python.org"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1)
echo -e "${GREEN}Found: $PYTHON_VERSION${NC}"

# Check for existing venv
if [ -d "venv" ]; then
    echo ""
    echo -e "${YELLOW}[INFO] Virtual environment already exists.${NC}"
    read -p "Rebuild it? (y/N): " REBUILD
    if [[ "$REBUILD" =~ ^[Yy]$ ]]; then
        echo "Removing old venv..."
        rm -rf venv
    else
        echo "Skipping venv creation."
    fi
fi

# Create virtual environment if needed
if [ ! -d "venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}[ERROR] Failed to create virtual environment.${NC}"
        exit 1
    fi
    echo -e "${GREEN}[OK] Virtual environment created.${NC}"
fi

# Activate and install dependencies
echo ""
echo "Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo -e "${RED}[ERROR] Failed to install dependencies.${NC}"
    exit 1
fi
echo -e "${GREEN}[OK] Dependencies installed.${NC}"

# Check Tesseract installation
echo ""
echo "Checking Tesseract OCR..."
if command -v tesseract &> /dev/null; then
    TESS_VERSION=$(tesseract --version 2>&1 | head -n 1)
    echo -e "${GREEN}[OK] Found: $TESS_VERSION${NC}"
else
    echo -e "${YELLOW}[WARNING] Tesseract OCR not found.${NC}"
    echo ""
    echo "Please install Tesseract:"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "  macOS:   brew install tesseract"
    else
        echo "  Ubuntu:  sudo apt install tesseract-ocr"
        echo "  Fedora:  sudo dnf install tesseract"
        echo "  Arch:    sudo pacman -S tesseract"
    fi
    echo ""
    echo "The tool will still work for text-based PDFs without Tesseract."
fi

# Check Claude CLI
echo ""
echo "Checking Claude Code CLI..."
if command -v claude &> /dev/null; then
    echo -e "${GREEN}[OK] Claude Code CLI found.${NC}"
else
    echo -e "${YELLOW}[WARNING] Claude Code CLI not found.${NC}"
    echo "Please install Claude Code: https://claude.ai/code"
fi

# Create data directories if missing
mkdir -p data logs

echo ""
echo "============================================"
echo "  Setup complete!"
echo "============================================"
echo ""
echo "Run './run.sh --help' to see available commands."
echo ""
