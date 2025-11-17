# Monitoring Quick Reference

Quick reference guide for monitoring and logging in Stealth VPN Server.

## Quick Start

```bash
# Setup monitoring (run once)
bash scripts/setup-monitoring.sh

# View dashboard
./scripts/dashboard.sh

# Check health
python3 scripts/monitor-services.py

# Rotate logs manually
bash scripts/rotate-logs.sh
```

## Health Monitoring

### Single Check
```bash
python3 scripts/monitor-services.py
```

### Continuous Monitoring
```bash
# Every 30 seconds
python3 scripts/monitor-services.py --continuous --interval 30

# Every 5 minutes
python3 scripts/monitor-services.py --continuous --interval 300
```

### Check Specific Service
```bash
# Via Docker
docker compose ps
docker compose logs -f xray

# Via health check
python3 -c "from core.health_monitor import HealthMonitor; m = HealthMonitor(); print(m.check_xray_service())"
```

## Logging

### View Logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f xray
docker compose logs -f trojan
docker compose logs -f singbox
docker compose logs -f wireguard
docker compose logs -f caddy
docker compose logs -f admin

# Last 100 lines
docker compose logs --tail=100 xray

# Since timestamp
docker compose logs --since 2025-01-15T10:00:00 xray
```

### Application Logs
```bash
# View service logs
tail -f data/stealth-vpn/logs/xray/xray.log
tail -f data/stealth-vpn/logs/admin/admin.log

# View health logs
tail -f data/stealth-vpn/logs/system/health.log

# View alerts
cat data/stealth-vpn/logs/alerts.json | jq '.'
```

### Log Statistics
```bash
# Disk usage
du -sh data/stealth-vpn/logs/*

# File counts
find data/stealth-vpn/logs -name "*.log*" | wc -l

# Get stats via Python
python3 -c "from core.logging_manager import LoggingManager; import json; m = LoggingManager(log_dir='./data/stealth-vpn/logs'); print(json.dumps(m.get_log_stats(), indent=2))"
```

## Log Rotation

### Manual Rotation
```bash
# Rotate all logs
bash scripts/rotate-logs.sh

# Custom retention (14 days)
MAX_AGE_DAYS=14 bash scripts/rotate-logs.sh

# Custom compression age (2 days)
COMPRESS_AGE_DAYS=2 bash scripts/rotate-logs.sh
```

### Automatic Rotation
```bash
# View cron jobs
crontab -l | grep stealth-vpn

# Edit cron jobs
crontab -e
```

## Alerts

### View Recent Alerts
```bash
# Last 10 alerts
cat data/stealth-vpn/logs/alerts.json | jq '.[-10:]'

# Alerts by service
cat data/stealth-vpn/logs/alerts.json | jq 'group_by(.service) | map({service: .[0].service, count: length})'

# Critical alerts only
cat data/stealth-vpn/logs/alerts.json | jq '.[] | select(.severity == "critical")'
```

## Service Management

### Restart Services
```bash
# Restart all
docker compose restart

# Restart specific service
docker compose restart xray
docker compose restart trojan
docker compose restart singbox
docker compose restart wireguard
docker compose restart caddy
docker compose restart admin
```

### Reload Configurations
```bash
# Via admin panel API
curl -X POST https://your-domain.com/api/v2/storage/services/xray/reload \
  -H "Cookie: session=your-session-cookie"

# Via Docker
docker compose exec xray pkill -HUP xray
docker compose exec trojan pkill -HUP trojan-go
docker compose exec caddy caddy reload --config /etc/caddy/Caddyfile
```

## Troubleshooting

### Service Not Healthy
```bash
# 1. Check logs
docker compose logs xray

# 2. Check configuration
python3 scripts/xray-config-manager.py validate

# 3. Restart service
docker compose restart xray

# 4. Check health again
python3 scripts/monitor-services.py
```

### High Disk Usage
```bash
# 1. Check usage
du -sh data/stealth-vpn/logs/*

# 2. Clean old logs
MAX_AGE_DAYS=3 bash scripts/rotate-logs.sh

# 3. Manual cleanup
find data/stealth-vpn/logs -name "*.log.*" -mtime +7 -delete
```

### Missing Logs
```bash
# 1. Check directories
ls -la data/stealth-vpn/logs/

# 2. Recreate structure
mkdir -p data/stealth-vpn/logs/{xray,trojan,singbox,wireguard,caddy,admin,system}

# 3. Check permissions
chmod -R 755 data/stealth-vpn/logs/
```

## Automated Setup

### Install Monitoring
```bash
# Run setup script
bash scripts/setup-monitoring.sh

# This installs:
# - Cron jobs for health checks (every 5 minutes)
# - Cron jobs for log rotation (daily at 2 AM)
# - Cron jobs for cleanup (weekly on Sunday)
# - Dashboard script
```

### Systemd Service (Optional)
```bash
# Enable continuous monitoring
sudo systemctl enable stealth-vpn-monitor
sudo systemctl start stealth-vpn-monitor

# Check status
sudo systemctl status stealth-vpn-monitor

# View logs
sudo journalctl -u stealth-vpn-monitor -f
```

## Dashboard

### Terminal Dashboard
```bash
./scripts/dashboard.sh
```

Shows:
- Service health status
- Docker container status
- Log disk usage
- Recent alerts
- System resources

### Web Dashboard
Access at: `https://your-domain.com/api/v2/storage/upload`

Features:
- Real-time service status
- User management
- Configuration management
- Backup/restore

## API Endpoints

### Health Check
```bash
# Admin panel health
curl http://localhost:8010/health

# Service status
curl -X GET https://your-domain.com/api/v2/storage/status \
  -H "Cookie: session=your-session-cookie"
```

### Service Control
```bash
# Reload service
curl -X POST https://your-domain.com/api/v2/storage/services/xray/reload \
  -H "Cookie: session=your-session-cookie"

# Update all configs
curl -X POST https://your-domain.com/api/v2/storage/configs/update \
  -H "Cookie: session=your-session-cookie"
```

## Security Features

### IP Anonymization
All IP addresses in logs are automatically anonymized:
- `192.168.1.100` → `user_2a39f1ee`
- Consistent hashing maintains tracking
- No actual IPs stored in logs

### Log Permissions
```bash
# Set secure permissions
chmod 640 data/stealth-vpn/logs/*/*.log
chown root:root data/stealth-vpn/logs/*/*.log
```

## Performance Tips

1. **Adjust Log Levels**
   - Use INFO for production
   - Use DEBUG only for troubleshooting
   - Reduce verbosity to save disk space

2. **Optimize Rotation**
   - Rotate daily for high-traffic servers
   - Compress logs older than 1 day
   - Keep 7 days of logs minimum

3. **Monitor Disk Usage**
   - Check weekly: `du -sh data/stealth-vpn/logs/*`
   - Set up alerts for >500MB usage
   - Clean up old logs regularly

## Documentation

For detailed information, see:
- [Full Monitoring Guide](docs/MONITORING_AND_LOGGING.md)
- [Docker Orchestration](docs/DOCKER_ORCHESTRATION.md)
- [Admin Panel Usage](docs/ADMIN_PANEL_USAGE.md)
