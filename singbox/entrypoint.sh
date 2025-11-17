#!/bin/sh
set -e

# Sing-box entrypoint script with security hardening

CONFIG_FILE="/etc/sing-box/singbox.json"
LOG_DIR="/var/log/sing-box"

# Create necessary directories if they don't exist
mkdir -p "$LOG_DIR" /var/lib/sing-box

# Set proper permissions (running as singbox user)
chown -R singbox:singbox "$LOG_DIR" /var/lib/sing-box

# Wait for configuration file (with timeout)
echo "Waiting for Sing-box configuration..."
TIMEOUT=300
ELAPSED=0
while [ ! -f "$CONFIG_FILE" ] && [ $ELAPSED -lt $TIMEOUT ]; do
    echo "Configuration file not found at $CONFIG_FILE, waiting... ($ELAPSED/$TIMEOUT seconds)"
    sleep 5
    ELAPSED=$((ELAPSED + 5))
done

if [ ! -f "$CONFIG_FILE" ]; then
    echo "ERROR: Configuration file not found after ${TIMEOUT} seconds"
    exit 1
fi

echo "Configuration file found, validating..."

# Validate configuration
if ! sing-box check -c "$CONFIG_FILE"; then
    echo "ERROR: Invalid Sing-box configuration"
    exit 1
fi

echo "Configuration valid, starting Sing-box as non-root user..."

# Start Sing-box with the configuration
exec sing-box run -c "$CONFIG_FILE"