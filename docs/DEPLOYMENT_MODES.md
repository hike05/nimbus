# Deployment Modes

The Stealth VPN Server supports two deployment modes to provide flexibility during initial setup and troubleshooting.

## Deployment Modes Overview

### 1. Minimal Mode (Recommended for First-Time Setup)

**Services Included:**
- Caddy (reverse proxy with automatic HTTPS)
- Admin Panel (web interface for management)

**Benefits:**
- Faster startup time
- Lower resource requirements
- Easier troubleshooting
- Verify SSL certificates and basic functionality first
- No VPN service dependencies

**Use Cases:**
- First-time deployment
- Testing SSL certificate acquisition
- Verifying domain configuration
- Troubleshooting Caddy or Admin Panel issues
- Low-resource servers (1 CPU core, 1GB RAM)

**Resource Requirements:**
- CPU: 0.5-1.0 cores
- Memory: 512MB
- Disk: 1GB

### 2. Full Mode (Complete VPN Deployment)

**Services Included:**
- Caddy (reverse proxy with automatic HTTPS)
- Admin Panel (web interface for management)
- Xray (VLESS with XTLS-Vision and WebSocket)
- Trojan-Go (Trojan protocol)
- Sing-box (ShadowTLS v3, Hysteria2, TUIC v5)
- WireGuard (with obfuscation support)

**Benefits:**
- All VPN protocols available immediately
- Complete functionality
- Production-ready deployment

**Use Cases:**
- Production deployment after verifying minimal mode
- Servers with adequate resources
- When all VPN protocols are needed

**Resource Requirements:**
- CPU: 2+ cores (recommended)
- Memory: 2GB+ (recommended)
- Disk: 5GB+

## Selecting Deployment Mode During Installation

During the installation process, you'll be prompted to select a deployment mode:

```bash
./install.sh
```

The installer will display:

```
╔════════════════════════════════════════════════════════════╗
║              Deployment Mode Selection                     ║
╚════════════════════════════════════════════════════════════╝

1. Minimal Mode (Recommended for first-time setup)
   • Deploys only Caddy and Admin Panel
   • Faster startup and easier troubleshooting
   • Verify SSL and basic functionality first
   • Add VPN services later through admin panel

2. Full Mode (Complete VPN deployment)
   • Deploys all services: Caddy, Admin Panel, and all VPN protocols
   • Xray, Trojan-Go, Sing-box, and WireGuard
   • Requires more resources and longer startup time
   • Recommended after verifying minimal mode works

Select deployment mode (1 for Minimal, 2 for Full) [1]:
```

## Transitioning from Minimal to Full Mode

After verifying that Caddy and the Admin Panel work correctly in minimal mode, you can transition to full mode without losing any data.

### Step-by-Step Transition Process

#### 1. Verify Minimal Mode is Working

Before transitioning, ensure:
- SSL certificates are obtained successfully
- Admin Panel is accessible at `https://your-domain.com/api/v2/storage/upload`
- No errors in Caddy or Admin Panel logs

Check service status:
```bash
docker compose -f docker-compose.minimal.yml ps
docker compose -f docker-compose.minimal.yml logs -f
```

#### 2. Stop Minimal Services

Stop the minimal deployment:
```bash
docker compose -f docker-compose.minimal.yml down
```

**Note:** This command stops containers but preserves all data:
- SSL certificates in `/data/caddy/certificates/`
- User data in `/data/stealth-vpn/`
- Configuration files
- Docker volumes

#### 3. Start Full Deployment

Start all services including VPN protocols:
```bash
docker compose -f docker-compose.yml up -d
```

This will:
- Reuse existing SSL certificates
- Preserve all user data and configurations
- Start VPN service containers
- Connect all services to the same network

#### 4. Verify All Services are Running

Check that all services are healthy:
```bash
docker compose -f docker-compose.yml ps
```

Expected output:
```
NAME                IMAGE                    STATUS
stealth-admin       stealth-admin:latest     Up (healthy)
stealth-caddy       caddy:2-alpine           Up (healthy)
stealth-singbox     stealth-singbox:latest   Up (healthy)
stealth-trojan      stealth-trojan:latest    Up (healthy)
stealth-wireguard   stealth-wireguard:latest Up (healthy)
stealth-xray        stealth-xray:latest      Up (healthy)
```

Run the health check script:
```bash
./scripts/health-check.sh
```

#### 5. Verify VPN Connectivity

