#!/bin/bash

# Install dependencies using pip directly (simplified approach)
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

# Install additional system dependencies that might be needed
echo "Installing system dependencies..."
apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    python3-dev \
    build-essential

# Apply database migrations if needed
echo "Setting up the application..."
python -m flask db upgrade || echo "No migrations to apply or migrations failed"

echo "Build completed successfully!"