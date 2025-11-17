# Monitoring and Logging Guide

This document describes the monitoring and logging system for Stealth VPN Server.

## Overview

The monitoring and logging system provides:

- **Health Monitoring**: Continuous monitoring of all VPN services
- **Centralized Logging**: Structured logging with security features
- **Log Rotation**: Automatic cleanup and compression of old logs
- **Alerting**: Basic alerting system for service failures
- **Privacy Protection**: IP address anonymization in logs

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Monitoring System                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐      ┌──────────────┐                │
│  │ Health       │      │ Logging      │                │
│  │ Monitor      │──────│ Manager      │                │
│  └──────────────┘      └──────────────┘                │
│         │                      │                        │
│         │                      │                        │
│  ┌──────▼──────────────────────▼──────┐                │
│  │     Service Checks & Logs          │                │
│  ├────────────────────────────────────┤                │
│  │ • Caddy      • Xray                │                │
│  │ • Trojan     • Sing-box            │                │
│  │ • WireGuard  • Admin Panel         │                │
│  └────────────────────────────────────┘                │
│                                                          │
│  ┌────────────────────────────────────┐                │
│  │     Outputs                        │                │
│  ├────────────────────────────────────┤                │
│  │ • Health Reports (JSON)            │                │
│  │ • Service Logs (Rotating)          │                │
│  │ • Alert Logs (JSON)                │                │
│  │ • Metrics & Statistics             │                │
│  └────────────────────────────────────┘                │
└─────────────────────────────────────────────────────────┘
```

## Health Monitoring

### Components

1. **Health Monitor** (`core/health_monitor.py`)
   - Checks Docker container status
   - Validates service configurations
   - Measures response times
   - Generates health reports

2. **Service Monitor** (`scripts/monitor-services.py`)
   - Continuous monitoring with configurable intervals
   - Alert generation on failures
   - Failure threshold tracking
   - Historical health logging

### Health Check Endpoints

Each service has health checks configured in `docker-compose.yml`:

- **Caddy**: HTTP check on admin API (port 2019)
- **Xray**: Process check (`pgrep xray`)
- **Trojan**: Process check (`pgrep trojan-go`)
- **Sing-box**: Process check (`pgrep sing-box`)
- **WireGuard**: Interface check (`wg show wg0`)
- **Admin Panel**: HTTP check on `/health` endpoint

### Running Health Checks

```bash
# Single health check
python3 scripts/monitor-services.py

# Continuous monitoring (every 30 seconds)
python3 scripts/monitor-services.py --continuous --interval 30

# Custom data directory
python3 scripts/monitor-services.py --data-dir /custom/path

# Adjust alert threshold
python3 scripts/monitor-services.py --alert-threshold 5
```

### Health Check Output

```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:00",
  "summary": {
    "healthy": 6,
    "unhealthy": 0,
    "degraded": 0,
    "unknown": 0,
    "total": 6
  },
  "services": [
    {
      "service": "caddy",
      "status": "healthy",
      "message": "Service operational",
      "response_time_ms": 45.2
    }
  ]
}
```

### Alert System

Alerts are generated when:

- Service becomes unhealthy
- Service fails health check multiple times (threshold)
- Service recovers from failure
- Configuration validation fails

Alerts are logged to: `data/stealth-vpn/logs/alerts.json`

## Centralized Logging

### Logging Manager

The `LoggingManager` class (`core/logging_manager.py`) provides:

- **Security Filtering**: Automatic IP address anonymization
- **Structured Logging**: JSON format support
- **Log Rotation**: Automatic rotation based on size
- **Service Isolation**: Separate log directories per service

### Log Directory Structure

```
data/stealth-vpn/logs/
├── xray/
│   ├── xray.log
│   └── xray.log.1.gz
├── trojan/
│   ├── trojan.log
│   └── trojan.log.1.gz
├── singbox/
│   ├── singbox.log
│   └── singbox.log.1.gz
├── wireguard/
│   ├── wireguard.log
│   └── wireguard.log.1.gz
├── caddy/
│   ├── caddy.log
│   └── caddy.log.1.gz
├── admin/
│   ├── admin.log
│   └── admin.log.1.gz
├── system/
│   ├── health.log
│   ├── cron.log
│   └── cleanup.log
├── health.json
└── alerts.json
```

### Using the Logging Manager

```python
from core.logging_manager import LoggingManager, setup_service_logging

