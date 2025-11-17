# WireGuard Service Usage Guide

## Overview

The WireGuard service provides high-performance VPN connectivity with multiple obfuscation methods to evade detection. All WireGuard traffic can be disguised as legitimate HTTPS traffic through WebSocket tunneling or TCP masking.

## Transport Methods

### 1. WebSocket over HTTPS (Recommended)
- **Port**: 8006 (TCP)
- **Obfuscation**: WireGuard UDP traffic tunneled through HTTPS WebSocket
- **Masquerade**: Appears as font file download (`/static/fonts/woff2/roboto-regular.woff2`)
- **Best for**: Environments with strict DPI and UDP blocking

### 2. udp2raw TCP Masking
- **Port**: 8007 (TCP)
- **Obfuscation**: UDP packets converted to fake TCP packets with HTTPS characteristics
- **Best for**: Networks that block UDP but allow TCP

### 3. Native WireGuard
- **Port**: 51820 (UDP)
- **Obfuscation**: None
- **Best for**: Testing and environments without VPN detection

## Configuration Management

### Generate Server Configuration

```bash
# Generate server config with all active users
python3 scripts/wireguard-config-manager.py server

# Show generated configuration
python3 scripts/wireguard-config-manager.py server --show
```

### Generate Client Configurations

```bash
# Generate all client configs for a user
python3 scripts/wireguard-config-manager.py client --username alice --domain vpn.example.com

# Show generated configs
python3 scripts/wireguard-config-manager.py client --username alice --domain vpn.example.com --show
```

This generates three configuration files:
- `wg-websocket.conf` - WebSocket transport
- `wg-udp2raw.conf` - udp2raw transport
- `wg-native.conf` - Native WireGuard

### List Peers

```bash
# List all configured peers
python3 scripts/wireguard-config-manager.py list
```

### Show Obfuscation Parameters

```bash
# Display obfuscation settings
python3 scripts/wireguard-config-manager.py obfuscation
```

## Service Management

### Setup WireGuard Service

```bash
# Initial setup (creates directories, generates keys)
./scripts/setup-wireguard.sh
```

### Start/Stop Service

```bash
# Start WireGuard container
docker compose up -d wireguard

# Stop WireGuard container
docker compose stop wireguard

# Restart WireGuard container
docker compose restart wireguard

# View logs
docker compose logs -f wireguard
```

### Graceful Configuration Reload

```bash
# Reload configuration without dropping connections
docker compose exec wireguard wg syncconf wg0 /config/wg0.conf
```

## Client Setup

### WebSocket Transport (Recommended)

1. Install WireGuard client on your device
2. Use the `wg-websocket.conf` configuration file
3. The client will connect through HTTPS WebSocket on port 8006
4. Traffic appears as legitimate font file downloads

**Example client config:**
```ini
[Interface]
PrivateKey = <client-private-key>
Address = 10.13.13.2/32
DNS = 1.1.1.1, 8.8.8.8

[Peer]
PublicKey = <server-public-key>
Endpoint = vpn.example.com:8006
# WebSocket over HTTPS transport
AllowedIPs = 0.0.0.0/0, ::/0
PersistentKeepalive = 25
```

### udp2raw Transport

1. Install WireGuard client
2. Install udp2raw client on your device
3. Use the `wg-udp2raw.conf` configuration
4. UDP traffic is masked as TCP with HTTPS characteristics

### Native Transport

1. Install WireGuard client
2. Use the `wg-native.conf` configuration
3. Direct UDP connection (no obfuscation)

## Architecture

```
Client Device
    ↓
[WireGuard Client]
    ↓
[WebSocket/udp2raw Client] (optional obfuscation layer)
    ↓
Internet (HTTPS/TCP traffic)
    ↓
[Caddy Reverse Proxy] (port 443)
    ↓
[WebSocket Proxy] (port 8006) or [udp2raw Server] (port 8007)
    ↓
[WireGuard Server] (port 51820 internal)
    ↓
Internet
```

## Security Features

