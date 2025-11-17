#!/bin/bash

# Health check script for Stealth VPN Server
# Verifies that all components are properly configured

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

# Check if required files exist
check_files() {
    log "Checking required files..."
    
    local required_files=(
        "docker-compose.yml"
        "config/Caddyfile"
        "core/interfaces.py"
        "admin-panel/Dockerfile"
        "admin-panel/requirements.txt"
        ".env.example"
    )
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            error "Required file missing: $file"
            return 1
        fi
    done
    
    log "All required files present"
}

# Check directory structure
check_directories() {
    log "Checking directory structure..."
    
    local required_dirs=(
        "data/stealth-vpn/configs"
        "data/stealth-vpn/backups"
        "data/stealth-vpn/configs/wireguard"
        "data/caddy"
        "data/www"
        "admin-panel/templates"
        "admin-panel/static"
    )
    
    for dir in "${required_dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            warn "Directory missing: $dir (will be created automatically)"
            mkdir -p "$dir"
        fi
    done
    
    log "Directory structure verified"
}

# Check Docker and Docker Compose
check_docker() {
    log "Checking Docker installation..."
    
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
        return 1
    fi
    
    if ! docker compose version &> /dev/null; then
        error "Docker Compose v2 is not available"
        return 1
    fi
    
    # Check if user can run Docker commands
    if ! docker ps &> /dev/null; then
        error "Cannot run Docker commands. User may not be in docker group"
        return 1
    fi
    
    log "Docker installation verified"
}

# Validate Docker Compose configuration
validate_compose() {
    log "Validating Docker Compose configuration..."
    
    if ! docker compose config &> /dev/null; then
        error "Docker Compose configuration is invalid"
        return 1
    fi
    
    log "Docker Compose configuration is valid"
}

# Check environment configuration
check_environment() {
    log "Checking environment configuration..."
    
    if [[ ! -f ".env" ]]; then
        warn ".env file not found. Copy from .env.example and configure"
        return 0
    fi
    
    # Check for placeholder values
    if grep -q "your-domain.com" .env; then
        warn ".env contains placeholder domain. Please update with your actual domain"
    fi
    
    if grep -q "change-this-secure-password" .env; then
        warn ".env contains default password. Please update with secure password"
    fi
    
    log "Environment configuration checked"
}

# Check network ports
check_ports() {
    log "Checking required ports..."
    
    local required_ports=(80 443)
    
    for port in "${required_ports[@]}"; do
        if netstat -tuln 2>/dev/null | grep -q ":$port "; then
            warn "Port $port is already in use"
        fi
    done
    
    log "Port check completed"
}

# Main health check function
main() {
    log "Starting Stealth VPN Server health check..."
    echo
    
    check_files
    check_directories
    check_docker
    validate_compose
    check_environment
    check_ports
    
    echo
    log "Health check completed successfully!"
    echo
    echo -e "${BLUE}System Status:${NC}"
    echo "✓ Project structure is properly set up"
    echo "✓ Docker environment is ready"
    echo "✓ Configuration files are present"
    echo
    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Configure .env file with your domain and settings"
    echo "2. Update config/Caddyfile with your domain"
    echo "3. Run: docker compose up -d"
    echo
}

# Run main function
main "$@"