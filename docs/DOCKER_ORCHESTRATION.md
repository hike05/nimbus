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

**Named Volume Behavior:**
- Persist data across container restarts
- Survive `docker compose down` (unless `-v` flag used)
- Managed by Docker (stored in `/var/lib/docker/volumes/`)
- Can be backed up with `docker volume` commands

#### Bind Mounts

Shared configuration and data directories:

- `./data/stealth-vpn/configs`: VPN configurations
- `./data/stealth-vpn/logs`: Service logs
- `./data/caddy/certificates`: SSL certificates
- `./data/www`: Cover website files
- `./core`: Shared Python modules

**Bind Mount Behavior:**

1. **Read-Write Mounts (`:rw` or default)**
   ```yaml
   volumes:
     - ./data/stealth-vpn/configs:/data/configs:rw
   ```
   - Container can read and write files
   - Changes persist on host filesystem
   - Used for configs, logs, and data that needs modification

2. **Read-Only Mounts (`:ro`)**
   ```yaml
   volumes:
     - ./core:/app/core:ro
   ```
   - Container can only read files
   - Prevents accidental modification
   - Used for shared code and static resources

**Volume Mount Conflicts:**

Conflicts occur when:
- Multiple containers mount the same path with different permissions
- File ownership doesn't match container user
- Host directory doesn't exist

**Solutions:**
```bash
# Create directories with correct permissions
mkdir -p data/stealth-vpn/{configs,logs,backups}
chmod -R 755 data/

# Fix ownership issues
sudo chown -R $USER:$USER data/

# Check mount points
docker compose config | grep -A 5 volumes
```

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

### Resource Limits

Resource limits prevent services from consuming excessive CPU or memory.

#### Standard Resource Limits (Full Mode)

```yaml
deploy:
  resources:
    limits:
      cpus: '1.0'      # Maximum 1 CPU core
      memory: 512M     # Maximum 512MB RAM
    reservations:
      cpus: '0.25'     # Minimum 0.25 CPU core
      memory: 128M     # Minimum 128MB RAM
```

#### Adjusted Limits for Single-Core Servers

For servers with only 1 CPU core, limits are automatically adjusted:

```yaml
deploy:
  resources:
    limits:
      cpus: '0.5'      # Reduced to 0.5 CPU core
      memory: 256M     # Reduced to 256MB RAM
    reservations:
      cpus: '0.1'      # Reduced to 0.1 CPU core
      memory: 64M      # Reduced to 64MB RAM
```

**Why Adjust for Single-Core?**
- Prevents resource contention between services
- Allows all services to run simultaneously
- Reduces risk of OOM (Out of Memory) kills
- Improves stability on constrained hardware

**Monitoring Resource Usage:**

```bash
# Real-time resource monitoring
docker stats

# Check if limits are being hit
docker stats --no-stream | awk '{print $1, $3, $7}'

# View container resource configuration
docker inspect stealth-xray | jq '.[0].HostConfig.Memory'
```

**Signs of Resource Constraints:**
- Services frequently restarting
- Health checks timing out
- Slow response times
- OOM killer messages in logs: `docker compose logs | grep -i "killed"`

**Solutions:**
1. Use Minimal Mode (Caddy + Admin only)
2. Increase server resources
3. Adjust resource limits in docker-compose.yml
4. Enable swap space

### Logging Configuration

All services use JSON file logging with rotation:

- **Max Size**: 10MB per file
- **Max Files**: 3 files retained
- **Total Storage**: ~30MB per service

Logs are also available via bind mounts in `./data/stealth-vpn/logs/`.

**Log Driver Configuration:**

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

**Accessing Logs:**

```bash
# Via Docker Compose
docker compose logs -f xray

# Via bind mount
tail -f data/stealth-vpn/logs/xray/xray.log

# Via Docker directly
docker logs -f stealth-xray
```

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

## Troubleshooting Docker-Specific Issues

### Services Won't Start