# Setup logging for a service
logger = setup_service_logging('xray', log_level='INFO', anonymize_ips=True)

# Log messages (IPs will be automatically anonymized)
logger.info("Connection from 192.168.1.100")  # Logged as: "Connection from user_a1b2c3d4"
logger.warning("Failed authentication from 10.0.0.5")
logger.error("Service error occurred")

# Get log statistics
manager = LoggingManager()
stats = manager.get_log_stats()
print(stats)

# Cleanup old logs
deleted = manager.cleanup_old_logs(days=7)
print(f"Deleted {deleted} old log files")
```

### Security Features

1. **IP Anonymization**
   - IPv4 and IPv6 addresses are automatically hashed
   - Consistent hashing maintains user tracking without exposing IPs
   - Example: `192.168.1.100` → `user_a1b2c3d4`

2. **No Sensitive Data**
   - Email addresses can be filtered (optional)
   - Passwords never logged
   - User credentials excluded from logs

3. **Access Control**
   - Log files have restricted permissions (0640)
   - Only root and service users can read logs

### Docker Container Logs

Docker containers use JSON file logging driver with rotation:

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

View container logs:

```bash
# View all logs
docker compose logs -f

# View specific service
docker compose logs -f xray

# View last 100 lines
docker compose logs --tail=100 xray

# View logs since timestamp
docker compose logs --since 2025-01-15T10:00:00 xray
```

## Log Rotation

### Automatic Rotation

Log rotation is handled by:

1. **Python Logging**: Built-in `RotatingFileHandler`
   - Max size: 10MB per file
   - Backup count: 5 files
   - Automatic rotation on size limit

2. **Custom Script**: `scripts/rotate-logs.sh`
   - Compresses logs older than 1 day
   - Deletes logs older than 7 days
   - Calculates disk usage

3. **Logrotate** (optional): `config/logrotate.conf`
   - System-level log rotation
   - Daily rotation with 7-day retention
   - Compression with gzip

### Manual Log Rotation

```bash
# Rotate all logs
bash scripts/rotate-logs.sh

# Custom retention period
MAX_AGE_DAYS=14 bash scripts/rotate-logs.sh

# Custom compression age
COMPRESS_AGE_DAYS=2 bash scripts/rotate-logs.sh

# Force rotation via Python
python3 -c "from core.logging_manager import LoggingManager; m = LoggingManager(); m.rotate_all_logs()"
```

### Installing Logrotate Configuration

```bash
# Copy configuration to system
sudo cp config/logrotate.conf /etc/logrotate.d/stealth-vpn

# Test configuration
sudo logrotate -d /etc/logrotate.d/stealth-vpn

# Force rotation
sudo logrotate -f /etc/logrotate.d/stealth-vpn
```

## Automated Monitoring Setup

### Installation

```bash
# Run setup script
bash scripts/setup-monitoring.sh
```

This script:
- Creates log directories
- Sets up cron jobs for automated tasks
- Creates monitoring dashboard
- Optionally installs systemd service

### Cron Jobs

The setup script installs these cron jobs:

```cron
# Log rotation (daily at 2 AM)
0 2 * * * cd /path/to/project && bash scripts/rotate-logs.sh

# Health checks (every 5 minutes)
*/5 * * * * cd /path/to/project && python3 scripts/monitor-services.py

# Log cleanup (weekly on Sunday at 3 AM)
0 3 * * 0 cd /path/to/project && python3 -c "from core.logging_manager import LoggingManager; m = LoggingManager(); m.cleanup_old_logs(7)"
```

### Systemd Service (Optional)

For continuous monitoring:

```bash
# Enable service
sudo systemctl enable stealth-vpn-monitor

