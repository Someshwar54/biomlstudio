#!/bin/bash

echo "Installing heavy ML dependencies (torch CPU)..."

pip install torch==2.0.1+cpu -f https://download.pytorch.org/whl/cpu/torch_stable.html

echo "Heavy deps installed."