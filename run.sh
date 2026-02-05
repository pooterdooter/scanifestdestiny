#!/usr/bin/env bash
#
# Scanifest Destiny - Run Script (macOS/Linux)
#

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if venv exists
if [ ! -f "$SCRIPT_DIR/venv/bin/activate" ]; then
    echo "[ERROR] Virtual environment not found."
    echo "Please run ./setup.sh first."
    exit 1
fi

# Activate venv and run
source "$SCRIPT_DIR/venv/bin/activate"
python -m src.main "$@"
EXIT_CODE=$?

exit $EXIT_CODE
