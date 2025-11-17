# Technology Stack

## Core Technologies

- **Container Platform**: Docker with Docker Compose v2
- **Reverse Proxy**: Caddy 2 (automatic HTTPS, HTTP/3 support)
- **Backend Language**: Python 3
- **Web Framework**: Flask 2.3.3
- **VPN Protocols**:
  - Xray-core (VLESS with XTLS-Vision and WebSocket)
  - Trojan-Go
  - Sing-box (ShadowTLS v3, Hysteria2, TUIC v5)
  - WireGuard with obfuscation

## Python Dependencies

- Flask 2.3.3 - Web framework for admin panel
- Werkzeug 2.3.7 - WSGI utilities
- bcrypt 4.0.1 - Password hashing
- qrcode[pil] 7.4.2 - QR code generation for client configs
- cryptography 41.0.7 - Cryptographic operations
- requests 2.31.0 - HTTP client

## Docker Services

All services run in isolated containers on the `stealth-vpn` bridge network:

- `caddy` - Web server and reverse proxy (ports 80, 443, 443/udp)
- `xray` - Xray-core VPN service
- `trojan` - Trojan-Go VPN service
- `singbox` - Sing-box multi-protocol service
- `wireguard` - WireGuard VPN service
- `admin` - Flask-based admin panel

## Common Commands

### Installation and Setup
```bash
./install.sh                    # Initial system setup
cp .env.example .env           # Create environment config
docker compose up -d           # Start all services
```

### Service Management
```bash
docker compose ps              # Check service status
docker compose logs -f         # View all logs
docker compose logs -f xray    # View specific service logs
docker compose restart xray    # Restart a service
docker compose down            # Stop all services
```

### Configuration Testing
```bash
# Test Xray configuration
python3 scripts/xray-config-manager.py test
python3 scripts/xray-config-manager.py validate

# Test Trojan configuration
python3 scripts/trojan-config-manager.py test

# Test Sing-box configuration
python3 scripts/singbox-config-manager.py test

# Integration tests
python3 scripts/test-xray-integration.py
python3 scripts/test-trojan-integration.py
python3 scripts/test-singbox-integration.py
```

### Health Checks
```bash
./scripts/health-check.sh      # Check all services
./scripts/caddy-health.sh      # Check Caddy specifically
```

### Configuration Generation
```bash
python3 scripts/generate-endpoints.py  # Generate obfuscated endpoints
```

## Build System

No build step required - Python scripts run directly. Docker images are built from Dockerfiles in service directories (`xray/`, `trojan/`, `singbox/`, `admin-panel/`).

## File Paths

- **Configs**: `./data/stealth-vpn/configs/`
- **Client Configs**: `./data/stealth-vpn/configs/clients/{username}/`
- **Logs**: `./data/stealth-vpn/logs/{service}/`
- **Backups**: `./data/stealth-vpn/backups/`
- **SSL Certs**: `./data/caddy/certificates/`
- **Web Files**: `./data/www/`
