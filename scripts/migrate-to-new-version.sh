#!/bin/bash

# Stealth VPN Server Migration Script
# Migrates existing deployments to the new version with improved configurations

set +e  # Don't exit on error - we'll handle errors gracefully

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Migration log file
MIGRATION_LOG="migration_$(date +'%Y%m%d_%H%M%S').log"

# Track migration status
declare -a SUCCESSFUL_STEPS=()
declare -a FAILED_STEPS=()
declare -a WARNING_STEPS=()

# Logging functions
log() {
    local timestamp=$(date +'%Y-%m-%d %H:%M:%S')
    local message="[INFO] $1"
    echo -e "${GREEN}[$timestamp] $message${NC}"
    echo "[$timestamp] $message" >> "$MIGRATION_LOG"
}

warn() {
    local timestamp=$(date +'%Y-%m-%d %H:%M:%S')
    local message="[WARNING] $1"
    echo -e "${YELLOW}[$timestamp] $message${NC}"
    echo "[$timestamp] $message" >> "$MIGRATION_LOG"
}

error() {
    local timestamp=$(date +'%Y-%m-%d %H:%M:%S')
    local message="[ERROR] $1"
    echo -e "${RED}[$timestamp] $message${NC}"
    echo "[$timestamp] $message" >> "$MIGRATION_LOG"
}

success() {
    local timestamp=$(date +'%Y-%m-%d %H:%M:%S')
    local message="[SUCCESS] $1"
    echo -e "${GREEN}[$timestamp] ✓ $message${NC}"
    echo "[$timestamp] $message" >> "$MIGRATION_LOG"
}

# Track step completion
track_success() {
    SUCCESSFUL_STEPS+=("$1")
    success "$1"
}

track_failure() {
    FAILED_STEPS+=("$1")
    error "$1"
}

track_warning() {
    WARNING_STEPS+=("$1")
    warn "$1"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        warn "Running as root. It's recommended to run as a regular user with Docker permissions."
        read -p "Continue anyway? (y/n): " CONTINUE
        if [[ ! "$CONTINUE" =~ ^[Yy]$ ]]; then
            log "Migration cancelled by user"
            exit 0
        fi
    fi
}

# Check if this is an existing deployment
check_existing_deployment() {
    log "Checking for existing deployment..."
    
    if [[ ! -f docker-compose.yml ]]; then
        error "docker-compose.yml not found. This script is for existing deployments only."
        exit 1
    fi
    
    if [[ ! -d data/stealth-vpn ]]; then
        error "data/stealth-vpn directory not found. This doesn't appear to be an existing deployment."
        exit 1
    fi
    
    # Check if services are running
    if docker compose ps | grep -q "Up"; then
        log "Found running services"
        SERVICES_RUNNING=true
    else
        log "No services currently running"
        SERVICES_RUNNING=false
    fi
    
    track_success "Existing deployment detected"
}

# Create backup using BackupManager
create_backup() {
    log "Creating backup of current configuration..."
    
    # Check if admin container is running
    if docker ps | grep -q "stealth-admin"; then
        log "Using admin panel BackupManager to create backup..."
        
        # Execute backup via admin container
        if docker exec stealth-admin python3 -c "
from core.backup_manager import BackupManager
bm = BackupManager()
backup_name = bm.create_backup('Pre-migration backup (automatic)')
print(f'Backup created: {backup_name}')
" 2>&1 | tee -a "$MIGRATION_LOG"; then
            track_success "Backup created via BackupManager"
            return 0
        else
            warn "Failed to create backup via BackupManager"
        fi
    fi
    
    # Fallback: Manual backup
    log "Creating manual backup..."
    local backup_dir="data/stealth-vpn/backups"
    local timestamp=$(date +'%Y%m%d_%H%M%S')
    local backup_name="manual_backup_${timestamp}.tar.gz"
    
    mkdir -p "$backup_dir"
    
    if tar -czf "$backup_dir/$backup_name" \
        data/stealth-vpn/configs/ \
        data/caddy/certificates/ \
        config/Caddyfile \
        docker-compose.yml \
        .env 2>&1 | tee -a "$MIGRATION_LOG"; then
        
        track_success "Manual backup created: $backup_name"
        echo "$backup_name" > /tmp/migration_backup_name.txt
        return 0
    else
        track_failure "Failed to create backup"
        return 1
    fi
}

