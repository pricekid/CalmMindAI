#!/bin/bash

# Check if poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "Poetry not found, installing..."
    curl -sSL https://install.python-poetry.org | python3 -
fi

# Generate requirements.txt from pyproject.toml
echo "Generating requirements.txt from pyproject.toml..."
poetry export -f requirements.txt --output requirements.txt --without-hashes

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt

echo "Build completed successfully!"