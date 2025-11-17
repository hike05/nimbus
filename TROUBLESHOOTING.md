# Troubleshooting Guide

This guide helps you diagnose and resolve common deployment and operational issues with Stealth VPN Server.

## Quick Diagnostics

Run these commands first to gather information:

```bash
# Check service status
docker compose ps

# View recent logs
docker compose logs --tail=50

# Run health check
./scripts/health-check.sh

# Check system resources
docker stats --no-stream
```

## Common Deployment Errors

### 1. Caddy SSL Certificate Validation Errors

#### Error: "acme: error: 400"

**Symptoms:**
```
caddy | {"level":"error","msg":"could not get certificate from issuer"}
caddy | {"level":"error","msg":"acme: error: 400"}
```

**Causes:**
- Domain DNS not pointing to server IP
- Ports 80 or 443 blocked by firewall
- Another service using port 80/443
- Domain validation failed

**Solutions:**

1. Verify DNS configuration:
```bash
dig +short your-domain.com
# Should return your server's IP address
```

2. Check port availability:
```bash
sudo netstat -tulpn | grep -E ':80|:443'
# Should show nothing or only Caddy
```

3. Test port accessibility from external:
```bash
curl -I http://your-domain.com
# Should connect (even if returns error page)
```

4. Check firewall rules:
```bash
sudo ufw status
# Should show 80/tcp and 443/tcp ALLOW
```

5. Stop conflicting services:
```bash
sudo systemctl stop nginx apache2
sudo systemctl disable nginx apache2
```

6. Restart Caddy:
```bash
docker compose restart caddy
docker compose logs -f caddy
```

#### Error: "Caddyfile validation failed"

**Symptoms:**
```
Error: adapting config using caddyfile: Caddyfile:X - Error during parsing
```

**Causes:**
- Invalid Caddy v2 syntax in Caddyfile
- Missing or incorrect directives
- Syntax errors (missing braces, semicolons)

**Solutions:**

1. Validate Caddyfile syntax:
```bash
docker compose exec caddy caddy validate --config /etc/caddy/Caddyfile
```

2. Check for common syntax errors:
   - Ensure `protocols` directive is inside `servers` block
   - Use `rate_limit` instead of deprecated `limits`
   - Check all braces are balanced `{}`
   - Verify reverse_proxy syntax

3. Review Caddyfile format (correct v2 syntax):
```caddyfile
{
    servers {
        protocols h1 h2 h3
    }
}

your-domain.com {
    rate_limit {
        zone static {
            key {remote_host}
            events 100
            window 1m
        }
    }
    
    reverse_proxy /api/v2/storage/* admin:8010
}
```

4. Test with minimal Caddyfile:
```bash
# Backup current Caddyfile
cp config/Caddyfile config/Caddyfile.backup

# Create minimal test version
cat > config/Caddyfile << 'EOF'
{
    email your-email@example.com
}

your-domain.com {
    respond "OK" 200
}
EOF

# Restart and test
docker compose restart caddy
```

### 2. Docker Build Failures

#### Error: "failed to solve with frontend dockerfile.v0"

**Symptoms:**
```
ERROR: failed to solve: failed to compute cache key
```

**Causes:**
- Missing Dockerfile
- Invalid Dockerfile syntax
- Network issues during build
- Insufficient disk space

**Solutions:**

1. Check disk space:
```bash
df -h
# Ensure at least 5GB free
```

2. Clean Docker cache:
```bash
docker system prune -a
docker builder prune -a
```

3. Rebuild with no cache:
```bash
docker compose build --no-cache
```

4. Build services individually:
```bash
docker compose build caddy
docker compose build admin
docker compose build xray
```

5. Check Dockerfile exists:
```bash
ls -la */Dockerfile
```

#### Error: "Cannot connect to Docker daemon"

**Symptoms:**
```
Cannot connect to the Docker daemon at unix:///var/run/docker.sock
```

**Solutions:**

1. Start Docker service:
```bash
sudo systemctl start docker
sudo systemctl enable docker
```

2. Add user to docker group:
```bash
sudo usermod -aG docker $USER
newgrp docker
```

3. Check Docker status:
```bash
sudo systemctl status docker
```

### 3. Permission Issues

#### Error: "Permission denied" on data directories

**Symptoms:**
```
admin | PermissionError: [Errno 13] Permission denied: '/data/configs/users.json'
```

**Solutions:**

1. Fix directory permissions:
```bash
sudo chown -R $USER:$USER data/
chmod -R 755 data/
```

2. Fix specific file permissions:
```bash
chmod 644 data/stealth-vpn/configs/users.json
chmod 644 .env
```

3. Recreate directories with correct permissions:
```bash
./install.sh
# Select option to recreate directories
```

#### Error: "Read-only file system"

**Symptoms:**
```
OSError: [Errno 30] Read-only file system
```

**Solutions:**

