# Product Overview

Stealth VPN Server is a multi-protocol VPN system designed to evade detection and blocking by masquerading as a legitimate cloud storage service. The system disguises VPN traffic as standard HTTPS/WebSocket/HTTP3 traffic through obfuscated endpoints.

## Core Capabilities

- Multi-protocol VPN support: Xray (VLESS), Trojan-Go, Sing-box (ShadowTLS, Hysteria2, TUIC), WireGuard
- Traffic masking through Caddy reverse proxy with realistic endpoint paths
- Admin panel for user management disguised as a storage API endpoint
- Automatic HTTPS with Let's Encrypt certificate management
- Client configuration generation for all supported protocols

## Security Model

- All VPN protocols disguised as legitimate web traffic
- Obfuscated admin panel endpoints (e.g., `/api/v2/storage/upload`)
- Container isolation for each VPN service
- Cover website serving as legitimate front-end
- Multiple protocol fallbacks if one is blocked

## Target Deployment

- Ubuntu/Debian Linux servers
- Docker-based containerized architecture
- Requires domain name with ports 80/443 accessible
- Designed for environments with VPN detection/blocking
