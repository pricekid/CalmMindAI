#!/bin/bash
set -euo pipefail

# Print Python version for debugging
python --version

# Install dependencies
pip install -U pip
pip install -r requirements.txt
pip install gunicorn

# Check for common package issues
pip check || echo "Warning: Package dependency check found issues"

# Create necessary directories
mkdir -p data
mkdir -p static/audio
mkdir -p flask_session

# Set Render environment flag
echo "Setting up Render-specific configuration"
export RENDER=true

# Print success message
echo "Build completed successfully"