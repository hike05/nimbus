#!/bin/bash

# Rollback script for migration
# Restores the system to pre-migration state

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Rollback log file
ROLLBACK_LOG="rollback_$(date +'%Y%m%d_%H%M%S').log"

log() {
    local timestamp=$(date +'%Y-%m-%d %H:%M:%S')
    echo -e "${GREEN}[$timestamp] $1${NC}"
    echo "[$timestamp] $1" >> "$ROLLBACK_LOG"
}

warn() {
    local timestamp=$(date +'%Y-%m-%d %H:%M:%S')
    echo -e "${YELLOW}[$timestamp] WARNING: $1${NC}"
    echo "[$timestamp] WARNING: $1" >> "$ROLLBACK_LOG"
}

error() {
    local timestamp=$(date +'%Y-%m-%d %H:%M:%S')
    echo -e "${RED}[$timestamp] ERROR: $1${NC}"
    echo "[$timestamp] ERROR: $1" >> "$ROLLBACK_LOG"
    exit 1
}

success() {
    local timestamp=$(date +'%Y-%m-%d %H:%M:%S')
    echo -e "${GREEN}[$timestamp] ✓ $1${NC}"
    echo "[$timestamp] $1" >> "$ROLLBACK_LOG"
}

# Check for pre-migration backups
check_backups() {
    log "Checking for pre-migration backups..."
    
    local found_backups=false
    
    if [[ -f docker-compose.yml.pre-migration ]]; then
        log "Found docker-compose.yml.pre-migration"
        found_backups=true
    else
        warn "docker-compose.yml.pre-migration not found"
    fi
    
    if [[ -f config/Caddyfile.pre-migration ]]; then
        log "Found Caddyfile.pre-migration"
        found_backups=true
    else
        warn "Caddyfile.pre-migration not found"
    fi
    
    if [[ -d data/stealth-vpn/backups ]]; then
        local backup_count=$(ls -1 data/stealth-vpn/backups/backup_*.tar.gz 2>/dev/null | wc -l)
        if [[ $backup_count -gt 0 ]]; then
            log "Found $backup_count configuration backup(s)"
            found_backups=true
        fi
    fi
    
    if [[ "$found_backups" == "false" ]]; then
        error "No pre-migration backups found. Cannot rollback."
    fi
    
    success "Pre-migration backups found"
}

# Stop services
stop_services() {
    log "Stopping services..."
    
    if docker compose down 2>&1 | tee -a "$ROLLBACK_LOG"; then
        success "Services stopped"
    else
        error "Failed to stop services"
    fi
}

# Restore docker-compose.yml
restore_docker_compose() {
    log "Restoring docker-compose.yml..."
    
    if [[ -f docker-compose.yml.pre-migration ]]; then
        if cp docker-compose.yml.pre-migration docker-compose.yml 2>&1 | tee -a "$ROLLBACK_LOG"; then
            success "docker-compose.yml restored"
        else
            error "Failed to restore docker-compose.yml"
        fi
    else
        warn "docker-compose.yml.pre-migration not found, skipping"
    fi
}

# Restore Caddyfile
restore_caddyfile() {
    log "Restoring Caddyfile..."
    
    if [[ -f config/Caddyfile.pre-migration ]]; then
        if cp config/Caddyfile.pre-migration config/Caddyfile 2>&1 | tee -a "$ROLLBACK_LOG"; then
            success "Caddyfile restored"
        else
            error "Failed to restore Caddyfile"
        fi
    else
        warn "Caddyfile.pre-migration not found, skipping"
    fi
}

