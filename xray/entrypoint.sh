#!/bin/sh
set -e

# Create log directory if it doesn't exist
mkdir -p /var/log/xray /var/lib/xray

# Set proper permissions
chown -R xray:xray /var/log/xray /var/lib/xray

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

echo "SSL certificates found, starting Xray..."

# Validate configuration before starting
if ! /usr/bin/xray test -config /etc/xray/xray.json; then
    echo "ERROR: Invalid Xray configuration"
    exit 1
fi

# Drop privileges and start Xray
exec su-exec xray:xray /usr/bin/xray run -config /etc/xray/xray.json