### Traffic Obfuscation
- **WebSocket**: Tunnels through standard HTTPS WebSocket connections
- **udp2raw**: Converts UDP to fake TCP packets with realistic timing
- **Realistic headers**: Mimics font file downloads and web traffic

### Encryption
- **WireGuard**: ChaCha20-Poly1305 encryption
- **TLS 1.3**: Additional encryption layer for WebSocket transport
- **Double encryption**: WireGuard + TLS for WebSocket method

### Anti-Detection
- **Timing randomization**: Prevents pattern analysis
- **Packet size normalization**: Matches typical web traffic
- **Realistic endpoints**: Uses common web resource paths

## Troubleshooting

### Check WireGuard Interface Status

```bash
# View interface status
docker compose exec wireguard wg show wg0

# View detailed interface info
docker compose exec wireguard ip addr show wg0
```

### Test Configuration

```bash
# Validate configuration
python3 scripts/wireguard-config-manager.py test

# Show configuration
python3 scripts/wireguard-config-manager.py test --show
```

### Check Logs

```bash
# View WireGuard logs
docker compose logs wireguard

# View WebSocket proxy logs
docker compose exec wireguard cat /var/log/wireguard/websocket.log

# View udp2raw logs
docker compose exec wireguard cat /var/log/wireguard/udp2raw.log
```

### Common Issues

**Issue**: WireGuard interface won't start
- Check kernel module: `lsmod | grep wireguard`
- Check container capabilities: `docker inspect stealth-wireguard | grep -A 10 CapAdd`

**Issue**: WebSocket proxy not working
- Verify SSL certificates are mounted: `docker compose exec wireguard ls /etc/letsencrypt/live/`
- Check WebSocket port is accessible: `netstat -tuln | grep 8006`

**Issue**: Clients can't connect
- Verify firewall rules allow port 443 (for WebSocket)
- Check Caddy is routing to WireGuard: `docker compose logs caddy | grep wireguard`
- Verify peer is in server config: `python3 scripts/wireguard-config-manager.py list`

## Integration Testing

```bash
# Run integration tests
python3 scripts/test-wireguard-integration.py
```

This tests:
- Server configuration generation
- Client configuration generation
- Key pair generation
- Peer management
- Obfuscation parameters
- Configuration file operations

## Performance Tuning

### Optimize for Speed

```bash
# Increase MTU for better performance (if network supports it)
# Edit wg0.conf:
MTU = 1420

# Adjust kernel parameters
sysctl -w net.core.rmem_max=2500000
sysctl -w net.core.wmem_max=2500000
```

### Optimize for Stealth

```bash
# Enable both obfuscation methods
# In docker-compose.yml:
ENABLE_WEBSOCKET=true
ENABLE_UDP2RAW=true

# Use smaller packet sizes to blend with web traffic
# In wg0.conf:
MTU = 1280
```

## Best Practices

1. **Always use obfuscation** in production environments
2. **Prefer WebSocket transport** for maximum compatibility
3. **Rotate keys regularly** for enhanced security
4. **Monitor logs** for connection issues
5. **Test configurations** before deploying to users
6. **Keep backups** of working configurations
7. **Use strong DNS** (1.1.1.1, 8.8.8.8) to prevent DNS leaks

## Advanced Configuration

### Custom WebSocket Path

Edit `core/wireguard_manager.py`:
```python
params['websocket_path'] = '/your/custom/path'
```

Update Caddyfile to match the new path.

### Custom udp2raw Key

```bash
# Generate new key
head -c 32 /dev/urandom | base64 > data/stealth-vpn/configs/wireguard/keys/udp2raw.key

# Restart WireGuard service
docker compose restart wireguard
```

### Multiple Server Instances

You can run multiple WireGuard instances on different ports by:
1. Duplicating the wireguard service in docker-compose.yml
2. Using different port numbers
3. Creating separate configuration directories

## References

- [WireGuard Official Documentation](https://www.wireguard.com/)
- [udp2raw GitHub](https://github.com/wangyu-/udp2raw)
- [WebSocket Protocol](https://tools.ietf.org/html/rfc6455)