**Symptoms:**
- Containers exit immediately after starting
- Services stuck in "starting" state
- "Exited (1)" status

**Diagnostics:**
```bash
# Check service status
docker compose ps

# View logs
docker compose logs -f

# Verify configuration
docker compose config

# Check for errors
docker compose logs | grep -i error
```

**Common Causes & Solutions:**

1. **Configuration errors:**
   ```bash
   # Validate docker-compose.yml
   docker compose config --quiet
   
   # Check for syntax errors
   yamllint docker-compose.yml
   ```

2. **Missing dependencies:**
   ```bash
   # Check if required images exist
   docker images | grep stealth
   
   # Rebuild if needed
   docker compose build
   ```

3. **Port conflicts:**
   ```bash
   # Check what's using ports
   sudo netstat -tulpn | grep -E ':80|:443'
   
   # Stop conflicting services
   sudo systemctl stop nginx apache2
   ```

### Health Checks Failing

**Symptoms:**
- Services show "unhealthy" status
- Containers restart repeatedly
- Health check timeout errors

**Diagnostics:**
```bash
# Check health status
docker compose ps

# View health check logs
docker inspect stealth-xray | jq '.[0].State.Health'

# Test health check manually
docker compose exec xray pgrep xray
```

**Solutions:**

1. **Increase timeouts for slow servers:**
   ```yaml
   healthcheck:
     interval: 60s        # Increase from 30s
     timeout: 20s         # Increase from 10s
     start_period: 120s   # Increase from 40s
     retries: 5           # Increase from 3
   ```

2. **Check if service is actually running:**
   ```bash
   docker compose exec xray ps aux
   ```

3. **Verify health check command works:**
   ```bash
   docker compose exec caddy wget -O- http://localhost:2019/config/
   ```

### Network Issues

**Symptoms:**
- Services can't communicate
- "Connection refused" errors
- DNS resolution failures

**Diagnostics:**
```bash
# Check network exists
docker network ls | grep stealth-vpn

# Inspect network
docker network inspect stealth-vpn

# Check container connectivity
docker compose exec caddy ping admin
docker compose exec caddy nslookup xray
```

**Solutions:**

1. **Recreate network:**
   ```bash
   docker compose down
   docker network rm stealth-vpn
   docker compose up -d
   ```

2. **Verify network configuration:**
   ```bash
   docker compose config | grep -A 10 networks
   ```

3. **Check firewall rules:**
   ```bash
   sudo iptables -L -n | grep docker
   ```

### Volume Mount Issues

**Symptoms:**
- "Permission denied" errors
- "Read-only file system" errors
- Data not persisting

**Diagnostics:**
```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect stealth-caddy-data

# Check mount points
docker inspect stealth-admin | jq '.[0].Mounts'

# Verify host directory permissions
ls -la data/stealth-vpn/
```

**Solutions:**

1. **Fix permissions:**
   ```bash
   sudo chown -R $USER:$USER data/
   chmod -R 755 data/
   ```

2. **Verify mount syntax:**
   ```yaml
   volumes:
     - ./data/configs:/data/configs:rw  # Correct
     # Not: ./data/configs:/data/configs:ro (if writing needed)
   ```

3. **Recreate volumes:**
   ```bash
   docker compose down -v
   docker compose up -d
   ```

4. **Check for conflicts:**
   ```bash
   # Ensure no other containers use same volumes
   docker ps -a --filter volume=stealth-caddy-data
   ```

### Resource Exhaustion

**Symptoms:**
- "Out of memory" errors
- Containers killed by OOM
- Slow performance
- Services timing out

**Diagnostics:**
```bash
# Check resource usage
docker stats --no-stream

# Check system resources
free -h
df -h

# View OOM kills
dmesg | grep -i "out of memory"
docker compose logs | grep -i "killed"
```

**Solutions:**

1. **Use Minimal Mode:**
   ```bash
   docker compose -f docker-compose.minimal.yml up -d
   ```