Test each VPN protocol:
```bash
# Test Xray integration
python3 scripts/test-xray-integration.py

# Test Trojan integration
python3 scripts/test-trojan-integration.py

# Test Sing-box integration
python3 scripts/test-singbox-integration.py

# Test WireGuard integration
python3 scripts/test-wireguard-integration.py
```

## Data Preservation During Transition

The following data is preserved when transitioning between modes:

### Preserved Data
- ✅ SSL certificates (`/data/caddy/certificates/`)
- ✅ User accounts (`/data/stealth-vpn/configs/users.json`)
- ✅ VPN configurations (`/data/stealth-vpn/configs/`)
- ✅ Client configurations (`/data/stealth-vpn/configs/clients/`)
- ✅ Backups (`/data/stealth-vpn/backups/`)
- ✅ Logs (`/data/stealth-vpn/logs/`)
- ✅ Docker volumes (caddy_data, admin_data, etc.)
- ✅ Environment variables (`.env` file)

### Not Preserved
- ❌ Container state (containers are recreated)
- ❌ Active connections (users will need to reconnect)
- ❌ In-memory data (session tokens, temporary files)

## Reverting from Full to Minimal Mode

If you need to revert to minimal mode (e.g., for troubleshooting):

```bash
# Stop full deployment
docker compose -f docker-compose.yml down

# Start minimal deployment
docker compose -f docker-compose.minimal.yml up -d
```

All data remains preserved during this process as well.

## Caddyfile Configuration Examples

Both deployment modes use the same Caddyfile with correct Caddy v2 syntax. Here are working examples:

### Global Configuration Block

The global block configures server-wide settings:

```caddyfile
{
    # Email for Let's Encrypt notifications
    email your-email@example.com
    
    # Server configuration
    servers {
        # Enable HTTP/1.1, HTTP/2, and HTTP/3 protocols
        protocols h1 h2 h3
    }
}
```

**Explanation:**
- `email`: Required for SSL certificate notifications
- `servers`: Global server configuration block
- `protocols h1 h2 h3`: Enables HTTP/1.1, HTTP/2, and HTTP/3 (QUIC)

### Minimal Mode Caddyfile

```caddyfile
{
    email your-email@example.com
    
    servers {
        protocols h1 h2 h3
    }
}

your-domain.com {
    # Rate limiting for admin panel
    rate_limit {
        zone admin {
            key {remote_host}
            events 5
            window 1m
        }
    }
    
    # Admin panel endpoint (obfuscated)
    reverse_proxy /api/v2/storage/* admin:8010
    
    # Cover website (root and other paths)
    root * /var/www/html
    file_server
    
    # Enable compression
    encode gzip
    
    # Security headers
    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
        Referrer-Policy "no-referrer"
    }
}
```

### Full Mode Caddyfile

```caddyfile
{
    email your-email@example.com
    
    servers {
        protocols h1 h2 h3
    }
}

your-domain.com {
    # Rate limiting zones
    rate_limit {
        zone admin {
            key {remote_host}
            events 5
            window 1m
        }
        zone vpn {
            key {remote_host}
            events 1000
            window 1m
        }
    }
    
    # Admin panel endpoint (obfuscated)
    rate_limit admin
    reverse_proxy /api/v2/storage/* admin:8010
    
    # Xray VLESS endpoints (obfuscated)
    rate_limit vpn
    reverse_proxy /api/v1/analytics/* xray:8001 {
        transport http {
            versions h2c
        }
    }
    
    reverse_proxy /cdn/assets/* xray:8004 {
        transport http {
            versions 1.1
        }
    }
    
    # Trojan endpoint (obfuscated)
    rate_limit vpn
    reverse_proxy /api/v1/metrics/* trojan:8002
    
    # Sing-box endpoints (obfuscated)
    rate_limit vpn
    reverse_proxy /api/v1/telemetry/* singbox:8003
    reverse_proxy /cdn/media/* singbox:8005
    reverse_proxy /api/v1/logs/* singbox:8006
    
    # WireGuard WebSocket endpoint (obfuscated)
    rate_limit vpn
    reverse_proxy /api/v1/sync/* wireguard:8006
    
    # Cover website (root and other paths)
    root * /var/www/html
    file_server
    
    # Enable compression
    encode gzip
    
    # Security headers
    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
        Referrer-Policy "no-referrer"
    }
}
```

### Directive Explanations

