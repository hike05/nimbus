#!/bin/bash

# Stealth VPN Server Installation Script
# Supports Ubuntu/Debian systems

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
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

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root for security reasons"
    fi
}

# Check system requirements
check_system() {
    log "Checking system requirements..."
    
    # Check OS
    if [[ ! -f /etc/debian_version ]] && [[ ! -f /etc/ubuntu_version ]]; then
        error "This script only supports Ubuntu/Debian systems"
    fi
    
    # Check architecture
    ARCH=$(uname -m)
    if [[ "$ARCH" != "x86_64" ]] && [[ "$ARCH" != "aarch64" ]]; then
        warn "Untested architecture: $ARCH. Proceeding anyway..."
    fi
    
    log "System check passed"
}

# Install Docker and Docker Compose
install_docker() {
    log "Installing Docker and Docker Compose..."
    
    # Check if Docker is already installed
    if command -v docker &> /dev/null; then
        log "Docker is already installed"
    else
        # Update package index
        sudo apt-get update
        
        # Install prerequisites
        sudo apt-get install -y \
            apt-transport-https \
            ca-certificates \
            curl \
            gnupg \
            lsb-release
        
        # Add Docker GPG key
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
        
        # Add Docker repository
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
        
        # Install Docker
        sudo apt-get update
        sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
        
        # Add user to docker group
        sudo usermod -aG docker $USER
        
        log "Docker installed successfully"
    fi
    
    # Check if Docker Compose is available
    if ! docker compose version &> /dev/null; then
        error "Docker Compose is not available. Please install Docker Compose v2"
    fi
    
    log "Docker and Docker Compose are ready"
}

# Setup firewall rules
setup_firewall() {
    log "Setting up firewall rules..."
    
    # Check if ufw is installed
    if command -v ufw &> /dev/null; then
        # Allow SSH (important!)
        sudo ufw allow ssh
        
        # Allow HTTP and HTTPS
        sudo ufw allow 80/tcp
        sudo ufw allow 443/tcp
        
        # Enable firewall if not already enabled
        sudo ufw --force enable
        
        log "Firewall configured successfully"
    else
        warn "UFW not found. Please configure firewall manually to allow ports 80 and 443"
    fi
}

# Generate configuration files
generate_config() {
    log "Generating configuration files..."
    
    # Copy environment template if .env doesn't exist
    if [[ ! -f .env ]]; then
        cp .env.example .env
        log "Created .env file from template"
        
        # Prompt for domain
        read -p "Enter your domain name (e.g., example.com): " DOMAIN_INPUT
        if [[ -n "$DOMAIN_INPUT" ]]; then
            sed -i "s/your-domain.com/$DOMAIN_INPUT/g" .env
            log "Domain set to: $DOMAIN_INPUT"
        else
            warn "No domain provided. Please edit .env file manually"
        fi
        
        # Prompt for email
        read -p "Enter your email for Let's Encrypt (e.g., admin@example.com): " EMAIL_INPUT
        if [[ -n "$EMAIL_INPUT" ]]; then
            sed -i "s/admin@your-domain.com/$EMAIL_INPUT/g" .env
            log "Email set to: $EMAIL_INPUT"
        fi
        
        # Generate admin password
        read -s -p "Enter admin panel password (leave empty for random): " ADMIN_PASS_INPUT
        echo
        if [[ -z "$ADMIN_PASS_INPUT" ]]; then
            ADMIN_PASS_INPUT=$(openssl rand -base64 24)
            log "Generated random admin password: $ADMIN_PASS_INPUT"
        fi
        
        # Generate password hash
        if command -v python3 &> /dev/null; then
            ADMIN_PASSWORD_HASH=$(python3 -c "import bcrypt; print(bcrypt.hashpw('$ADMIN_PASS_INPUT'.encode(), bcrypt.gensalt()).decode())")
            sed -i "s|ADMIN_PASSWORD_HASH=|ADMIN_PASSWORD_HASH=$ADMIN_PASSWORD_HASH|" .env
            log "Admin password hash generated"
        else
            warn "Python3 not found. Please run: python3 admin-panel/setup_admin.py <password>"
        fi
        
        # Generate session secret
        SESSION_SECRET=$(openssl rand -hex 32)
        sed -i "s/SESSION_SECRET=/SESSION_SECRET=$SESSION_SECRET/" .env
        log "Session secret generated"
    else
        log ".env file already exists, skipping generation"
    fi
    
    # Set proper permissions
    chmod 600 .env
    
    log "Configuration files generated"
}

# Create data directories
create_directories() {
    log "Creating data directories..."
    
    # Create all necessary directories
    mkdir -p data/stealth-vpn/{configs,backups}
    mkdir -p data/stealth-vpn/configs/{clients,wireguard}
    mkdir -p data/stealth-vpn/logs/{xray,trojan,singbox,wireguard}
    mkdir -p data/caddy/{data,config,certificates}
    mkdir -p data/www/{css,js,api/v1}
    
    # Create initial users.json if it doesn't exist
    if [[ ! -f data/stealth-vpn/configs/users.json ]]; then
        echo '{"users": {}, "server": {}, "admin": {}}' > data/stealth-vpn/configs/users.json
        log "Created initial users.json"
    fi
    
    # Set proper permissions
    chmod -R 755 data/
    chmod 644 data/stealth-vpn/configs/users.json
    
    log "Data directories created"
}

