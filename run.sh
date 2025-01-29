#!/usr/bin/env bash
# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# If you want to redo the install, delete the venv folder and run this script again.
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo "[INFO] Creating virtual environment..."
    python -m venv "$SCRIPT_DIR/venv"
    source "$SCRIPT_DIR/venv/bin/activate"

    echo "[INFO] Upgrading pip and installing base requirements..."
    python -m pip install --upgrade pip
    
    # Install PyTorch with ROCm support if specified in config.yaml
    if grep -q 'type: *"rocm"' "$SCRIPT_DIR/config.yaml"; then
        echo "Installing PyTorch with ROCm support..."
        python3 -m pip install torch --index-url https://download.pytorch.org/whl/nightly/rocm6.3
    else
        echo "Installing PyTorch without ROCm..."
        python3 -m pip install torch
    fi

    python -m pip install -r "$SCRIPT_DIR/requirements.txt"
    pip install -e "$SCRIPT_DIR"
    echo "[INFO] Running install_steps.py..."
    python "$SCRIPT_DIR/src/bot/install_steps.py"
else
    source "$SCRIPT_DIR/venv/bin/activate"
fi

# Run the bot module with any provided arguments
python -m bot "$@"