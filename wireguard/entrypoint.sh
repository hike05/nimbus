#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[WireGuard]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WireGuard]${NC} $1"
}

error() {
    echo -e "${RED}[WireGuard]${NC} $1"
}

# Configuration paths
WG_CONFIG_DIR="/config"
WG_INTERFACE="wg0"
WG_CONFIG_FILE="${WG_CONFIG_DIR}/${WG_INTERFACE}.conf"
WG_KEYS_DIR="${WG_CONFIG_DIR}/keys"
WG_PEER_DIR="${WG_CONFIG_DIR}/peer_configs"

# Default configuration
WG_PORT="${WG_PORT:-51820}"
WG_ADDRESS="${WG_ADDRESS:-10.13.13.1/24}"
WG_DNS="${WG_DNS:-1.1.1.1,8.8.8.8}"

# Obfuscation settings
ENABLE_WEBSOCKET="${ENABLE_WEBSOCKET:-true}"
ENABLE_UDP2RAW="${ENABLE_UDP2RAW:-false}"
WEBSOCKET_PORT="${WEBSOCKET_PORT:-8006}"
UDP2RAW_PORT="${UDP2RAW_PORT:-8007}"
UDP2RAW_KEY="${UDP2RAW_KEY:-$(head -c 32 /dev/urandom | base64)}"

log "Starting WireGuard service with obfuscation..."

# Create directories if they don't exist
mkdir -p "${WG_KEYS_DIR}" "${WG_PEER_DIR}"

# Generate server keys if they don't exist
if [ ! -f "${WG_KEYS_DIR}/server_private.key" ]; then
    log "Generating server keys..."
    wg genkey | tee "${WG_KEYS_DIR}/server_private.key" | wg pubkey > "${WG_KEYS_DIR}/server_public.key"
    chmod 600 "${WG_KEYS_DIR}/server_private.key"
    log "Server public key: $(cat ${WG_KEYS_DIR}/server_public.key)"
fi

SERVER_PRIVATE_KEY=$(cat "${WG_KEYS_DIR}/server_private.key")
SERVER_PUBLIC_KEY=$(cat "${WG_KEYS_DIR}/server_public.key")

# Generate base WireGuard configuration if it doesn't exist
if [ ! -f "${WG_CONFIG_FILE}" ]; then
    log "Creating WireGuard configuration..."
    cat > "${WG_CONFIG_FILE}" <<EOF
[Interface]
Address = ${WG_ADDRESS}
ListenPort = ${WG_PORT}
PrivateKey = ${SERVER_PRIVATE_KEY}
PostUp = iptables -A FORWARD -i ${WG_INTERFACE} -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i ${WG_INTERFACE} -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

# Peers will be added dynamically
EOF
    chmod 600 "${WG_CONFIG_FILE}"
fi

# Enable IP forwarding
log "Enabling IP forwarding..."
sysctl -w net.ipv4.ip_forward=1 > /dev/null
sysctl -w net.ipv6.conf.all.forwarding=1 > /dev/null

# Load WireGuard kernel module (if not already loaded)
if ! lsmod | grep -q wireguard; then
    warn "WireGuard kernel module not loaded, attempting to load..."
    modprobe wireguard || warn "Could not load WireGuard module, using userspace implementation"
fi

# Start WireGuard interface
log "Starting WireGuard interface ${WG_INTERFACE}..."
wg-quick up "${WG_INTERFACE}" || {
    error "Failed to start WireGuard interface"
    exit 1
}

# Verify WireGuard is running
if wg show "${WG_INTERFACE}" > /dev/null 2>&1; then
    log "WireGuard interface ${WG_INTERFACE} is up"
    wg show "${WG_INTERFACE}"
else
    error "WireGuard interface failed to start"
    exit 1
fi

# Start WebSocket proxy if enabled
if [ "${ENABLE_WEBSOCKET}" = "true" ]; then
    log "Starting WebSocket proxy on port ${WEBSOCKET_PORT}..."
    websockify --web=/dev/null \
        --cert=/etc/letsencrypt/live/*/fullchain.pem \
        --key=/etc/letsencrypt/live/*/privkey.pem \
        0.0.0.0:${WEBSOCKET_PORT} \
        127.0.0.1:${WG_PORT} \
        > /var/log/wireguard/websocket.log 2>&1 &
    
    WEBSOCKET_PID=$!
    log "WebSocket proxy started with PID ${WEBSOCKET_PID}"
    
    # Save PID for cleanup
    echo ${WEBSOCKET_PID} > /var/run/websocket.pid
fi

# Start udp2raw if enabled
if [ "${ENABLE_UDP2RAW}" = "true" ]; then
    log "Starting udp2raw TCP masking on port ${UDP2RAW_PORT}..."
    udp2raw -s \
        -l 0.0.0.0:${UDP2RAW_PORT} \
        -r 127.0.0.1:${WG_PORT} \
        --raw-mode faketcp \
        --cipher-mode aes256gcm \
        --auth-mode hmac_sha256 \
        --key "${UDP2RAW_KEY}" \
        --seq-mode 4 \
        --fix-gro \
        --log-level 1 \
        > /var/log/wireguard/udp2raw.log 2>&1 &
    
    UDP2RAW_PID=$!
    log "udp2raw started with PID ${UDP2RAW_PID}"
    
    # Save PID and key for cleanup and client config
    echo ${UDP2RAW_PID} > /var/run/udp2raw.pid
    echo "${UDP2RAW_KEY}" > "${WG_KEYS_DIR}/udp2raw.key"
fi

# Cleanup function
cleanup() {
    log "Shutting down WireGuard service..."
    
    # Stop WebSocket proxy
    if [ -f /var/run/websocket.pid ]; then
        WEBSOCKET_PID=$(cat /var/run/websocket.pid)
        kill ${WEBSOCKET_PID} 2>/dev/null || true
        rm -f /var/run/websocket.pid
    fi
    
    # Stop udp2raw
    if [ -f /var/run/udp2raw.pid ]; then
        UDP2RAW_PID=$(cat /var/run/udp2raw.pid)
        kill ${UDP2RAW_PID} 2>/dev/null || true
        rm -f /var/run/udp2raw.pid
    fi
    
    # Stop WireGuard interface
    wg-quick down "${WG_INTERFACE}" || true
    
    log "WireGuard service stopped"
    exit 0
}

trap cleanup SIGTERM SIGINT

log "WireGuard service is ready"
log "Native WireGuard: UDP port ${WG_PORT}"
[ "${ENABLE_WEBSOCKET}" = "true" ] && log "WebSocket transport: TCP port ${WEBSOCKET_PORT}"
[ "${ENABLE_UDP2RAW}" = "true" ] && log "udp2raw transport: TCP port ${UDP2RAW_PORT}"

# Keep container running and monitor WireGuard
while true; do
    if ! wg show "${WG_INTERFACE}" > /dev/null 2>&1; then
        error "WireGuard interface ${WG_INTERFACE} is down, restarting..."
        wg-quick up "${WG_INTERFACE}" || {
            error "Failed to restart WireGuard interface"
            sleep 5
            continue
        }
    fi
    
    # Log peer count every 5 minutes
    PEER_COUNT=$(wg show "${WG_INTERFACE}" peers | wc -l)
    if [ $(($(date +%s) % 300)) -eq 0 ]; then
        log "Active peers: ${PEER_COUNT}"
    fi
    
    sleep 10
done
