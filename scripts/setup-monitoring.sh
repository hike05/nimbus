#!/bin/bash

# Setup monitoring and log rotation for Multi-Protocol Proxy Server
# Configures cron jobs for automated maintenance

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

log "Setting up monitoring and log rotation..."
log "Project directory: $PROJECT_DIR"

# Check if running as root or with sudo
if [[ $EUID -ne 0 ]]; then
    warn "This script should be run with sudo for cron job setup"
    warn "Some features may not work without root privileges"
fi

# Create log directories
log "Creating log directories..."
mkdir -p "$PROJECT_DIR/data/proxy/logs"/{xray,trojan,singbox,wireguard,caddy,admin,system}

# Install Python dependencies for monitoring
log "Checking Python dependencies..."
if command -v python3 &> /dev/null; then
    log "Python 3 is installed"
else
    error "Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Create systemd service for continuous monitoring (optional)
create_systemd_service() {
    log "Creating systemd service for monitoring..."
    
    cat > /tmp/proxy-monitor.service <<EOF
[Unit]
Description=Multi-Protocol Proxy Server Monitoring
After=docker.service
Requires=docker.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
ExecStart=/usr/bin/python3 $PROJECT_DIR/scripts/monitor-services.py --continuous --interval 60
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    if [[ $EUID -eq 0 ]]; then
        mv /tmp/proxy-monitor.service /etc/systemd/system/
        systemctl daemon-reload
        log "Systemd service created: proxy-monitor.service"
        log "To enable: sudo systemctl enable proxy-monitor"
        log "To start: sudo systemctl start proxy-monitor"
    else
        warn "Cannot install systemd service without root privileges"
        warn "Service file created at: /tmp/proxy-monitor.service"
    fi
}

# Setup cron jobs
setup_cron_jobs() {
    log "Setting up cron jobs..."
    
    # Create temporary cron file
    CRON_FILE="/tmp/proxy-cron"
    
    # Get existing crontab (if any)
    crontab -l > "$CRON_FILE" 2>/dev/null || echo "# Multi-Protocol Proxy Server Cron Jobs" > "$CRON_FILE"
    
    # Remove existing proxy cron jobs
    sed -i.bak '/Multi-Protocol Proxy Server/d' "$CRON_FILE"
    
    # Add new cron jobs
    cat >> "$CRON_FILE" <<EOF

# Multi-Protocol Proxy Server - Log rotation (daily at 2 AM)
0 2 * * * cd $PROJECT_DIR && bash scripts/rotate-logs.sh >> data/proxy/logs/system/cron.log 2>&1

# Multi-Protocol Proxy Server - Health check (every 5 minutes)
*/5 * * * * cd $PROJECT_DIR && python3 scripts/monitor-services.py >> data/proxy/logs/system/health.log 2>&1

# Multi-Protocol Proxy Server - Cleanup old logs (weekly on Sunday at 3 AM)
0 3 * * 0 cd $PROJECT_DIR && python3 -c "from core.logging_manager import LoggingManager; m = LoggingManager(); print(m.cleanup_old_logs(7))" >> data/proxy/logs/system/cleanup.log 2>&1

EOF
    
    # Install new crontab
    if crontab "$CRON_FILE"; then
        log "Cron jobs installed successfully"
        log "Installed jobs:"
        echo "  - Log rotation: Daily at 2 AM"
        echo "  - Health checks: Every 5 minutes"
        echo "  - Log cleanup: Weekly on Sunday at 3 AM"
    else
        error "Failed to install cron jobs"
        return 1
    fi
    
    # Cleanup
    rm -f "$CRON_FILE" "$CRON_FILE.bak"
}

# Create monitoring dashboard script
create_dashboard_script() {
    log "Creating monitoring dashboard script..."
    
    cat > "$PROJECT_DIR/scripts/dashboard.sh" <<'EOF'
#!/bin/bash

# Simple monitoring dashboard for Multi-Protocol Proxy Server

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

clear
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║    Multi-Protocol Proxy Server - Monitoring Dashboard     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo

# Service status
echo -e "${YELLOW}Service Status:${NC}"
python3 scripts/monitor-services.py
echo

# Docker container status
echo -e "${YELLOW}Docker Containers:${NC}"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo

# Log disk usage
echo -e "${YELLOW}Log Disk Usage:${NC}"
du -sh data/proxy/logs/* 2>/dev/null | sort -h
echo

# Recent alerts
echo -e "${YELLOW}Recent Alerts (last 10):${NC}"
if [[ -f data/proxy/logs/alerts.json ]]; then
    python3 -c "
import json
with open('data/proxy/logs/alerts.json') as f:
    alerts = json.load(f)
    for alert in alerts[-10:]:
        print(f\"{alert['timestamp']} [{alert['severity'].upper()}] {alert['service']}: {alert['message']}\")
" 2>/dev/null || echo "No alerts"
else
    echo "No alerts"
fi
echo

# System resources
echo -e "${YELLOW}System Resources:${NC}"
echo "CPU Usage: $(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1"%"}')"
echo "Memory: $(free -h | awk '/^Mem:/ {print $3 "/" $2}')"
echo "Disk: $(df -h / | awk 'NR==2 {print $3 "/" $2 " (" $5 " used)"}')"
echo

echo -e "${BLUE}Press Ctrl+C to exit${NC}"
EOF
    
    chmod +x "$PROJECT_DIR/scripts/dashboard.sh"
    log "Dashboard script created: scripts/dashboard.sh"
}

# Main setup
main() {
    log "Starting monitoring setup..."
    echo
    
    # Setup cron jobs
    setup_cron_jobs
    echo
    
    # Create dashboard
    create_dashboard_script
    echo
    
    # Ask about systemd service
    if [[ $EUID -eq 0 ]]; then
        read -p "Do you want to create a systemd service for continuous monitoring? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            create_systemd_service
        fi
    fi
    
    echo
    log "Monitoring setup completed successfully!"
    echo
    echo -e "${BLUE}Available commands:${NC}"
    echo "  - View dashboard:        ./scripts/dashboard.sh"
    echo "  - Run health check:      python3 scripts/monitor-services.py"
    echo "  - Continuous monitoring: python3 scripts/monitor-services.py --continuous"
    echo "  - Rotate logs manually:  bash scripts/rotate-logs.sh"
    echo "  - View cron jobs:        crontab -l | grep proxy-server"
    echo
    echo -e "${YELLOW}Note: Cron jobs will run automatically according to schedule${NC}"
    echo
}

# Run main function
main "$@"
