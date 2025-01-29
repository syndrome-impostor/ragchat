#!/bin/bash

# Source environment configuration
source venv/bin/activate

# Run GPU tests
echo "Running GPU tests..."
PYTHONPATH=. python3 src/bot/cuda_test.py 