# Initialize configuration templates
init_templates() {
    log "Initializing configuration templates..."
    
    # Generate initial VPN configurations
    if command -v python3 &> /dev/null; then
        # Generate Xray config
        if [[ -f scripts/xray-config-manager.py ]]; then
            python3 scripts/xray-config-manager.py init || warn "Failed to initialize Xray config"
        fi
        
        # Generate Trojan config
        if [[ -f scripts/trojan-config-manager.py ]]; then
            python3 scripts/trojan-config-manager.py init || warn "Failed to initialize Trojan config"
        fi
        
        # Generate Sing-box config
        if [[ -f scripts/singbox-config-manager.py ]]; then
            python3 scripts/singbox-config-manager.py init || warn "Failed to initialize Sing-box config"
        fi
        
        # Generate WireGuard config
        if [[ -f scripts/wireguard-config-manager.py ]]; then
            python3 scripts/wireguard-config-manager.py init || warn "Failed to initialize WireGuard config"
        fi
        
        log "Configuration templates initialized"
    else
        warn "Python3 not found. Skipping template initialization"
    fi
}

# Build Docker images
build_images() {
    log "Building Docker images..."
    
    if ! docker compose build; then
        error "Failed to build Docker images"
    fi
    
    log "Docker images built successfully"
}

# Validate configuration
validate_config() {
    log "Validating configuration..."
    
    # Check if .env file exists and has required variables
    if [[ ! -f .env ]]; then
        error ".env file not found"
    fi
    
    source .env
    
    # Validate required variables
    if [[ -z "$DOMAIN" ]] || [[ "$DOMAIN" == "your-domain.com" ]]; then
        error "DOMAIN not set in .env file"
    fi
    
    if [[ -z "$ADMIN_PASSWORD_HASH" ]]; then
        error "ADMIN_PASSWORD_HASH not set in .env file"
    fi
    
    if [[ -z "$SESSION_SECRET" ]]; then
        error "SESSION_SECRET not set in .env file"
    fi
    
    log "Configuration validation passed"
}

# Start services
start_services() {
    log "Starting services..."
    
    read -p "Do you want to start services now? (y/n): " START_NOW
    if [[ "$START_NOW" =~ ^[Yy]$ ]]; then
        if docker compose up -d; then
            log "Services started successfully"
            
            # Wait for services to be healthy
            log "Waiting for services to become healthy..."
            sleep 10
            
            # Check service status
            docker compose ps
        else
            error "Failed to start services"
        fi
    else
        log "Skipping service start. Run 'docker compose up -d' when ready"
    fi
}

# Display summary
display_summary() {
    source .env 2>/dev/null || true
    
    echo
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║         Stealth VPN Server Installation Complete          ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo
    echo -e "${BLUE}Configuration Summary:${NC}"
    echo "  Domain: ${DOMAIN:-Not set}"
    echo "  Admin Panel: https://${DOMAIN:-your-domain.com}/api/v2/storage/upload"
    echo "  Admin Username: ${ADMIN_USERNAME:-admin}"
    echo
    echo -e "${BLUE}Service Management:${NC}"
    echo "  Start services:   docker compose up -d"
    echo "  Stop services:    docker compose down"
    echo "  View logs:        docker compose logs -f"
    echo "  Restart service:  docker compose restart <service>"
    echo "  Service status:   docker compose ps"
    echo
    echo -e "${BLUE}Utility Scripts:${NC}"
    echo "  Health check:     ./scripts/health-check.sh"
    echo "  Add user:         python3 scripts/xray-config-manager.py add-user <username>"
    echo "  List users:       python3 scripts/xray-config-manager.py list-users"
    echo "  Generate config:  python3 scripts/generate-endpoints.py"
    echo
    echo -e "${YELLOW}Important Notes:${NC}"
    echo "  • Ensure your domain DNS points to this server's IP"
    echo "  • Ports 80 and 443 must be accessible from the internet"
    echo "  • SSL certificates will be obtained automatically via Let's Encrypt"
    echo "  • Check logs if services fail to start: docker compose logs -f"
    echo
    echo -e "${BLUE}Documentation:${NC}"
    echo "  Admin Panel:  docs/ADMIN_PANEL_USAGE.md"
    echo "  WireGuard:    docs/WIREGUARD_USAGE.md"
    echo "  Sing-box:     docs/SINGBOX_USAGE.md"
    echo
}

# Main installation function
main() {
    log "Starting Stealth VPN Server installation..."
    echo
    
    check_root
    check_system
    install_docker
    setup_firewall
    generate_config
    create_directories
    init_templates
    validate_config
    build_images
    start_services
    display_summary
    
    log "Installation completed successfully!"
}

# Run main function
main "$@"