# Start service
sudo systemctl start stealth-vpn-monitor

# Check status
sudo systemctl status stealth-vpn-monitor

# View logs
sudo journalctl -u stealth-vpn-monitor -f
```

## Monitoring Dashboard

### Quick Dashboard

```bash
# Run dashboard script
./scripts/dashboard.sh
```

The dashboard shows:
- Service health status
- Docker container status
- Log disk usage
- Recent alerts
- System resources (CPU, memory, disk)

### Web Dashboard (Admin Panel)

Access the admin panel at: `https://your-domain.com/api/v2/storage/upload`

Features:
- Real-time service status
- User management
- Configuration management
- Backup/restore functionality

## Troubleshooting

### High Disk Usage

```bash
# Check log disk usage
du -sh data/stealth-vpn/logs/*

# Clean up old logs manually
find data/stealth-vpn/logs -name "*.log.*" -mtime +7 -delete

# Reduce retention period
MAX_AGE_DAYS=3 bash scripts/rotate-logs.sh
```

### Service Health Issues

```bash
# Check specific service
docker compose logs xray

# Restart unhealthy service
docker compose restart xray

# Check configuration
python3 scripts/xray-config-manager.py validate

# View health history
cat data/stealth-vpn/logs/health.json | jq '.[-10:]'
```

### Missing Logs

```bash
# Check log directories exist
ls -la data/stealth-vpn/logs/

# Check permissions
ls -la data/stealth-vpn/logs/xray/

# Recreate directories
bash scripts/setup-monitoring.sh
```

### Cron Jobs Not Running

```bash
# Check cron service
sudo systemctl status cron

# View cron logs
grep CRON /var/log/syslog

# Test cron job manually
cd /path/to/project && bash scripts/rotate-logs.sh
```

## Best Practices

1. **Regular Monitoring**
   - Check dashboard daily
   - Review alerts weekly
   - Monitor disk usage monthly

2. **Log Retention**
   - Keep logs for at least 7 days
   - Compress logs older than 1 day
   - Archive important logs separately

3. **Security**
   - Enable IP anonymization in production
   - Restrict log file permissions
   - Regularly review alert logs

4. **Performance**
   - Monitor log disk usage
   - Adjust rotation frequency if needed
   - Use JSON format for structured logging

5. **Backup**
   - Include logs in backup strategy
   - Keep compressed logs for compliance
   - Test log restoration procedures

## API Integration

### Health Check API

```bash
# Check admin panel health
curl http://localhost:8010/health

# Get service status
curl -X GET https://your-domain.com/api/v2/storage/status \
  -H "Cookie: session=your-session-cookie"
```

### Programmatic Access

```python
from core.health_monitor import HealthMonitor

# Create monitor
monitor = HealthMonitor()

# Get health report
report = monitor.get_health_report()
print(report)

# Check specific service
xray_health = monitor.check_xray_service()
print(f"Xray status: {xray_health.status.value}")
```

## Metrics and Statistics

### Available Metrics

- Service uptime
- Response times
- Failure counts
- Log file sizes
- Disk usage
- Alert frequency

### Viewing Statistics

```bash
# Log statistics
python3 -c "from core.logging_manager import LoggingManager; import json; m = LoggingManager(); print(json.dumps(m.get_log_stats(), indent=2))"

# Health statistics
cat data/stealth-vpn/logs/health.json | jq '.[-1]'

# Alert statistics
cat data/stealth-vpn/logs/alerts.json | jq 'group_by(.service) | map({service: .[0].service, count: length})'
```

## Future Enhancements

Potential improvements:

- Prometheus metrics export
- Grafana dashboard integration
- Email/SMS alerting
- Advanced anomaly detection
- Performance metrics collection
- Traffic analysis (anonymized)
- Automated remediation actions

## Support

For issues or questions:

1. Check service logs: `docker compose logs [service]`
2. Run health check: `python3 scripts/monitor-services.py`
3. Review alerts: `cat data/stealth-vpn/logs/alerts.json`
4. Check documentation: `docs/`