1. Check volume mounts in docker-compose.yml:
```yaml
volumes:
  - ./data/stealth-vpn/configs:/data/configs:rw  # Add :rw
```

2. Remove read-only flag if present:
```yaml
# Remove or comment out:
# read_only: true
```

3. Restart containers:
```bash
docker compose down
docker compose up -d
```

### 4. Resource Constraint Issues (Single-Core Servers)

#### Error: Services fail to start or timeout

**Symptoms:**
```
Container stealth-xray is unhealthy
Health check timeout
```

**Causes:**
- Insufficient CPU resources
- Too many services starting simultaneously
- Resource limits too restrictive

**Solutions:**

1. Use minimal deployment mode:
```bash
docker compose -f docker-compose.minimal.yml up -d
```

2. Increase health check timeouts:
```yaml
healthcheck:
  start_period: 120s  # Increase from 40s
  interval: 60s       # Increase from 30s
```

3. Adjust resource limits for single-core:
```yaml
deploy:
  resources:
    limits:
      cpus: '0.5'     # Reduce from 1.0
      memory: 256M    # Reduce from 512M
```

4. Start services sequentially:
```bash
docker compose up -d caddy
sleep 30
docker compose up -d admin
sleep 30
docker compose up -d xray
```

5. Monitor resource usage:
```bash
docker stats
htop
```

#### Error: "Out of memory" or OOM killed

**Symptoms:**
```
Container killed by OOM killer
```

**Solutions:**

1. Check available memory:
```bash
free -h
```

2. Reduce memory limits:
```yaml
deploy:
  resources:
    limits:
      memory: 256M  # Reduce limits
```

3. Enable swap:
```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

4. Use minimal mode with fewer services

## Service-Specific Issues

### Xray Issues

#### Error: "Failed to start Xray"

**Diagnostics:**
```bash
docker compose logs xray
python3 scripts/xray-config-manager.py validate
```

**Solutions:**

1. Validate configuration:
```bash
python3 scripts/xray-config-manager.py test
```

2. Check config file syntax:
```bash
cat data/stealth-vpn/configs/xray.json | jq .
```

3. Regenerate configuration:
```bash
python3 scripts/xray-config-manager.py generate
docker compose restart xray
```

### Trojan Issues

#### Error: "Trojan-Go failed to start"

**Diagnostics:**
```bash
docker compose logs trojan
python3 scripts/trojan-config-manager.py validate
```

**Solutions:**

1. Test configuration:
```bash
python3 scripts/trojan-config-manager.py test
```

2. Check certificate paths:
```bash
ls -la data/caddy/certificates/
```

3. Regenerate configuration:
```bash
python3 scripts/trojan-config-manager.py generate
docker compose restart trojan
```

### Sing-box Issues

#### Error: "Sing-box configuration invalid"

**Diagnostics:**
```bash
docker compose logs singbox
python3 scripts/singbox-config-manager.py validate
```

**Solutions:**

1. Validate configuration:
```bash
python3 scripts/singbox-config-manager.py test
```

2. Check for syntax errors:
```bash
cat data/stealth-vpn/configs/singbox.json | jq .
```

3. Regenerate configuration:
```bash
python3 scripts/singbox-config-manager.py generate
docker compose restart singbox
```

### Admin Panel Issues

#### Error: "Admin panel not accessible"

**Diagnostics:**
```bash
docker compose logs admin
curl -I http://localhost:8010/health
```

**Solutions:**

1. Check admin container health:
```bash
docker compose ps admin
```

2. Verify environment variables:
```bash
grep ADMIN .env
```

3. Check Flask logs:
```bash
docker compose logs -f admin
```

4. Test internal connectivity:
```bash
docker compose exec caddy wget -O- http://admin:8010/health
```

5. Restart admin service:
```bash
docker compose restart admin
```

## Network Issues

### Port Conflicts

**Error:** "Port already in use"

**Diagnostics:**
```bash
sudo netstat -tulpn | grep -E ':80|:443|:8001|:8002'
```

**Solutions:**

1. Identify conflicting process:
```bash
sudo lsof -i :443
```

2. Stop conflicting service:
```bash
sudo systemctl stop nginx
sudo systemctl stop apache2
```

3. Change port in docker-compose.yml (if needed):
```yaml
ports:
  - "8443:443"  # Use alternative port
