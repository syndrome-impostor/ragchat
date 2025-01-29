#!/usr/bin/env bash
# If you want to redo the install, delete the venv folder and run this script again.
if [ ! -d "venv" ]; then
    echo "[INFO] Creating virtual environment..."
    python -m venv venv
    source venv/bin/activate

    echo "[INFO] Upgrading pip and installing base requirements..."
    python -m pip install --upgrade pip
    
    # Install PyTorch with ROCm support if specified in config.yaml
    if grep -q 'type: *"rocm"' config.yaml; then
        echo "Installing PyTorch with ROCm support..."
        python3 -m pip install torch --index-url https://download.pytorch.org/whl/nightly/rocm6.3
    else
        echo "Installing PyTorch without ROCm..."
        python3 -m pip install torch
    fi

    python -m pip install -r requirements.txt
    pip install -e .
    echo "[INFO] Running install_steps.py..."
    python src/bot/install_steps.py 
else
    source venv/bin/activate
fi

# Run the bot module with any provided arguments
python -m bot "$@"