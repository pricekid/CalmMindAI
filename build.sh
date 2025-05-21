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
mkdir -p static/img
mkdir -p static/css
mkdir -p static/js
mkdir -p flask_session

# Copy static assets to ensure they're available
echo "Copying static assets..."
cp -r static/* static/ 2>/dev/null || true

# Check if some key files exist, create placeholder if needed
if [ ! -f "static/img/teddy-logo.png" ]; then
  echo "Creating placeholder logo"
  echo "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAGQAAABkCAYAAABw4pVUAAAACXBIWXMAAAsTAAALEwEAmpwYAAAEcElEQVR4nO2dy2sdVRiHH5O0qTXaJk3VJqkXvKGiKFoRRbQiiiBeuiJqFbHgwoXixoX+Be5cuBDcWDeuXLpyoYtaRQQXiuJdtDWk9ZKmJhFzPvgWQs4kc+acTG7vD94fJMycb86ZM9/MfPOdgYiIiIiIiIiIiIiIiIiIiIiIiIiIiBhPJoCbgFuBOWAaaFZ43A7cBXwMXAQGwHngUeBp4B3gS2AxvH8ReAO4vwxtIfq1fhgZNYAZ4F1gALzj+LoVWC+N08DHAXnL8rVKe8AMMAd8BfwDHAb2A3fleDrRry1hZDwEfAusBfTnwLwLaHVD7hkicdnwcyGE5/uAH0KZvwCPxCVvTAXDzwiRrAYkLQG3xCWOoc11W+C3p8NjwZEQvi4Dt9tcV8AUcCK0o58DVwfyfgEeiYsch8j8Bngt/P1b4PZAxjPAWTSB3VPX4MY6MraNkcCTKLIeBO5B4e89dYxtI6NYvzHfxxWOrkMjcVJRwL9DZdpAjzOVpMiawHYu6wIaDZtDhe3oOU0F+w2ZthjuFy4AD4/a6IsMRdQ+0aR2fzh/aAIHgCeBC8A7dcz3ySZi3gJeCZHmf+Cd8PoTaOUGsBomu3WK7Y+ELYD54NuAVpH7gSfCdj8FXqY1HQ1DthZ0Anh+9NY1YZRcBL4DvgZ+BH4CfkHrj0V0UPQvWkG1w/m/0Vn7OLc1TZyuHcOlrgCu81iE1BbpwEiviB10K8zrkMnA/cGQFDmyIWQTkUGkkRHJIJLIiGQQKLO7HMkg0GZ3uSoZfWC+4u5yuUnfGfmgAuMvVtBdXmwYnECb3eVKZCwB3wdXAx9ZAB4HnkMTbfJsDVGU3eVN4MGu+mKfhW/oUOi9dBIeIW13l8vuWOyK8+HLZZL92fIm3eXIEMxOiVNkmELsW3SbV3aXI0NMVW13eYgMQ8h4F93mlQPDUkZjxLOH6HaXiwz7E+a6ZJRxlwvFSsaE9cKQ492wPe4uF4qVDO/ey8PYXc5Dxqb2cSXDstcTsS6wlSHFzRCW7nJuGY7fh4i14a16mTwTNiWjsMhwKmStbJhbJx05jGToC1k7GyvUk8GoI4eXDPOeyFaGdecr6sgRJUOdBMvKdLZrmZLhmVLdM+nIESXDvOlvyXCLJnlZoZqOHF4yOqlGd0vGqKpRp+zIESXDJaqWpSOHk4xRbKKi4+vIkRTTkbOUYX0dYdVGjigZLrBuUWZsGfZ32sZNhnsb6sYxkmHcojpWSLfMTMmwvzUcIxnOhajLjWUgw7qNu2syXKJqGTtyRMlwialZ2pGzlOF8QTBuMqzbYGcjo6idMVMy7K8hx0xGEbFypmTY3/+OmYyiommqO3LUfZ6sZJjfxo6bjKJ2BUw6cpQy8l6Uj5uMonYkx0xGUTtioyajCJ+Vm4zi/LSG7c6i9XWNIaP+0lJnIrqmqKODNhlFnq7n+dqYXsXGu14ndpfbZNT9wDYi6slvRERERERERERERERERERE9Ej/AS1m+/fCVQPKAAAAAElFTkSuQmCC" > static/img/teddy-logo.png
fi

if [ ! -f "static/css/styles.css" ]; then
  echo "Creating placeholder CSS"
  echo "body { font-family: Arial, sans-serif; background-color: #f8f9fa; }" > static/css/styles.css
fi

if [ ! -f "static/css/bootstrap.min.css" ]; then
  echo "Downloading Bootstrap CSS"
  curl -s https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css > static/css/bootstrap.min.css || echo "Warning: Failed to download Bootstrap"
fi

# Create favicon.ico if missing
if [ ! -f "static/favicon.ico" ]; then
  echo "Creating placeholder favicon"
  echo "data:image/x-icon;base64,AAABAAEAEBAAAAEAIABoBAAAFgAAACgAAAAQAAAAIAAAAAEAIAAAAAAAAAQAABILAAASCwAAAAAAAAAAAAD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8AYjcMFWI3DEViNwxVYjcMVWI3DEViNwxVYjcMVWI3DEViNwxVYjcMVWI3DEViNwxVYjcMRWI3DBX///8AYjcMi2I3DP9iNwz/YjcM/2I3DP9iNwz/YjcM/2I3DP9iNwz/YjcM/2I3DP9iNwz/YjcM/2I3DP9iNwyL////AGI3DNtiNwz/YjcM/2I3DP9iNwz/YjcM/2I3DP9iNwz/YjcM/2I3DP9iNwz/YjcM/2I3DP9iNwz/YjcM2////wBiNwzbYjcM/2I3DP9iNwz/YjcM/2I3DP9iNwz/YjcM/2I3DP9iNwz/YjcM/2I3DP9iNwz/YjcM/2I3DNv///8AYjcM22I3DP9iNwz/YjcM/2I3DP9iNwz/YjcM/2I3DP9iNwz/YjcM/2I3DP9iNwz/YjcM/2I3DP9iNwzb////AGI3DNtiNwz/YjcM/2I3DP9iNwz/YjcM/2I3DP9iNwz/YjcM/2I3DP9iNwz/YjcM/2I3DP9iNwz/YjcM2////wBiNwzbYjcM/2I3DP9iNwz/YjcM/2I3DP9iNwz/YjcM/2I3DP9iNwz/YjcM/2I3DP9iNwz/YjcM/2I3DNv///8AYjcMi2I3DP9iNwz/YjcM/2I3DP9iNwz/YjcM/2I3DP9iNwz/YjcM/2I3DP9iNwz/YjcM/2I3DP9iNwyL////AGI3DBViNwxFYjcMVWI3DFViNwxVYjcMVWI3DFViNwxVYjcMVWI3DFViNwxVYjcMVWI3DEViNwwV////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A//8AAP//AAD//wAA//8AAP//AAD//wAA//8AAP//AAD//wAA//8AAP//AAD//wAA//8AAP//AAD//wAA//8AAA==" > static/favicon.ico
fi

# Copy favicon.ico to the root directory for browsers that look there
cp static/favicon.ico favicon.ico 2>/dev/null || true

# Set Render environment flag
echo "Setting up Render-specific configuration"
export RENDER=true

# Create a .env file for Render deployment
echo "Creating Render environment file"
cat > .env << EOF
RENDER=true
FLASK_ENV=production
FLASK_DEBUG=0
EOF

echo "Render deployment configuration complete"

# Print success message
echo "Build completed successfully"