# Stealth VPN Server

A multi-protocol VPN server that masquerades as a legitimate cloud storage service to avoid detection and blocking.

## Project Structure

```
stealth-vpn-server/
├── docker-compose.yml          # Main Docker orchestration
├── .env.example               # Environment configuration template
├── install.sh                 # Automated installation script
├── README.md                  # This file
│
├── config/
│   └── Caddyfile             # Caddy web server configuration
│
├── core/
│   └── interfaces.py         # Core system interfaces and data models
│
├── admin-panel/              # Admin panel Docker container
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── templates/            # HTML templates
│   └── static/              # CSS/JS assets
│
└── data/                    # Persistent data (created during setup)
    ├── stealth-vpn/         # VPN configurations and user data
    │   ├── configs/         # Generated VPN server configs
    │   └── backups/         # Automatic backups
    ├── caddy/               # SSL certificates and Caddy data
    └── www/                 # Static website files
```

## Quick Start

1. **Clone and setup:**
   ```bash
   git clone <repository>
   cd stealth-vpn-server
   ./install.sh
   ```

2. **Configure:**
   ```bash
   # Edit environment variables
   cp .env.example .env
   nano .env
   
   # Update Caddyfile with your domain
   nano config/Caddyfile
   ```

3. **Deploy:**
   ```bash
   docker compose up -d
   ```

4. **Access admin panel:**
   - URL: `https://your-domain.com/api/v2/storage/upload`
   - Credentials: Check `.env` file for generated password

## Architecture

The system consists of 6 Docker containers:

- **caddy**: Web server and reverse proxy (ports 80, 443)
- **xray**: Xray-core for VLESS protocols
- **trojan**: Trojan-Go server
- **singbox**: Sing-box for ShadowTLS, Hysteria2, TUIC
- **wireguard**: WireGuard with obfuscation
- **admin**: Admin panel for user management

All VPN traffic is masked as legitimate HTTPS/WebSocket/HTTP3 traffic through the Caddy reverse proxy.

## Security Features

- **Traffic Masking**: All VPN protocols disguised as standard web traffic
- **Endpoint Obfuscation**: Admin panel and VPN endpoints use realistic paths
- **Multiple Protocols**: Fallback options if one protocol is blocked
- **Automatic HTTPS**: Let's Encrypt certificates with auto-renewal
- **Container Isolation**: Each service runs in isolated Docker containers

## Requirements

- Ubuntu/Debian Linux server
- Docker and Docker Compose v2
- Domain name pointing to server IP
- Ports 80 and 443 accessible from internet

## Next Steps

After completing this task, the following tasks can be implemented:

1. Cover web service (static website)
2. VPN protocol implementations (Xray, Trojan, Sing-box, WireGuard)
3. Admin panel functionality
4. User management system
5. Configuration generators
6. Monitoring and logging

## Support

This is the foundation structure. Individual components will be implemented in subsequent tasks according to the implementation plan.