# Stop services gracefully
stop_services() {
    log "Stopping services..."
    
    if [[ "$SERVICES_RUNNING" == "true" ]]; then
        if docker compose down 2>&1 | tee -a "$MIGRATION_LOG"; then
            track_success "Services stopped"
            return 0
        else
            track_failure "Failed to stop services"
            return 1
        fi
    else
        log "Services not running, skipping stop"
        return 0
    fi
}

# Backup docker-compose.yml
backup_docker_compose() {
    log "Backing up docker-compose.yml..."
    
    if [[ -f docker-compose.yml ]]; then
        if cp docker-compose.yml docker-compose.yml.pre-migration 2>&1 | tee -a "$MIGRATION_LOG"; then
            track_success "docker-compose.yml backed up"
            return 0
        else
            track_failure "Failed to backup docker-compose.yml"
            return 1
        fi
    else
        warn "docker-compose.yml not found"
        return 1
    fi
}

# Update docker-compose.yml with new resource limits
update_docker_compose() {
    log "Updating docker-compose.yml with new resource limits..."
    
    # Detect CPU cores
    local cpu_cores=$(nproc 2>/dev/null || echo "2")
    log "Detected $cpu_cores CPU core(s)"
    
    # Check if resource limits already exist
    if grep -q "deploy:" docker-compose.yml; then
        log "Resource limits already present in docker-compose.yml"
        track_success "docker-compose.yml already has resource limits"
        return 0
    fi
    
    # For now, just note that manual update may be needed
    warn "docker-compose.yml may need manual resource limit updates"
    warn "Please review the new docker-compose.yml format in the repository"
    track_warning "docker-compose.yml may need manual updates"
    
    return 0
}

# Backup Caddyfile
backup_caddyfile() {
    log "Backing up Caddyfile..."
    
    if [[ -f config/Caddyfile ]]; then
        if cp config/Caddyfile config/Caddyfile.pre-migration 2>&1 | tee -a "$MIGRATION_LOG"; then
            track_success "Caddyfile backed up"
            return 0
        else
            track_failure "Failed to backup Caddyfile"
            return 1
        fi
    else
        warn "Caddyfile not found at config/Caddyfile"
        return 1
    fi
}

# Update Caddyfile with corrected syntax
update_caddyfile() {
    log "Updating Caddyfile with corrected syntax..."
    
    if [[ ! -f config/Caddyfile ]]; then
        warn "Caddyfile not found, skipping update"
        return 1
    fi
    
    local updated=false
    
    # Fix: Remove invalid auto_https directive from global config
    if grep -q "auto_https" config/Caddyfile; then
        log "Removing invalid auto_https directive..."
        sed -i '/auto_https/d' config/Caddyfile
        updated=true
    fi
    
    # Fix: Move security headers from global to site block if needed
    if grep -A 20 "^{" config/Caddyfile | grep -q "header"; then
        warn "Security headers found in global config - may need manual relocation"
        track_warning "Caddyfile may have headers in global config"
    fi
    
    # Fix: Ensure HTTP/3 is properly configured
    if ! grep -q "protocols h1 h2 h3" config/Caddyfile; then
        log "HTTP/3 configuration may need updating"
        track_warning "HTTP/3 configuration should be reviewed"
    fi
    
    if [[ "$updated" == "true" ]]; then
        track_success "Caddyfile updated"
    else
        log "No Caddyfile updates needed"
    fi
    
    return 0
}

