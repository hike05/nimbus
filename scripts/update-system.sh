#!/bin/bash

# Stealth VPN Server Update Script
# Handles system updates and migrations

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Create backup before update
create_backup() {
    log "Creating backup before update..."
    
    local backup_dir="backups/pre-update-$(date +'%Y%m%d_%H%M%S')"
    mkdir -p "$backup_dir"
    
    # Backup configurations
    cp -r data/stealth-vpn/configs "$backup_dir/" 2>/dev/null || true
    cp .env "$backup_dir/" 2>/dev/null || true
    cp docker-compose.yml "$backup_dir/" 2>/dev/null || true
    
    # Create tarball
    tar -czf "$backup_dir.tar.gz" "$backup_dir"
    rm -rf "$backup_dir"
    
    log "Backup created: $backup_dir.tar.gz"
}

# Pull latest code
pull_updates() {
    log "Pulling latest updates..."
    
    if [[ -d .git ]]; then
        git pull origin main || git pull origin master || warn "Failed to pull updates"
    else
        warn "Not a git repository. Skipping code update"
    fi
}

# Update Docker images
update_images() {
    log "Updating Docker images..."
    
    # Pull latest base images
    docker compose pull || warn "Failed to pull some images"
    
    # Rebuild custom images
    docker compose build --no-cache
    
    log "Docker images updated"
}

# Migrate configuration
migrate_config() {
    log "Checking for configuration migrations..."
    
    # Check if migration script exists
    if [[ -f scripts/migrate-config.py ]]; then
        python3 scripts/migrate-config.py || warn "Configuration migration failed"
    else
        log "No migration script found, skipping"
    fi
}

# Update dependencies
update_dependencies() {
    log "Updating Python dependencies..."
    
    if [[ -f admin-panel/requirements.txt ]]; then
        # Rebuild admin panel with new dependencies
        docker compose build --no-cache admin
    fi
    
    log "Dependencies updated"
}

# Restart services
restart_services() {
    log "Restarting services with new configuration..."
    
    # Stop services gracefully
    docker compose down
    
    # Start services with new images
    docker compose up -d
    
    # Wait for services to be healthy
    log "Waiting for services to become healthy..."
    sleep 15
    
    # Check status
    docker compose ps
}

# Verify update
verify_update() {
    log "Verifying update..."
    
    # Run health checks
    if [[ -f scripts/health-check.sh ]]; then
        bash scripts/health-check.sh || warn "Some health checks failed"
    fi
    
    # Check service logs for errors
    log "Checking service logs for errors..."
    docker compose logs --tail=50 | grep -i error || log "No errors found in logs"
}

# Rollback to backup
rollback() {
    local backup_file=$1
    
    if [[ -z "$backup_file" ]]; then
        # Find latest backup
        backup_file=$(ls -t backups/pre-update-*.tar.gz 2>/dev/null | head -1)
    fi
    
    if [[ -z "$backup_file" ]]; then
        error "No backup file found for rollback"
    fi
    
    warn "Rolling back to backup: $backup_file"
    
    # Stop services
    docker compose down
    
    # Extract backup
    tar -xzf "$backup_file" -C .
    local backup_dir=$(basename "$backup_file" .tar.gz)
    
    # Restore files
    cp -r "$backup_dir/configs/"* data/stealth-vpn/configs/ 2>/dev/null || true
    cp "$backup_dir/.env" . 2>/dev/null || true
    cp "$backup_dir/docker-compose.yml" . 2>/dev/null || true
    
    # Cleanup
    rm -rf "$backup_dir"
    
    # Restart services
    docker compose up -d
    
    log "Rollback completed"
}

# Show update summary
show_summary() {
    echo
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║              Update Completed Successfully                 ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo
    echo -e "${BLUE}Service Status:${NC}"
    docker compose ps
    echo
    echo -e "${BLUE}Next Steps:${NC}"
    echo "  • Check logs: docker compose logs -f"
    echo "  • Run health check: ./scripts/health-check.sh"
    echo "  • Test admin panel: https://your-domain.com/api/v2/storage/upload"
    echo
    echo -e "${YELLOW}Rollback:${NC}"
    echo "  If issues occur, run: $0 rollback"
    echo
}

# Main update function
update() {
    log "Starting system update..."
    echo
    
    # Create backup
    create_backup
    
    # Pull updates
    pull_updates
    
    # Update images
    update_images
    
    # Migrate configuration
    migrate_config
    
    # Update dependencies
    update_dependencies
    
    # Restart services
    restart_services
    
    # Verify update
    verify_update
    
    # Show summary
    show_summary
    
    log "Update completed successfully!"
}

# Usage information
usage() {
    echo "Stealth VPN Server Update Script"
    echo
    echo "Usage: $0 <command>"
    echo
    echo "Commands:"
    echo "  update              Perform full system update"
    echo "  rollback [file]     Rollback to previous backup"
    echo "  backup              Create backup only"
    echo
    echo "Examples:"
    echo "  $0 update           # Update system"
    echo "  $0 rollback         # Rollback to latest backup"
    echo "  $0 backup           # Create backup"
    echo
}

# Main function
main() {
    local command=$1
    
    case "$command" in
        update)
            update
            ;;
        rollback)
            rollback "$2"
            ;;
        backup)
            create_backup
            ;;
        *)
            usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