# Restore configuration backup
restore_config_backup() {
    log "Looking for configuration backups..."
    
    # Find the most recent backup
    local latest_backup=$(ls -t data/stealth-vpn/backups/backup_*.tar.gz 2>/dev/null | head -1)
    
    if [[ -z "$latest_backup" ]]; then
        warn "No configuration backups found"
        return 0
    fi
    
    log "Found backup: $latest_backup"
    echo
    echo -e "${YELLOW}Do you want to restore configuration from backup?${NC}"
    echo "Backup: $(basename $latest_backup)"
    echo "This will restore:"
    echo "  • User configurations"
    echo "  • VPN service configs"
    echo "  • Client configurations"
    echo "  • SSL certificates (if included)"
    echo
    read -p "Restore configuration backup? (y/n): " RESTORE_CONFIG
    
    if [[ "$RESTORE_CONFIG" =~ ^[Yy]$ ]]; then
        log "Restoring configuration backup..."
        
        # Use admin panel BackupManager if available
        if docker ps | grep -q "stealth-admin"; then
            log "Using admin panel BackupManager..."
            
            local backup_name=$(basename "$latest_backup")
            if docker exec stealth-admin python3 -c "
from core.backup_manager import BackupManager
bm = BackupManager()
result = bm.restore_backup('$backup_name')
if result['success']:
    print('Backup restored successfully')
    exit(0)
else:
    print(f\"Backup restore failed: {result['message']}\")
    exit(1)
" 2>&1 | tee -a "$ROLLBACK_LOG"; then
                success "Configuration backup restored via BackupManager"
            else
                warn "Failed to restore via BackupManager, trying manual restore..."
                
                # Manual restore
                if tar -xzf "$latest_backup" -C / 2>&1 | tee -a "$ROLLBACK_LOG"; then
                    success "Configuration backup restored manually"
                else
                    error "Failed to restore configuration backup"
                fi
            fi
        else
            # Manual restore
            log "Admin container not running, using manual restore..."
            if tar -xzf "$latest_backup" -C / 2>&1 | tee -a "$ROLLBACK_LOG"; then
                success "Configuration backup restored manually"
            else
                error "Failed to restore configuration backup"
            fi
        fi
    else
        log "Skipping configuration backup restore"
    fi
}

# Rebuild images
rebuild_images() {
    log "Rebuilding Docker images..."
    
    if docker compose build 2>&1 | tee -a "$ROLLBACK_LOG"; then
        success "Docker images rebuilt"
    else
        error "Failed to rebuild Docker images"
    fi
}

# Start services
start_services() {
    log "Starting services..."
    
    if docker compose up -d 2>&1 | tee -a "$ROLLBACK_LOG"; then
        success "Services started"
        
        # Wait for services to be healthy
        log "Waiting for services to become healthy..."
        sleep 15
        
        # Check service status
        docker compose ps
    else
        error "Failed to start services"
    fi
}

# Verify services
verify_services() {
    log "Verifying services..."
    
    local failed_services=()
    
    # Check each service
    for service in caddy admin xray trojan singbox wireguard; do
        if docker compose ps | grep "$service" | grep -q "Up"; then
            log "✓ $service is running"
        else
            warn "✗ $service is not running"
            failed_services+=("$service")
        fi
    done
    
    if [[ ${#failed_services[@]} -eq 0 ]]; then
        success "All services verified"
    else
        warn "Some services failed: ${failed_services[*]}"
        warn "Check logs: docker compose logs -f"
    fi
}

# Display rollback summary
display_summary() {
    echo
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║              Rollback Summary                              ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo
    echo -e "${GREEN}Rollback completed!${NC}"
    echo
    echo "Restored items:"
    echo "  ✓ docker-compose.yml"
    echo "  ✓ Caddyfile"
    if [[ "$RESTORE_CONFIG" =~ ^[Yy]$ ]]; then
        echo "  ✓ Configuration backup"
    fi
    echo
    echo "Next steps:"
    echo "  • Check service logs: docker compose logs -f"
    echo "  • Run health checks: ./scripts/health-check.sh"
    echo "  • Verify admin panel: https://your-domain.com/admin"
    echo "  • Test VPN connectivity"
    echo
    echo "Rollback log saved to: $ROLLBACK_LOG"
    echo
}

# Main rollback function
main() {
    echo
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║         Migration Rollback Script                         ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo
    log "Starting rollback process..."
    log "Rollback log: $ROLLBACK_LOG"
    echo
    
    # Confirmation prompt
    echo -e "${YELLOW}This script will:${NC}"
    echo "  • Stop all running services"
    echo "  • Restore docker-compose.yml from pre-migration backup"
    echo "  • Restore Caddyfile from pre-migration backup"
    echo "  • Optionally restore configuration backup"
    echo "  • Rebuild Docker images"
    echo "  • Restart services"
    echo
    echo -e "${RED}WARNING: This will undo all changes made by the migration.${NC}"
    echo
    read -p "Do you want to continue with rollback? (y/n): " CONFIRM
    if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
        log "Rollback cancelled by user"
        exit 0
    fi
    echo
    
    # Run rollback steps
    check_backups
    stop_services
    restore_docker_compose
    restore_caddyfile
    restore_config_backup
    rebuild_images
    start_services
    sleep 5
    verify_services
    
    # Display summary
    display_summary
}

# Run main function
main "$@"