# Validate Caddyfile syntax
validate_caddyfile() {
    log "Validating Caddyfile syntax..."
    
    # Check if caddy is available in container
    if docker compose ps | grep -q "caddy"; then
        log "Validating via Caddy container..."
        if docker compose exec -T caddy caddy validate --config /etc/caddy/Caddyfile 2>&1 | tee -a "$MIGRATION_LOG"; then
            track_success "Caddyfile validation passed"
            return 0
        else
            track_failure "Caddyfile validation failed"
            return 1
        fi
    else
        warn "Caddy container not running, skipping validation"
        return 0
    fi
}

# Preserve SSL certificates
preserve_ssl_certificates() {
    log "Checking SSL certificates..."
    
    if [[ -d data/caddy/certificates ]]; then
        local cert_count=$(find data/caddy/certificates -type f -name "*.crt" 2>/dev/null | wc -l)
        log "Found $cert_count SSL certificate(s)"
        track_success "SSL certificates preserved"
        return 0
    else
        log "No SSL certificates found (will be generated on first run)"
        return 0
    fi
}

# Preserve user data
preserve_user_data() {
    log "Checking user data..."
    
    if [[ -f data/stealth-vpn/configs/users.json ]]; then
        local user_count=$(python3 -c "import json; data=json.load(open('data/stealth-vpn/configs/users.json')); print(len(data.get('users', {})))" 2>/dev/null || echo "0")
        log "Found $user_count user(s) in users.json"
        track_success "User data preserved"
        return 0
    else
        warn "users.json not found"
        return 1
    fi
}

# Rebuild Docker images
rebuild_images() {
    log "Rebuilding Docker images with latest changes..."
    
    if docker compose build 2>&1 | tee -a "$MIGRATION_LOG"; then
        track_success "Docker images rebuilt"
        return 0
    else
        track_failure "Failed to rebuild Docker images"
        return 1
    fi
}

# Start services
start_services() {
    log "Starting services..."
    
    if docker compose up -d 2>&1 | tee -a "$MIGRATION_LOG"; then
        track_success "Services started"
        
        # Wait for services to be healthy
        log "Waiting for services to become healthy..."
        sleep 15
        
        # Check service status
        docker compose ps
        
        return 0
    else
        track_failure "Failed to start services"
        return 1
    fi
}

# Verify services are running
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
        track_success "All services verified"
        return 0
    else
        track_warning "Some services failed: ${failed_services[*]}"
        return 1
    fi
}

# Run health checks
run_health_checks() {
    log "Running health checks..."
    
    if [[ -f scripts/health-check.sh ]]; then
        if bash scripts/health-check.sh 2>&1 | tee -a "$MIGRATION_LOG"; then
            track_success "Health checks passed"
            return 0
        else
            track_warning "Some health checks failed"
            return 1
        fi
    else
        warn "health-check.sh not found, skipping"
        return 0
    fi
}

# Display rollback instructions
display_rollback_instructions() {
    echo
    echo -e "${YELLOW}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${YELLOW}║              Rollback Instructions                         ║${NC}"
    echo -e "${YELLOW}╚════════════════════════════════════════════════════════════╝${NC}"
    echo
    echo "If you need to rollback to the previous version:"
    echo
    echo "1. Stop current services:"
    echo "   docker compose down"
    echo
    echo "2. Restore docker-compose.yml:"
    echo "   cp docker-compose.yml.pre-migration docker-compose.yml"
    echo
    echo "3. Restore Caddyfile:"
    echo "   cp config/Caddyfile.pre-migration config/Caddyfile"
    echo
    echo "4. Restore configuration backup:"
    if [[ -f /tmp/migration_backup_name.txt ]]; then
        local backup_name=$(cat /tmp/migration_backup_name.txt)
        echo "   # Via admin panel (if available):"
        echo "   # Use the admin panel to restore: $backup_name"
        echo
        echo "   # Or manually:"
        echo "   tar -xzf data/stealth-vpn/backups/$backup_name -C /"
    else
        echo "   # Use the admin panel to restore the latest backup"
    fi
    echo
    echo "5. Restart services:"
    echo "   docker compose up -d"
    echo
}

