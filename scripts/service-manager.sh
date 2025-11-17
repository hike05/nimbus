#!/bin/bash

# Stealth VPN Server Service Manager
# Utility for managing Docker services

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

# Check if Docker Compose is available
check_docker() {
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
    fi
    
    if ! docker compose version &> /dev/null; then
        error "Docker Compose is not available"
    fi
}

# Start all services
start_all() {
    log "Starting all services..."
    docker compose up -d
    log "All services started"
    show_status
}

# Stop all services
stop_all() {
    log "Stopping all services..."
    docker compose down
    log "All services stopped"
}

# Restart all services
restart_all() {
    log "Restarting all services..."
    docker compose restart
    log "All services restarted"
    show_status
}

# Start specific service
start_service() {
    local service=$1
    if [[ -z "$service" ]]; then
        error "Service name required"
    fi
    
    log "Starting service: $service"
    docker compose up -d "$service"
    log "Service $service started"
}

# Stop specific service
stop_service() {
    local service=$1
    if [[ -z "$service" ]]; then
        error "Service name required"
    fi
    
    log "Stopping service: $service"
    docker compose stop "$service"
    log "Service $service stopped"
}

# Restart specific service
restart_service() {
    local service=$1
    if [[ -z "$service" ]]; then
        error "Service name required"
    fi
    
    log "Restarting service: $service"
    docker compose restart "$service"
    log "Service $service restarted"
}

# Show service status
show_status() {
    echo
    echo -e "${BLUE}Service Status:${NC}"
    docker compose ps
    echo
}

# Show service logs
show_logs() {
    local service=$1
    local lines=${2:-100}
    
    if [[ -z "$service" ]]; then
        log "Showing logs for all services (last $lines lines)"
        docker compose logs --tail="$lines" -f
    else
        log "Showing logs for service: $service (last $lines lines)"
        docker compose logs --tail="$lines" -f "$service"
    fi
}

# Rebuild service
rebuild_service() {
    local service=$1
    if [[ -z "$service" ]]; then
        error "Service name required"
    fi
    
    log "Rebuilding service: $service"
    docker compose build --no-cache "$service"
    docker compose up -d "$service"
    log "Service $service rebuilt and restarted"
}

# Rebuild all services
rebuild_all() {
    log "Rebuilding all services..."
    docker compose build --no-cache
    docker compose up -d
    log "All services rebuilt and restarted"
    show_status
}

# Health check
health_check() {
    log "Running health checks..."
    
    if [[ -f scripts/health-check.sh ]]; then
        bash scripts/health-check.sh
    else
        warn "Health check script not found"
        show_status
    fi
}

# Clean up unused resources
cleanup() {
    log "Cleaning up unused Docker resources..."
    
    # Remove stopped containers
    docker container prune -f
    
    # Remove unused images
    docker image prune -f
    
    # Remove unused volumes (be careful!)
    read -p "Remove unused volumes? This may delete data! (y/n): " REMOVE_VOLUMES
    if [[ "$REMOVE_VOLUMES" =~ ^[Yy]$ ]]; then
        docker volume prune -f
    fi
    
    # Remove unused networks
    docker network prune -f
    
    log "Cleanup completed"
}

# Backup data
backup_data() {
    log "Creating backup..."
    
    local backup_dir="backups/$(date +'%Y%m%d_%H%M%S')"
    mkdir -p "$backup_dir"
    
    # Backup configuration files
    cp -r data/stealth-vpn/configs "$backup_dir/"
    cp .env "$backup_dir/" 2>/dev/null || true
    
    # Create tarball
    tar -czf "$backup_dir.tar.gz" "$backup_dir"
    rm -rf "$backup_dir"
    
    log "Backup created: $backup_dir.tar.gz"
}

# Restore from backup
restore_data() {
    local backup_file=$1
    
    if [[ -z "$backup_file" ]]; then
        error "Backup file required"
    fi
    
    if [[ ! -f "$backup_file" ]]; then
        error "Backup file not found: $backup_file"
    fi
    
    log "Restoring from backup: $backup_file"
    
    # Stop services
    docker compose down
    
    # Extract backup
    tar -xzf "$backup_file" -C .
    
    # Copy files
    local backup_dir=$(basename "$backup_file" .tar.gz)
    cp -r "$backup_dir/configs/"* data/stealth-vpn/configs/
    cp "$backup_dir/.env" . 2>/dev/null || true
    
    # Cleanup
    rm -rf "$backup_dir"
    
    # Start services
    docker compose up -d
    
    log "Restore completed"
}

# Show usage
usage() {
    echo "Stealth VPN Server Service Manager"
    echo
    echo "Usage: $0 <command> [options]"
    echo
    echo "Commands:"
    echo "  start [service]       Start all services or specific service"
    echo "  stop [service]        Stop all services or specific service"
    echo "  restart [service]     Restart all services or specific service"
    echo "  status                Show service status"
    echo "  logs [service] [n]    Show logs (default: 100 lines)"
    echo "  rebuild [service]     Rebuild and restart service(s)"
    echo "  health                Run health checks"
    echo "  cleanup               Clean up unused Docker resources"
    echo "  backup                Create backup of configuration"
    echo "  restore <file>        Restore from backup file"
    echo
    echo "Services:"
    echo "  caddy, xray, trojan, singbox, wireguard, admin"
    echo
    echo "Examples:"
    echo "  $0 start              # Start all services"
    echo "  $0 restart xray       # Restart Xray service"
    echo "  $0 logs caddy 50      # Show last 50 lines of Caddy logs"
    echo "  $0 rebuild admin      # Rebuild admin panel"
    echo
}

# Main function
main() {
    check_docker
    
    local command=$1
    shift || true
    
    case "$command" in
        start)
            if [[ -n "$1" ]]; then
                start_service "$1"
            else
                start_all
            fi
            ;;
        stop)
            if [[ -n "$1" ]]; then
                stop_service "$1"
            else
                stop_all
            fi
            ;;
        restart)
            if [[ -n "$1" ]]; then
                restart_service "$1"
            else
                restart_all
            fi
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs "$1" "$2"
            ;;
        rebuild)
            if [[ -n "$1" ]]; then
                rebuild_service "$1"
            else
                rebuild_all
            fi
            ;;
        health)
            health_check
            ;;
        cleanup)
            cleanup
            ;;
        backup)
            backup_data
            ;;
        restore)
            restore_data "$1"
            ;;
        *)
            usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