```

### DNS Resolution Issues

**Error:** "Cannot resolve domain"

**Diagnostics:**
```bash
dig your-domain.com
nslookup your-domain.com
```

**Solutions:**

1. Wait for DNS propagation (up to 48 hours)

2. Check DNS records:
```bash
dig +trace your-domain.com
```

3. Verify A record points to correct IP:
```bash
dig +short your-domain.com
curl ifconfig.me  # Compare IPs
```

4. Clear DNS cache:
```bash
sudo systemd-resolve --flush-caches
```

## Configuration Issues

### Invalid JSON Configuration

**Error:** "JSON decode error"

**Diagnostics:**
```bash
cat data/stealth-vpn/configs/xray.json | jq .
```

**Solutions:**

1. Validate JSON syntax:
```bash
jq . data/stealth-vpn/configs/xray.json
```

2. Fix common JSON errors:
   - Missing commas
   - Trailing commas
   - Unescaped quotes
   - Missing brackets

3. Regenerate from template:
```bash
python3 scripts/xray-config-manager.py generate
```

### Environment Variable Issues

**Error:** "Environment variable not set"

**Diagnostics:**
```bash
cat .env
docker compose config
```

**Solutions:**

1. Verify .env file exists:
```bash
ls -la .env
```

2. Check required variables:
```bash
grep -E "DOMAIN|ADMIN_PASSWORD_HASH|SESSION_SECRET" .env
```

3. Regenerate .env from template:
```bash
cp .env.example .env
# Edit with your values
```

4. Reload environment:
```bash
docker compose down
docker compose up -d
```

## Debugging Commands

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f caddy

# Last 100 lines
docker compose logs --tail=100 xray

# Since timestamp
docker compose logs --since=2024-01-01T00:00:00

# Follow with timestamps
docker compose logs -f --timestamps
```

### Check Service Health

```bash
# Docker health status
docker compose ps

# Detailed inspection
docker inspect stealth-caddy

# Health check logs
docker inspect stealth-caddy | jq '.[0].State.Health'

# Run health check manually
docker compose exec caddy wget -O- http://localhost:2019/config/
```

### Network Diagnostics

```bash
# List networks
docker network ls

# Inspect network
docker network inspect stealth-vpn

# Test connectivity between services
docker compose exec caddy ping admin
docker compose exec admin ping xray

# Check DNS resolution
docker compose exec caddy nslookup admin
```

### Resource Monitoring

```bash
# Real-time stats
docker stats

# Disk usage
docker system df

# Volume usage
docker volume ls
du -sh data/*

# Process list
docker compose exec xray ps aux
```

### Configuration Validation

```bash
# Validate docker-compose.yml
docker compose config

# Validate Caddyfile
docker compose exec caddy caddy validate --config /etc/caddy/Caddyfile

# Validate Xray config
python3 scripts/xray-config-manager.py validate

# Validate Trojan config
python3 scripts/trojan-config-manager.py validate

# Validate Sing-box config
python3 scripts/singbox-config-manager.py validate
```

## Recovery Procedures

### Complete Service Reset

```bash
# Stop all services
docker compose down

# Remove volumes (WARNING: deletes data)
docker compose down -v

# Clean Docker system
docker system prune -a

# Reinstall
./install.sh
```

### Restore from Backup

```bash
# Stop services
docker compose down

# Restore backup
tar -xzf backup-YYYYMMDD-HHMMSS.tar.gz

# Restart services
docker compose up -d

# Verify
./scripts/health-check.sh
```

### Rollback Update

```bash
# Use update script rollback
./scripts/update-system.sh rollback

# Or manual rollback
docker compose down
git checkout previous-version
docker compose build
docker compose up -d
```

## Getting Help

### Collect Diagnostic Information

```bash
# Create diagnostic report
cat > diagnostic-report.txt << EOF
=== System Information ===
$(uname -a)
$(docker --version)
$(docker compose version)

=== Service Status ===
$(docker compose ps)

=== Recent Logs ===
$(docker compose logs --tail=50)

=== Resource Usage ===
$(docker stats --no-stream)

=== Disk Space ===
$(df -h)

=== Network ===
$(docker network inspect stealth-vpn)
EOF

cat diagnostic-report.txt
```

### Check Documentation

- [Deployment Guide](DEPLOYMENT.md)
- [Deployment Modes](docs/DEPLOYMENT_MODES.md)
- [Docker Orchestration](docs/DOCKER_ORCHESTRATION.md)
- [Quick Start](QUICKSTART.md)

### Common Solutions Summary

| Issue | Quick Fix |
|-------|-----------|
| SSL certificate fails | Check DNS, verify ports 80/443 open |
| Service won't start | Check logs, validate config, increase timeout |
| Permission denied | Fix ownership: `sudo chown -R $USER:$USER data/` |
| Out of memory | Use minimal mode, enable swap, reduce limits |
| Port conflict | Stop conflicting service, change port |
| Invalid config | Regenerate from template, validate JSON |
| Health check fails | Increase start_period, check resources |
| Network issues | Verify DNS, check firewall, test connectivity |

## Prevention Best Practices

1. **Always start with minimal mode** for first deployment
2. **Verify DNS** before running install.sh
3. **Check system resources** meet requirements
4. **Create backups** before major changes
5. **Monitor logs** regularly
6. **Test configurations** before applying
7. **Document custom changes**
8. **Keep system updated**