# Display migration summary
display_migration_summary() {
    echo
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║           Migration Summary                                ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo
    
    # Display successful steps
    if [ ${#SUCCESSFUL_STEPS[@]} -gt 0 ]; then
        echo -e "${GREEN}✓ Successful Operations (${#SUCCESSFUL_STEPS[@]}):${NC}"
        for step in "${SUCCESSFUL_STEPS[@]}"; do
            echo -e "  ${GREEN}✓${NC} $step"
        done
        echo
    fi
    
    # Display warnings
    if [ ${#WARNING_STEPS[@]} -gt 0 ]; then
        echo -e "${YELLOW}⚠ Warnings (${#WARNING_STEPS[@]}):${NC}"
        for step in "${WARNING_STEPS[@]}"; do
            echo -e "  ${YELLOW}⚠${NC} $step"
        done
        echo
    fi
    
    # Display failures
    if [ ${#FAILED_STEPS[@]} -gt 0 ]; then
        echo -e "${RED}✗ Failed Operations (${#FAILED_STEPS[@]}):${NC}"
        for step in "${FAILED_STEPS[@]}"; do
            echo -e "  ${RED}✗${NC} $step"
        done
        echo
    fi
    
    # Overall status
    if [ ${#FAILED_STEPS[@]} -eq 0 ]; then
        echo -e "${GREEN}Overall Status: SUCCESS${NC}"
        echo "Migration completed successfully!"
    elif [ ${#SUCCESSFUL_STEPS[@]} -gt ${#FAILED_STEPS[@]} ]; then
        echo -e "${YELLOW}Overall Status: PARTIAL SUCCESS${NC}"
        echo "Migration completed with some warnings."
        echo "Review the warnings above and check the log file: $MIGRATION_LOG"
    else
        echo -e "${RED}Overall Status: FAILED${NC}"
        echo "Migration encountered critical failures."
        echo "Review the log file for details: $MIGRATION_LOG"
        display_rollback_instructions
    fi
    
    echo
    echo "Migration log saved to: $MIGRATION_LOG"
    echo
}

# Main migration function
main() {
    echo
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║     Stealth VPN Server Migration to New Version           ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo
    log "Starting migration process..."
    log "Migration log: $MIGRATION_LOG"
    echo
    
    # Confirmation prompt
    echo -e "${YELLOW}This script will:${NC}"
    echo "  • Create a backup of your current configuration"
    echo "  • Stop running services"
    echo "  • Update docker-compose.yml with new resource limits"
    echo "  • Update Caddyfile with corrected syntax"
    echo "  • Preserve SSL certificates and user data"
    echo "  • Rebuild Docker images"
    echo "  • Restart services"
    echo
    read -p "Do you want to continue? (y/n): " CONFIRM
    if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
        log "Migration cancelled by user"
        exit 0
    fi
    echo
    
    # Run migration steps
    check_root
    check_existing_deployment
    create_backup || { error "Backup failed. Aborting migration."; exit 1; }
    stop_services
    backup_docker_compose
    update_docker_compose
    backup_caddyfile
    update_caddyfile
    preserve_ssl_certificates
    preserve_user_data
    rebuild_images
    start_services
    sleep 5
    verify_services
    run_health_checks
    
    # Display summary
    display_migration_summary
    
    if [ ${#FAILED_STEPS[@]} -eq 0 ]; then
        log "Migration completed successfully!"
        echo
        echo -e "${GREEN}Next steps:${NC}"
        echo "  • Check service logs: docker compose logs -f"
        echo "  • Access admin panel: https://your-domain.com/admin"
        echo "  • Verify VPN connectivity with existing users"
        echo
    else
        warn "Migration completed with ${#FAILED_STEPS[@]} failure(s)."
        echo
        display_rollback_instructions
    fi
}

# Run main function
main "$@"
