# Deployment Checklist

This document provides a comprehensive checklist for deploying Stealth VPN Server to production.

## Migration from Existing Deployment

If you're upgrading an existing deployment, see the [Migration Guide](docs/MIGRATION_GUIDE.md) for detailed instructions on migrating to the new version with improved configurations.

## Pre-Deployment Checklist

### Server Requirements

#### Minimum Requirements (Minimal Mode)
- [ ] Ubuntu 20.04+ or Debian 11+ server
- [ ] **Minimum 1 CPU core** (single-core supported)
- [ ] **Minimum 1GB RAM** (2GB recommended)
- [ ] Minimum 10GB disk space
- [ ] Root or sudo access
- [ ] Static IP address

#### Recommended Requirements (Full Mode)
- [ ] Ubuntu 20.04+ or Debian 11+ server
- [ ] **Recommended 2+ CPU cores**
- [ ] **Recommended 2GB+ RAM**
- [ ] Minimum 20GB disk space
- [ ] Root or sudo access
- [ ] Static IP address

**Note:** Single-core servers are supported but should use **Minimal Mode** for initial deployment. See [Deployment Modes](docs/DEPLOYMENT_MODES.md) for details.

### Domain & DNS

- [ ] Domain name registered
- [ ] DNS A record pointing to server IP
- [ ] DNS propagation completed (check with `dig your-domain.com`)
- [ ] No conflicting DNS records (AAAA, CNAME)

### Network Requirements

