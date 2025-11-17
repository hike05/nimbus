#!/bin/sh
set -e

# Trojan-Go entrypoint script with security hardening

# Default configuration file
CONFIG_FILE="${CONFIG_FILE:-/etc/trojan-go/trojan.json}"

# Wait for certificates to be available (with timeout)
echo "Waiting for SSL certificates..."
TIMEOUT=300
ELAPSED=0
while [ ! -f "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" ] && [ $ELAPSED -lt $TIMEOUT ]; do
    echo "SSL certificates not found, waiting... ($ELAPSED/$TIMEOUT seconds)"
    sleep 10
    ELAPSED=$((ELAPSED + 10))
done

if [ ! -f "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" ]; then
    echo "ERROR: SSL certificates not found after ${TIMEOUT} seconds"
    exit 1
fi

echo "SSL certificates found, validating configuration..."

# Validate configuration file
if [ ! -f "$CONFIG_FILE" ]; then
    echo "ERROR: Configuration file $CONFIG_FILE not found"
    exit 1
fi

# Validate JSON syntax
if ! python3 -m json.tool "$CONFIG_FILE" > /dev/null 2>&1; then
    echo "ERROR: Invalid JSON in configuration file"
    exit 1
fi

# Create log directory if it doesn't exist
mkdir -p /var/log/trojan-go /var/lib/trojan-go

# Set proper permissions (running as trojan user)
chown -R trojan:trojan /var/log/trojan-go /var/lib/trojan-go

# Start Trojan-Go with the configuration
echo "Starting Trojan-Go server as non-root user..."
exec trojan-go -config "$CONFIG_FILE"