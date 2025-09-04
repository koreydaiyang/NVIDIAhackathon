#!/bin/bash

# Load API keys from configuration file
echo "Loading API keys from api_keys.yml..."
python3 load_api_keys.py

if [ $? -ne 0 ]; then
    echo "Failed to load API keys. Please check your api_keys.yml file."
    exit 1
fi

# Load API keys into environment variables using Python
if [ -f "api_keys.yml" ]; then
    # Use Python to parse YAML and export variables
    eval $(python3 -c "
import yaml
import os
try:
    with open('api_keys.yml', 'r') as f:
        config = yaml.safe_load(f)
    for key, value in config.items():
        if isinstance(value, str) and value.strip():
            print(f'export {key}=\"{value}\"')
except Exception as e:
    print(f'echo \"Error loading API keys: {e}\"', file=sys.stderr)
")
else
    echo "Warning: api_keys.yml not found. Please create it with your API keys."
    echo "You can copy from api_keys.yml.template and fill in your actual keys."
fi

# Start the authentication server
echo "Starting authentication server..."
python auth_server.py &
AUTH_PID=$!
echo $AUTH_PID > .auth.pid

# Start the static file server for the frontend
echo "Starting static file server..."
python -m http.server 8081 &
STATIC_PID=$!
echo $STATIC_PID > .static.pid

echo "Servers started:"
echo "- Authentication server: http://localhost:8080"
echo "- Static file server: http://localhost:8081"
echo "- Dashboard: http://localhost:8080/dashboard.html"
echo ""
echo "To stop servers, run: ./stop_with_auth.sh"

# Wait for servers
wait