- [ ] Port 80 open (for Let's Encrypt HTTP-01 challenge)
- [ ] Port 443 open (for HTTPS and VPN traffic)
- [ ] Port 443/UDP open (for HTTP/3 QUIC support)
- [ ] No other web server running on ports 80/443
- [ ] Firewall configured correctly

### Security Preparation

- [ ] SSH key-based authentication enabled
- [ ] Root login disabled
- [ ] Non-root user with sudo access created
- [ ] Fail2ban or similar intrusion prevention installed
- [ ] System packages updated (`apt update && apt upgrade`)

## Deployment Modes

The system supports two deployment modes:

### Minimal Mode (Recommended for First-Time Setup)
- Deploys only Caddy and Admin Panel
- Faster startup, easier troubleshooting
- Ideal for verifying SSL certificates and domain configuration
- **Best for single-core servers**
- Resource usage: ~0.5 CPU, ~512MB RAM

### Full Mode (Complete VPN Deployment)
- Deploys all services including VPN protocols
- Requires more resources
- Recommended after verifying minimal mode works
- **Requires 2+ CPU cores for optimal performance**
- Resource usage: ~2 CPU, ~2GB RAM

**Recommendation:** Always start with Minimal Mode, verify SSL and basic functionality, then transition to Full Mode. See [Deployment Modes Guide](docs/DEPLOYMENT_MODES.md) for detailed instructions.

## Installation Steps

### 1. Initial Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y git curl wget

# Clone repository
git clone https://github.com/yourusername/stealth-vpn-server.git
cd stealth-vpn-server
```

- [ ] System updated
- [ ] Repository cloned
- [ ] Working directory set

### 2. Run Installation Script

```bash
chmod +x install.sh
./install.sh
```

During installation, you will be prompted to:
- [ ] Select deployment mode (Minimal or Full)
- [ ] Enter domain name correctly
- [ ] Provide valid email address for SSL certificates
- [ ] Set strong admin password
- [ ] Confirm installation settings

**For first-time deployment:** Select **Minimal Mode (option 1)**

- [ ] Installation completed without errors

### 3. Verify Configuration

```bash
# Check .env file
cat .env

# Verify required variables
grep -E "DOMAIN|ADMIN_PASSWORD_HASH|SESSION_SECRET" .env
```

- [ ] `.env` file exists
- [ ] `DOMAIN` is set correctly
- [ ] `ADMIN_PASSWORD_HASH` is populated
- [ ] `SESSION_SECRET` is populated
- [ ] All ports are configured

### 4. Build and Start Services

#### For Minimal Mode:
```bash
# Build Docker images
docker compose -f docker-compose.minimal.yml build

# Start services
docker compose -f docker-compose.minimal.yml up -d

# Wait for services to be healthy
sleep 30

# Check status
docker compose -f docker-compose.minimal.yml ps
```

- [ ] Caddy and Admin images built successfully
- [ ] Services started
- [ ] Both services show as "healthy"
- [ ] No error messages in logs

#### For Full Mode:
```bash
# Build Docker images
docker compose build

# Start services
docker compose up -d

# Wait for services to be healthy (longer for full mode)
sleep 60

# Check status
docker compose ps
```

- [ ] All images built successfully
- [ ] All services started
- [ ] All services show as "healthy"
- [ ] No error messages in logs

### 5. Verify SSL Certificates

```bash
# Check Caddy logs for certificate acquisition
docker compose logs caddy | grep -i certificate

# Test HTTPS
curl -I https://your-domain.com
```

- [ ] SSL certificate obtained successfully
- [ ] HTTPS responds with 200 OK
- [ ] No certificate warnings
- [ ] HTTP redirects to HTTPS

## Transitioning from Minimal to Full Mode

After verifying that Minimal Mode works correctly (SSL certificates obtained, Admin Panel accessible), you can transition to Full Mode to enable all VPN protocols.

### Prerequisites

Before transitioning:
- [ ] Minimal mode is running successfully
- [ ] SSL certificates obtained (check Caddy logs)
- [ ] Admin Panel accessible at `https://your-domain.com/api/v2/storage/upload`
- [ ] No errors in logs
- [ ] Server has adequate resources (2+ CPU cores, 2GB+ RAM recommended)

### Transition Steps

```bash
# 1. Stop minimal services
docker compose -f docker-compose.minimal.yml down

# 2. Start full deployment
docker compose up -d

# 3. Wait for all services to be healthy
sleep 60

# 4. Verify all services are running
docker compose ps

# 5. Run health check
./scripts/health-check.sh
```

### Verification After Transition

- [ ] All 6 services running (Caddy, Admin, Xray, Trojan, Sing-box, WireGuard)
- [ ] All services show "healthy" status
- [ ] SSL certificates preserved (no re-acquisition needed)
- [ ] Admin Panel still accessible
- [ ] VPN configurations generated successfully

### Data Preservation

The following data is automatically preserved during transition:
- ✅ SSL certificates
- ✅ User accounts
- ✅ Configuration files
- ✅ Environment variables
- ✅ Docker volumes

**Note:** See [Deployment Modes Guide](docs/DEPLOYMENT_MODES.md) for detailed transition instructions and troubleshooting.

## Post-Deployment Verification

### Service Health Checks

```bash
# Run health check script
./scripts/health-check.sh

# Check individual services
docker compose ps
docker compose logs --tail=50 caddy
docker compose logs --tail=50 xray
docker compose logs --tail=50 trojan
docker compose logs --tail=50 singbox
docker compose logs --tail=50 wireguard
docker compose logs --tail=50 admin
```

- [ ] Health check script passes
- [ ] Caddy is running and healthy
- [ ] Xray is running and healthy
- [ ] Trojan is running and healthy
- [ ] Sing-box is running and healthy
- [ ] WireGuard is running and healthy
- [ ] Admin panel is running and healthy

### Admin Panel Access

```bash
# Test admin panel endpoint
curl -I https://your-domain.com/api/v2/storage/upload
```

- [ ] Admin panel accessible via HTTPS
- [ ] Login page loads correctly
- [ ] Can login with admin credentials
- [ ] Dashboard displays correctly

### Cover Website

```bash
# Test cover website
curl -I https://your-domain.com
```

- [ ] Main page loads correctly
- [ ] Looks like legitimate cloud storage service
- [ ] No VPN-related information visible
- [ ] All static assets load correctly

### VPN Service Testing

#### Test Xray Configuration

```bash
python3 scripts/xray-config-manager.py test
python3 scripts/xray-config-manager.py validate
```

- [ ] Xray configuration valid
- [ ] No syntax errors
- [ ] Service responds to test connections

#### Test Trojan Configuration

```bash
python3 scripts/trojan-config-manager.py test
python3 scripts/trojan-config-manager.py validate
```

- [ ] Trojan configuration valid
- [ ] No syntax errors
- [ ] Service responds to test connections

#### Test Sing-box Configuration

```bash
python3 scripts/singbox-config-manager.py test
python3 scripts/singbox-config-manager.py validate
```

- [ ] Sing-box configuration valid
- [ ] All protocols configured correctly
- [ ] Service responds to test connections

#### Test WireGuard Configuration

```bash
python3 scripts/wireguard-config-manager.py test
docker compose exec wireguard wg show
```

- [ ] WireGuard interface created
- [ ] Configuration valid
- [ ] Service responds to test connections

### Create Test User

```bash
# Add test user
python3 scripts/xray-config-manager.py add-user testuser

# Verify user created
python3 scripts/xray-config-manager.py list-users

# Generate client configs
ls -la data/stealth-vpn/configs/clients/testuser/
```

- [ ] Test user created successfully
- [ ] User appears in list
- [ ] Client configurations generated
- [ ] All protocol configs present

### Test VPN Connection

Using a VPN client:

- [ ] Xray XTLS-Vision connection works
- [ ] Xray WebSocket connection works
- [ ] Trojan connection works
- [ ] Sing-box ShadowTLS connection works
- [ ] Sing-box Hysteria2 connection works
- [ ] Sing-box TUIC connection works
- [ ] WireGuard WebSocket connection works
- [ ] Internet access works through VPN
- [ ] DNS resolution works
- [ ] No IP leaks (check with ipleak.net)

## Security Hardening

### Firewall Configuration

```bash
# Verify firewall rules
sudo ufw status

# Should show:
# 22/tcp (SSH)
# 80/tcp (HTTP)
# 443/tcp (HTTPS)
# 443/udp (QUIC)
```

- [ ] Firewall enabled
- [ ] Only necessary ports open
- [ ] SSH access restricted (if applicable)

### System Security

```bash
# Check for security updates
sudo apt update
sudo apt list --upgradable

# Install security updates
sudo apt upgrade -y
```

- [ ] All security updates installed
- [ ] Automatic security updates enabled
- [ ] System logs monitored

### Docker Security

```bash
# Check Docker security
docker compose config --quiet
docker ps --format "table {{.Names}}\t{{.Status}}"
```

- [ ] All containers running with security options
- [ ] No containers running as root (where applicable)
- [ ] Read-only filesystems where possible
- [ ] Resource limits configured

### Backup Configuration

```bash
# Create initial backup
./scripts/service-manager.sh backup

# Verify backup created
ls -lh backups/
```

- [ ] Backup created successfully
- [ ] Backup contains all necessary files
- [ ] Backup stored securely
- [ ] Backup schedule configured

## Monitoring Setup

### Log Rotation

```bash
# Check log configuration
docker compose config | grep -A 5 logging
```

- [ ] Log rotation configured
- [ ] Log size limits set
- [ ] Old logs cleaned up automatically

### Health Monitoring

```bash
# Set up cron job for health checks
crontab -e

# Add:
# */5 * * * * /path/to/stealth-vpn-server/scripts/health-check.sh >> /var/log/vpn-health.log 2>&1
```

- [ ] Health check cron job configured
- [ ] Health check logs reviewed
- [ ] Alerting configured (optional)

### Resource Monitoring

```bash
# Check resource usage
docker stats --no-stream
```

- [ ] CPU usage acceptable
- [ ] Memory usage acceptable
- [ ] Disk usage acceptable
- [ ] Network usage monitored

## Documentation

- [ ] Admin credentials documented securely
- [ ] Backup procedures documented
- [ ] Recovery procedures documented
- [ ] User onboarding guide created
- [ ] Troubleshooting guide accessible

## Final Checks

### Functionality

- [ ] All VPN protocols working
- [ ] Admin panel fully functional
- [ ] User management working
- [ ] Configuration generation working
- [ ] Backup/restore tested

### Performance

- [ ] Connection speed acceptable
- [ ] Latency acceptable
- [ ] Multiple concurrent connections work
- [ ] No resource bottlenecks

### Security

- [ ] SSL/TLS configured correctly
- [ ] No sensitive information exposed
- [ ] Logs don't contain sensitive data
- [ ] Admin panel access restricted
- [ ] VPN traffic properly obfuscated

### Maintenance

- [ ] Update procedure documented
- [ ] Rollback procedure tested
- [ ] Backup schedule configured
- [ ] Monitoring in place
- [ ] Support contacts documented

## Post-Deployment Tasks

### Day 1

- [ ] Monitor logs for errors
- [ ] Test all VPN protocols
- [ ] Verify SSL certificate renewal
- [ ] Check resource usage
- [ ] Create first backup

### Week 1

- [ ] Review logs daily
- [ ] Monitor connection stability
- [ ] Test backup restoration
- [ ] Verify health checks
- [ ] Document any issues

### Month 1

- [ ] Review security logs
- [ ] Update system packages
- [ ] Test disaster recovery
- [ ] Optimize performance
- [ ] Plan capacity upgrades

## Rollback Plan

If deployment fails:

1. **Stop services**
   ```bash
   docker compose down
   ```

2. **Restore from backup**
   ```bash
   ./scripts/update-system.sh rollback
   ```

3. **Verify restoration**
   ```bash
   docker compose ps
   ./scripts/health-check.sh
   ```

4. **Document issues**
   - Save error logs
   - Note what went wrong
   - Plan fixes

## Support Resources

- **Troubleshooting Guide**: `TROUBLESHOOTING.md` - Common errors and solutions
- **Deployment Modes**: `docs/DEPLOYMENT_MODES.md` - Minimal vs Full mode details
- **Docker Orchestration**: `docs/DOCKER_ORCHESTRATION.md` - Container management
- **Quick Start**: `QUICKSTART.md`
- **Health Checks**: `./scripts/health-check.sh`
- **Service Manager**: `./scripts/service-manager.sh`
- **Logs**: `docker compose logs -f`

## Emergency Contacts

Document your emergency contacts:

- [ ] System administrator
- [ ] Network administrator
- [ ] DNS provider support
- [ ] Hosting provider support
- [ ] Backup administrator

## Sign-Off

Deployment completed by: ___________________

Date: ___________________

Verified by: ___________________

Date: ___________________

Notes:
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________
