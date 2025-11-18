#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[Setup]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[Setup]${NC} $1"
}

error() {
    echo -e "${RED}[Setup]${NC} $1"
}

log "Setting up WireGuard proxy service..."

# Configuration directories
WG_CONFIG_DIR="./data/proxy/configs/wireguard"
WG_KEYS_DIR="${WG_CONFIG_DIR}/keys"
WG_PEER_DIR="${WG_CONFIG_DIR}/peer_configs"
WG_LOG_DIR="./data/proxy/logs/wireguard"

# Create directories
log "Creating WireGuard directories..."
mkdir -p "${WG_CONFIG_DIR}"
mkdir -p "${WG_KEYS_DIR}"
mkdir -p "${WG_PEER_DIR}"
mkdir -p "${WG_LOG_DIR}"

# Set proper permissions
chmod 700 "${WG_KEYS_DIR}"
chmod 755 "${WG_CONFIG_DIR}"
chmod 755 "${WG_PEER_DIR}"

# Check if WireGuard tools are available in container
log "Checking WireGuard container..."
if ! docker compose ps wireguard | grep -q "Up"; then
    warn "WireGuard container is not running, starting it..."
    docker compose up -d wireguard
    sleep 5
fi

# Generate server keys if they don't exist
if [ ! -f "${WG_KEYS_DIR}/server_private.key" ]; then
    log "Generating WireGuard server keys..."
    
    # Generate keys using the container
    PRIVATE_KEY=$(docker compose exec -T wireguard wg genkey)
    PUBLIC_KEY=$(echo "${PRIVATE_KEY}" | docker compose exec -T wireguard wg pubkey)
    
    echo "${PRIVATE_KEY}" > "${WG_KEYS_DIR}/server_private.key"
    echo "${PUBLIC_KEY}" > "${WG_KEYS_DIR}/server_public.key"
    
    chmod 600 "${WG_KEYS_DIR}/server_private.key"
    chmod 600 "${WG_KEYS_DIR}/server_public.key"
    
    log "Server public key: ${PUBLIC_KEY}"
else
    log "WireGuard server keys already exist"
    PUBLIC_KEY=$(cat "${WG_KEYS_DIR}/server_public.key")
    log "Server public key: ${PUBLIC_KEY}"
fi

# Generate udp2raw key if it doesn't exist
if [ ! -f "${WG_KEYS_DIR}/udp2raw.key" ]; then
    log "Generating udp2raw obfuscation key..."
    UDP2RAW_KEY=$(head -c 32 /dev/urandom | base64)
    echo "${UDP2RAW_KEY}" > "${WG_KEYS_DIR}/udp2raw.key"
    chmod 600 "${WG_KEYS_DIR}/udp2raw.key"
    log "udp2raw key generated"
else
    log "udp2raw key already exists"
fi

# Create base WireGuard configuration if it doesn't exist
WG_CONFIG_FILE="${WG_CONFIG_DIR}/wg0.conf"
if [ ! -f "${WG_CONFIG_FILE}" ]; then
    log "Creating base WireGuard configuration..."
    
    PRIVATE_KEY=$(cat "${WG_KEYS_DIR}/server_private.key")
    
    cat > "${WG_CONFIG_FILE}" <<EOF
[Interface]
Address = 10.13.13.1/24
ListenPort = 51820
PrivateKey = ${PRIVATE_KEY}
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

# Peers will be added dynamically by the admin panel
EOF
    
    chmod 600 "${WG_CONFIG_FILE}"
    log "Base configuration created"
else
    log "WireGuard configuration already exists"
fi

# Check WireGuard service status
log "Checking WireGuard proxy service status..."
if docker compose exec -T wireguard wg show wg0 > /dev/null 2>&1; then
    log "WireGuard interface is up and running"
    docker compose exec -T wireguard wg show wg0
else
    warn "WireGuard interface is not up yet"
    log "The interface will be started by the container entrypoint"
fi

# Display obfuscation endpoints
log ""
log "WireGuard Obfuscation Endpoints:"
log "  - Native WireGuard: UDP port 51820 (internal only)"
log "  - WebSocket transport: TCP port 8006 (HTTPS)"
log "  - udp2raw transport: TCP port 8007 (TCP masking)"
log ""
log "All external connections should use WebSocket or udp2raw for obfuscation"

log "WireGuard proxy service setup complete!"