#### `rate_limit` Directive

```caddyfile
rate_limit {
    zone admin {
        key {remote_host}    # Rate limit by client IP
        events 5             # Maximum 5 requests
        window 1m            # Per 1 minute window
    }
}
```

- `zone`: Named rate limit zone
- `key {remote_host}`: Use client IP as the key
- `events`: Maximum number of requests allowed
- `window`: Time window for the limit

#### `reverse_proxy` Directive

```caddyfile
reverse_proxy /api/v2/storage/* admin:8010
```

- `/api/v2/storage/*`: Path matcher (wildcard)
- `admin:8010`: Backend service (Docker service name and port)

#### `reverse_proxy` with Transport Options

```caddyfile
reverse_proxy /api/v1/analytics/* xray:8001 {
    transport http {
        versions h2c    # Use HTTP/2 Cleartext
    }
}
```

- `transport http`: Configure HTTP transport
- `versions h2c`: Use HTTP/2 without TLS (for internal communication)
- `versions 1.1`: Use HTTP/1.1

#### HTTP/3 Configuration

HTTP/3 is enabled globally in the `servers` block:

```caddyfile
{
    servers {
        protocols h1 h2 h3    # h3 enables HTTP/3 (QUIC)
    }
}
```

**Requirements for HTTP/3:**
- Port 443/UDP must be open
- Caddy automatically handles QUIC protocol
- Clients must support HTTP/3

**Testing HTTP/3:**
```bash
# Check if HTTP/3 is advertised
curl -I https://your-domain.com | grep -i alt-svc

# Expected output:
# alt-svc: h3=":443"; ma=2592000
```

## Service Management Commands

### Minimal Mode

```bash
# Start services
docker compose -f docker-compose.minimal.yml up -d

# Stop services
docker compose -f docker-compose.minimal.yml down

# View logs
docker compose -f docker-compose.minimal.yml logs -f

# Restart a service
docker compose -f docker-compose.minimal.yml restart caddy

# Check status
docker compose -f docker-compose.minimal.yml ps
```

### Full Mode

```bash
# Start services
docker compose -f docker-compose.yml up -d

# Stop services
docker compose -f docker-compose.yml down

# View logs
docker compose -f docker-compose.yml logs -f

# Restart a service
docker compose -f docker-compose.yml restart xray

# Check status
docker compose -f docker-compose.yml ps
```

## Troubleshooting

### Minimal Mode Issues

**Problem:** Caddy fails to obtain SSL certificate

**Solution:**
1. Verify DNS points to server IP: `dig your-domain.com`
2. Check ports 80 and 443 are accessible
3. Review Caddy logs: `docker compose -f docker-compose.minimal.yml logs caddy`
4. Verify domain in `.env` file is correct

**Problem:** Admin Panel not accessible

**Solution:**
1. Check admin container is healthy: `docker compose -f docker-compose.minimal.yml ps`
2. Review admin logs: `docker compose -f docker-compose.minimal.yml logs admin`
3. Verify `ADMIN_PASSWORD_HASH` is set in `.env`
4. Check file permissions: `ls -la data/stealth-vpn/`

### Full Mode Issues

**Problem:** VPN services fail to start

**Solution:**
1. Check if configuration files exist: `ls -la data/stealth-vpn/configs/`
2. Verify VPN configs are valid JSON
3. Review service logs: `docker compose -f docker-compose.yml logs <service>`
4. Ensure sufficient resources (CPU/memory)

**Problem:** Services stuck in "starting" state

**Solution:**
1. Increase health check `start_period` in docker-compose.yml
2. Check resource limits aren't too restrictive
3. Review system resources: `docker stats`
4. Check for port conflicts: `netstat -tulpn`

## Best Practices

1. **Always start with minimal mode** for first-time deployments
2. **Verify SSL certificates** work before adding VPN services
3. **Test admin panel** functionality in minimal mode
4. **Monitor resource usage** before transitioning to full mode
5. **Create backups** before major changes
6. **Review logs** after transitioning between modes
7. **Test VPN connectivity** after enabling full mode
8. **Document any custom changes** to configuration files

## Additional Resources

- [Deployment Guide](../DEPLOYMENT.md)
- [Admin Panel Usage](ADMIN_PANEL_USAGE.md)
- [Troubleshooting Guide](../DEPLOYMENT.md#troubleshooting)
- [Docker Orchestration](DOCKER_ORCHESTRATION.md)