2. **Reduce resource limits:**
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '0.5'
         memory: 256M
   ```

3. **Enable swap:**
   ```bash
   sudo fallocate -l 2G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   
   # Make permanent
   echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
   ```

4. **Clean up Docker resources:**
   ```bash
   docker system prune -a
   docker volume prune
   ```

### Port Conflicts

**Symptoms:**
- "Address already in use" errors
- Services fail to bind to ports
- Cannot start Caddy

**Diagnostics:**
```bash
# Check what's using ports
sudo netstat -tulpn | grep -E ':80|:443|:8001|:8002'
sudo lsof -i :443

# Check Docker port mappings
docker compose ps
docker port stealth-caddy
```

**Solutions:**

1. **Stop conflicting services:**
   ```bash
   sudo systemctl stop nginx apache2
   sudo systemctl disable nginx apache2
   ```

2. **Change ports in docker-compose.yml:**
   ```yaml
   ports:
     - "8080:80"    # Use alternative port
     - "8443:443"
   ```

3. **Kill process using port:**
   ```bash
   sudo kill $(sudo lsof -t -i:443)
   ```

### Build Failures

**Symptoms:**
- "failed to solve" errors
- "no space left on device"
- Build context too large

**Diagnostics:**
```bash
# Check disk space
df -h

# Check Docker disk usage
docker system df

# View build logs
docker compose build --progress=plain
```

**Solutions:**

1. **Clean up Docker:**
   ```bash
   docker system prune -a
   docker builder prune -a
   ```

2. **Build with no cache:**
   ```bash
   docker compose build --no-cache
   ```

3. **Build services individually:**
   ```bash
   docker compose build caddy
   docker compose build admin
   ```

4. **Check .dockerignore:**
   ```bash
   cat .dockerignore
   # Should exclude: node_modules, .git, data/, etc.
   ```

### Container Restart Loops

**Symptoms:**
- Container constantly restarting
- "Restarting (1)" status
- Logs show repeated startup attempts

**Diagnostics:**
```bash
# Check restart count
docker compose ps

# View logs for errors
docker compose logs --tail=100 xray

# Check exit code
docker inspect stealth-xray | jq '.[0].State.ExitCode'
```

**Solutions:**

1. **Check for configuration errors:**
   ```bash
   python3 scripts/xray-config-manager.py validate
   ```

2. **Disable restart policy temporarily:**
   ```yaml
   restart: "no"  # Instead of "unless-stopped"
   ```

3. **Increase resource limits:**
   ```yaml
   deploy:
     resources:
       limits:
         memory: 1G  # Increase if OOM
   ```

4. **Check dependencies:**
   ```yaml
   depends_on:
     admin:
       condition: service_healthy  # Ensure deps are healthy
   ```

## Docker-Specific Best Practices

### Volume Management

1. **Use named volumes for data:**
   ```yaml
   volumes:
     stealth-caddy-data:
       driver: local
   ```

2. **Use bind mounts for configs:**
   ```yaml
   volumes:
     - ./config/Caddyfile:/etc/caddy/Caddyfile:ro
   ```

3. **Regular backups:**
   ```bash
   docker run --rm -v stealth-caddy-data:/data -v $(pwd):/backup \
     alpine tar czf /backup/caddy-data.tar.gz /data
   ```

### Network Security

1. **Use internal networks:**
   ```yaml
   networks:
     stealth-vpn:
       internal: false  # Only Caddy needs external access
   ```

2. **Limit exposed ports:**
   ```yaml
   ports:
     - "443:443"  # Only expose necessary ports
   ```

3. **Use network aliases:**
   ```yaml
   networks:
     stealth-vpn:
       aliases:
         - xray-service
   ```

### Resource Management

1. **Set appropriate limits:**
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '1.0'
         memory: 512M
   ```

2. **Monitor usage:**
   ```bash
   docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
   ```

3. **Use health checks:**
   ```yaml
   healthcheck:
     test: ["CMD", "pgrep", "xray"]
     interval: 30s
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
