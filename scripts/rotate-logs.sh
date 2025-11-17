#!/bin/bash

# Log rotation script for Stealth VPN Server
# Rotates and compresses old log files

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

# Configuration
LOG_DIR="${LOG_DIR:-./data/stealth-vpn/logs}"
MAX_AGE_DAYS="${MAX_AGE_DAYS:-7}"
COMPRESS_AGE_DAYS="${COMPRESS_AGE_DAYS:-1}"

# Ensure log directory exists
if [[ ! -d "$LOG_DIR" ]]; then
    error "Log directory not found: $LOG_DIR"
    exit 1
fi

log "Starting log rotation..."
log "Log directory: $LOG_DIR"
log "Max age: $MAX_AGE_DAYS days"
log "Compress age: $COMPRESS_AGE_DAYS days"

# Function to rotate logs for a service
rotate_service_logs() {
    local service=$1
    local service_dir="$LOG_DIR/$service"
    
    if [[ ! -d "$service_dir" ]]; then
        warn "Service directory not found: $service_dir"
        return
    fi
    
    log "Rotating logs for $service..."
    
    # Count files
    local total_files=$(find "$service_dir" -type f -name "*.log*" | wc -l)
    local compressed=0
    local deleted=0
    
    # Compress old logs (older than COMPRESS_AGE_DAYS)
    while IFS= read -r -d '' logfile; do
        if [[ ! "$logfile" =~ \.gz$ ]]; then
            gzip "$logfile"
            ((compressed++))
        fi
    done < <(find "$service_dir" -type f -name "*.log*" -mtime +$COMPRESS_AGE_DAYS ! -name "*.gz" -print0)
    
    # Delete very old logs (older than MAX_AGE_DAYS)
    while IFS= read -r -d '' logfile; do
        rm -f "$logfile"
        ((deleted++))
    done < <(find "$service_dir" -type f -name "*.log*" -mtime +$MAX_AGE_DAYS -print0)
    
    if [[ $compressed -gt 0 ]]; then
        log "  Compressed $compressed log files"
    fi
    
    if [[ $deleted -gt 0 ]]; then
        log "  Deleted $deleted old log files"
    fi
    
    # Calculate disk usage
    local disk_usage=$(du -sh "$service_dir" 2>/dev/null | cut -f1)
    log "  Disk usage: $disk_usage"
}

# Rotate logs for all services
for service in xray trojan singbox wireguard caddy admin system; do
    rotate_service_logs "$service"
done

# Rotate Docker container logs
log "Rotating Docker container logs..."
for container in stealth-caddy stealth-xray stealth-trojan stealth-singbox stealth-wireguard stealth-admin; do
    if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        # Get log file path
        log_file=$(docker inspect --format='{{.LogPath}}' "$container" 2>/dev/null || echo "")
        
        if [[ -n "$log_file" && -f "$log_file" ]]; then
            # Check log file size
            log_size=$(stat -f%z "$log_file" 2>/dev/null || stat -c%s "$log_file" 2>/dev/null || echo "0")
            log_size_mb=$((log_size / 1024 / 1024))
            
            if [[ $log_size_mb -gt 50 ]]; then
                warn "  $container log is ${log_size_mb}MB (consider adjusting max-size in docker-compose.yml)"
            fi
        fi
    fi
done

# Clean up empty directories
log "Cleaning up empty directories..."
find "$LOG_DIR" -type d -empty -delete 2>/dev/null || true

# Summary
log "Log rotation completed successfully"

# Calculate total disk usage
total_usage=$(du -sh "$LOG_DIR" 2>/dev/null | cut -f1)
log "Total log disk usage: $total_usage"

# Check if disk usage is too high
total_bytes=$(du -sb "$LOG_DIR" 2>/dev/null | cut -f1)
total_mb=$((total_bytes / 1024 / 1024))

if [[ $total_mb -gt 500 ]]; then
    warn "Log directory is using ${total_mb}MB of disk space"
    warn "Consider reducing MAX_AGE_DAYS or increasing compression frequency"
fi

exit 0
