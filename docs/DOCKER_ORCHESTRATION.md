# Docker Orchestration Documentation

This document describes the Docker orchestration setup for Stealth VPN Server.

## Overview

The system uses Docker Compose to orchestrate 6 containerized services:
- **Caddy**: Reverse proxy and web server
- **Xray**: VLESS protocol VPN service
- **Trojan**: Trojan-Go protocol VPN service
- **Sing-box**: Multi-protocol VPN service (ShadowTLS, Hysteria2, TUIC)
- **WireGuard**: WireGuard VPN service with obfuscation
- **Admin**: Flask-based admin panel

## Docker Compose Configuration

### Service Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Internet                             │
└──────────────────────┬──────────────────────────────────────┘
                       │ Ports 80, 443, 443/udp
                       ▼
              ┌────────────────┐
              │  Caddy Proxy   │
              │  (Port 443)    │
              └────────┬───────┘
                       │
        ┌──────────────┼──────────────┬──────────────┐
        ▼              ▼              ▼              ▼
   ┌────────┐    ┌─────────┐    ┌─────────┐    ┌──────────┐
   │  Xray  │    │ Trojan  │    │Sing-box │    │WireGuard │
   │ :8001  │    │  :8002  │    │:8003-06 │    │  :8006   │
   │ :8004  │    │         │    │         │    │          │
   └────────┘    └─────────┘    └─────────┘    └──────────┘
        │              │              │              │
        └──────────────┴──────────────┴──────────────┘
                       │
                       ▼
              ┌────────────────┐
              │  Admin Panel   │
              │    :8010       │
              └────────────────┘
                       │
                       ▼
              ┌────────────────┐
              │  Shared Data   │
              │   Volumes      │
              └────────────────┘
```

### Network Configuration

- **Network Name**: `stealth-vpn`
- **Network Type**: Bridge
- **Subnet**: `172.20.0.0/16`
- **Gateway**: `172.20.0.1`

All services communicate through this isolated network, with only Caddy exposing ports to the internet.

### Volume Management

#### Named Volumes

Each service has its own named volume for persistent data:

- `stealth-caddy-data`: Caddy data and cache
- `stealth-caddy-config`: Caddy configuration
- `stealth-xray-data`: Xray runtime data
- `stealth-trojan-data`: Trojan runtime data
- `stealth-singbox-data`: Sing-box runtime data
- `stealth-wireguard-data`: WireGuard runtime data
- `stealth-admin-data`: Admin panel data

#### Bind Mounts

Shared configuration and data directories:

- `./data/stealth-vpn/configs`: VPN configurations
- `./data/stealth-vpn/logs`: Service logs
- `./data/caddy/certificates`: SSL certificates
- `./data/www`: Cover website files
- `./core`: Shared Python modules

### Health Checks

All services include health checks:

- **Interval**: 30 seconds
- **Timeout**: 10 seconds
- **Retries**: 3
- **Start Period**: 40 seconds

Health check commands:
- **Caddy**: `wget http://localhost:2019/config/`
- **Xray**: `pgrep xray`
- **Trojan**: `pgrep trojan-go`
- **Sing-box**: `pgrep sing-box`
- **WireGuard**: `wg show wg0`
- **Admin**: `python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8010/health')"`

### Service Dependencies

Caddy depends on all other services being healthy before starting:

```yaml
depends_on:
  admin:
    condition: service_healthy
  xray:
    condition: service_healthy
  trojan:
    condition: service_healthy
  singbox:
    condition: service_healthy
  wireguard:
    condition: service_healthy
```

This ensures proper startup order and prevents Caddy from routing to unhealthy services.

### Logging Configuration

All services use JSON file logging with rotation:

- **Max Size**: 10MB per file
- **Max Files**: 3 files retained
- **Total Storage**: ~30MB per service

Logs are also available via bind mounts in `./data/stealth-vpn/logs/`.

### Security Features

#### Container Security

- **no-new-privileges**: Prevents privilege escalation
- **read_only**: Read-only root filesystem (where applicable)
- **tmpfs**: Temporary filesystem for /tmp with noexec, nosuid

#### Network Isolation

- Services communicate only through the `stealth-vpn` network
- No direct internet access except through Caddy
- Internal ports not exposed to host

#### Capabilities

WireGuard requires special capabilities:
- `NET_ADMIN`: Network administration
- `SYS_MODULE`: Kernel module loading

Sysctls:
- `net.ipv4.conf.all.src_valid_mark=1`: Source validation
- `net.ipv4.ip_forward=1`: IP forwarding

## Deployment Automation

### Installation Script (`install.sh`)

The installation script automates:

1. **System Checks**
   - Verify OS compatibility (Ubuntu/Debian)
   - Check architecture
   - Ensure non-root execution

2. **Docker Installation**
   - Install Docker CE
   - Install Docker Compose v2
   - Add user to docker group

3. **Firewall Configuration**
   - Configure UFW rules
   - Allow ports 80, 443
   - Enable firewall

4. **Configuration Generation**
   - Create `.env` from template
   - Prompt for domain and email
   - Generate admin password hash
   - Generate session secret

5. **Directory Setup**
   - Create data directories
   - Set proper permissions
   - Initialize users.json

6. **Template Initialization**
   - Generate Xray config
   - Generate Trojan config
   - Generate Sing-box config
   - Generate WireGuard config

7. **Image Building**
   - Build all Docker images
   - Verify builds successful

8. **Service Startup**
   - Start all services
   - Wait for health checks
   - Display status

### Service Manager (`scripts/service-manager.sh`)

Utility for managing services:

