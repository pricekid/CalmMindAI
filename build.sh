#!/usr/bin/env bash
# Build script for Render

echo "Starting build process for Dear Teddy application..."

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Copy any static assets that need to be available
echo "Setting up static directories..."
mkdir -p static/audio
chmod -R 755 static

# Run database initialization for Render
echo "Running database initialization..."
python render_db_init.py

# Create test user directly in the database
echo "Ensuring test user exists..."
python create_direct_entry.py

# Verify database state
echo "Verifying database configuration..."
python verify_database.py

echo "Build process completed successfully!"