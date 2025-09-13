#!/bin/sh
set -e

if [ ! -f /mnt/config.yml ]; then
  echo 'Error: /mnt/config.yml file not found. Please mount the /mnt/config.yml file and try again.'
  exit 1
fi

# Start D-Bus session for Cypress
eval $(dbus-launch --sh-syntax)
export DBUS_SESSION_BUS_ADDRESS

# Start Xvfb virtual display for headless Cypress
Xvfb :99 -ac -screen 0 1280x1024x16 &
XVFB_PID=$!

# Wait a moment for Xvfb to start
sleep 2

# Verify Cypress installation
echo "Verifying Cypress installation..."
npx cypress verify

cp -f /mnt/config.yml /app/config.yml

# Cleanup function
cleanup() {
    echo "Shutting down..."
    kill $XVFB_PID 2>/dev/null || true
    exit
}

# Set up signal handlers for cleanup
trap cleanup TERM INT

exec /app/.venv/bin/python -u main.py