```bash
# Start/stop/restart
./scripts/service-manager.sh start [service]
./scripts/service-manager.sh stop [service]
./scripts/service-manager.sh restart [service]

# Monitoring
./scripts/service-manager.sh status
./scripts/service-manager.sh logs [service] [lines]
./scripts/service-manager.sh health

# Maintenance
./scripts/service-manager.sh backup
./scripts/service-manager.sh restore <file>
./scripts/service-manager.sh rebuild [service]
./scripts/service-manager.sh cleanup
```

### Update Script (`scripts/update-system.sh`)

Handles system updates:

```bash
# Full update
./scripts/update-system.sh update

# Rollback
./scripts/update-system.sh rollback [file]

# Backup only
./scripts/update-system.sh backup
```

Update process:
1. Create backup
2. Pull latest code
3. Update Docker images
4. Migrate configurations
5. Restart services
6. Verify update
7. Display summary

### Makefile

Convenient shortcuts for common operations:

```bash
# Installation
make install

# Service management
make start
make stop
make restart
make status
make logs
make logs-xray

# User management
make add-user USER=alice
make list-users
make remove-user USER=alice

# Maintenance
make backup
make restore FILE=backup.tar.gz
make update
make rebuild
make clean

# Development
make build
make test
make validate
```

## Environment Configuration

### Required Variables

```bash
DOMAIN=your-domain.com
EMAIL=admin@your-domain.com
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=<bcrypt-hash>
SESSION_SECRET=<random-hex>
```

### Optional Variables

```bash
# Service Ports
XRAY_VISION_PORT=8001
XRAY_WEBSOCKET_PORT=8004
TROJAN_PORT=8002
SINGBOX_SHADOWTLS_PORT=8003
SINGBOX_HYSTERIA_PORT=8005
SINGBOX_TUIC_PORT=8006
WIREGUARD_SERVER_PORT=51820
WIREGUARD_WEBSOCKET_PORT=8006
ADMIN_PANEL_PORT=8010

# Network
VPN_SUBNET=10.66.66.0/24
DNS_SERVERS=1.1.1.1,8.8.8.8
TZ=UTC

# Security
RATE_LIMIT_ADMIN=5
RATE_LIMIT_VPN=1000
SESSION_TIMEOUT=3600

# Logging
LOG_LEVEL=INFO
LOG_RETENTION_DAYS=7
LOG_MAX_SIZE=10M
LOG_MAX_FILES=3
```

## Service Management

### Starting Services

```bash
# All services
docker compose up -d

# Specific service
docker compose up -d xray

# With logs
docker compose up
```

### Stopping Services

```bash
# All services
docker compose down

# Specific service
docker compose stop xray

# With volume removal
docker compose down -v
```

### Restarting Services

```bash
# All services
docker compose restart

# Specific service
docker compose restart xray

# Graceful reload
docker compose kill -s SIGHUP caddy
```

### Viewing Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f xray

# Last N lines
docker compose logs --tail=100 xray

# Since timestamp
docker compose logs --since=2024-01-01T00:00:00 xray
```

### Checking Status

```bash
# Service status
docker compose ps

# Detailed info
docker compose ps -a

# Resource usage
docker stats
```

## Backup and Restore

### Creating Backups

```bash
# Using service manager
./scripts/service-manager.sh backup

# Manual backup
tar -czf backup.tar.gz \
  data/stealth-vpn/configs \
  .env \
  docker-compose.yml
```

### Restoring from Backup

```bash
# Using service manager
./scripts/service-manager.sh restore backup.tar.gz

# Manual restore
docker compose down
tar -xzf backup.tar.gz
docker compose up -d
```

## Troubleshooting

### Services Won't Start

1. Check logs:
   ```bash
   docker compose logs -f
   ```

2. Verify configuration:
   ```bash
   cat .env
   docker compose config
   ```

3. Check dependencies:
   ```bash
   docker compose ps
   ```

### Health Checks Failing

1. Check service logs:
   ```bash
   docker compose logs -f <service>
   ```

2. Verify health check command:
   ```bash
   docker compose exec <service> <health-check-command>
   ```

3. Increase start period:
   ```yaml
   healthcheck:
     start_period: 60s
   ```

### Network Issues

1. Check network:
   ```bash
   docker network ls
   docker network inspect stealth-vpn
   ```

2. Verify connectivity:
   ```bash
   docker compose exec caddy ping xray
   ```

3. Recreate network:
   ```bash
   docker compose down
   docker network rm stealth-vpn
   docker compose up -d
   ```

### Volume Issues

1. Check volumes:
   ```bash
   docker volume ls
   docker volume inspect stealth-caddy-data
   ```

2. Verify permissions:
   ```bash
   ls -la data/stealth-vpn/
   ```

3. Recreate volumes:
   ```bash
   docker compose down -v
   docker compose up -d
   ```

## Best Practices

### Security

1. **Use secrets management** for sensitive data
2. **Limit container capabilities** to minimum required
3. **Enable read-only filesystems** where possible
4. **Regular security updates** for base images
5. **Monitor logs** for suspicious activity

### Performance

1. **Resource limits** to prevent resource exhaustion
2. **Log rotation** to manage disk space
3. **Health checks** to detect issues early
4. **Graceful shutdowns** to prevent data loss
5. **Regular backups** for disaster recovery

### Maintenance

1. **Regular updates** of Docker images
2. **Monitor disk usage** of volumes
3. **Review logs** periodically
4. **Test backups** regularly
5. **Document changes** to configuration

## References

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [Caddy Documentation](https://caddyserver.com/docs/)
- [Xray Documentation](https://xtls.github.io/)
- [WireGuard Documentation](https://www.wireguard.com/)
