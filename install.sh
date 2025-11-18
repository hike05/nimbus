#!/bin/bash

# Multi-Protocol Proxy Server Installation Script
# Supports Ubuntu/Debian systems

# Don't exit on error - we'll handle errors gracefully
set +e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Installation log file
INSTALL_LOG="install_$(date +'%Y%m%d_%H%M%S').log"

# Track installation status
declare -a SUCCESSFUL_STEPS=()
declare -a FAILED_STEPS=()
declare -a WARNING_STEPS=()

# Logging functions with file output
log() {
    local timestamp=$(date +'%Y-%m-%d %H:%M:%S')
    local message="[INFO] $1"
    echo -e "${GREEN}[$timestamp] $message${NC}"
    echo "[$timestamp] $message" >> "$INSTALL_LOG"
}

warn() {
    local timestamp=$(date +'%Y-%m-%d %H:%M:%S')
    local message="[WARNING] $1"
    echo -e "${YELLOW}[$timestamp] $message${NC}"
    echo "[$timestamp] $message" >> "$INSTALL_LOG"
}

error() {
    local timestamp=$(date +'%Y-%m-%d %H:%M:%S')
    local message="[ERROR] $1"
    local context="${2:-Unknown operation}"
    echo -e "${RED}[$timestamp] $message${NC}"
    echo "[$timestamp] [ERROR] $message" >> "$INSTALL_LOG"
    echo "[$timestamp] [CONTEXT] Operation: $context" >> "$INSTALL_LOG"
    echo "[$timestamp] [SYSTEM] $(uname -a)" >> "$INSTALL_LOG"
    echo "[$timestamp] Installation failed. Check $INSTALL_LOG for details." >> "$INSTALL_LOG"
    
    # Trigger rollback
    rollback_installation "$message" "$context"
    exit 1
}

success() {
    local timestamp=$(date +'%Y-%m-%d %H:%M:%S')
    local message="[SUCCESS] $1"
    echo -e "${GREEN}[$timestamp] ✓ $message${NC}"
    echo "[$timestamp] $message" >> "$INSTALL_LOG"
}

# Progress tracking variables
TOTAL_STEPS=12
CURRENT_STEP=0
STEP_START_TIME=0

# Display progress indicator
show_progress() {
    local step_name="$1"
    ((CURRENT_STEP++))
    
    local percentage=$((CURRENT_STEP * 100 / TOTAL_STEPS))
    local elapsed_total=$(($(date +%s) - INSTALL_START_TIME))
    local estimated_total=$((elapsed_total * TOTAL_STEPS / CURRENT_STEP))
    local remaining=$((estimated_total - elapsed_total))
    
    # Format time remaining
    local remaining_min=$((remaining / 60))
    local remaining_sec=$((remaining % 60))
    
    echo
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  Step $CURRENT_STEP/$TOTAL_STEPS - ${percentage}% Complete$(printf '%*s' $((42 - ${#CURRENT_STEP} - ${#TOTAL_STEPS} - ${#percentage})) '')║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo -e "${GREEN}▶ $step_name${NC}"
    
    if [[ $CURRENT_STEP -gt 1 ]] && [[ $remaining -gt 0 ]]; then
        echo -e "${YELLOW}  Estimated time remaining: ${remaining_min}m ${remaining_sec}s${NC}"
    fi
    echo
    
    STEP_START_TIME=$(date +%s)
}

# Track step completion
track_success() {
    SUCCESSFUL_STEPS+=("$1")
    success "$1"
    
    # Show step completion time
    if [[ $STEP_START_TIME -gt 0 ]]; then
        local step_duration=$(($(date +%s) - STEP_START_TIME))
        log "  Completed in ${step_duration}s"
    fi
}

track_failure() {
    FAILED_STEPS+=("$1")
    error "$1"
}

track_warning() {
    WARNING_STEPS+=("$1")
    warn "$1"
}

# Non-fatal error - log but continue
soft_error() {
    local timestamp=$(date +'%Y-%m-%d %H:%M:%S')
    local message="[ERROR] $1"
    local context="${2:-Unknown operation}"
    echo -e "${RED}[$timestamp] $message${NC}"
    echo "[$timestamp] [ERROR] $message" >> "$INSTALL_LOG"
    echo "[$timestamp] [CONTEXT] Operation: $context" >> "$INSTALL_LOG"
    FAILED_STEPS+=("$1")
}

# Log comprehensive system information
log_system_info() {
    local timestamp=$(date +'%Y-%m-%d %H:%M:%S')
    
    log "Logging system information..."
    
    # Log to file with detailed system info
    cat >> "$INSTALL_LOG" <<EOF

════════════════════════════════════════════════════════════
SYSTEM INFORMATION
════════════════════════════════════════════════════════════
Timestamp: $timestamp

Operating System:
$(cat /etc/os-release 2>/dev/null || echo "OS information not available")

Kernel:
$(uname -a)

CPU Information:
  Cores: $(nproc 2>/dev/null || echo "unknown")
  Model: $(grep "model name" /proc/cpuinfo 2>/dev/null | head -1 | cut -d: -f2 | xargs || echo "unknown")

Memory Information:
$(free -h 2>/dev/null || echo "Memory information not available")

Disk Space:
$(df -h . 2>/dev/null || echo "Disk information not available")

Network Configuration:
  Hostname: $(hostname 2>/dev/null || echo "unknown")
  Public IP: $(curl -s --max-time 5 ifconfig.me 2>/dev/null || echo "Could not determine")

Docker Version:
$(docker --version 2>/dev/null || echo "Docker not installed")

Docker Compose Version:
$(docker compose version 2>/dev/null || echo "Docker Compose not installed")

Python Version:
$(python3 --version 2>/dev/null || echo "Python3 not installed")

════════════════════════════════════════════════════════════

EOF
    
    log "System information logged to $INSTALL_LOG"
}

# Rollback installation on error
rollback_installation() {
    local error_message="$1"
    local error_context="${2:-Unknown operation}"
    local timestamp=$(date +'%Y-%m-%d %H:%M:%S')
    
    echo
    echo -e "${RED}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║         Installation Failed - Rolling Back                 ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════════╝${NC}"
    echo
    echo -e "${RED}Error:${NC} $error_message"
    echo -e "${YELLOW}Context:${NC} $error_context"
    echo
    
    log "Starting rollback procedure..."
    echo "[$timestamp] [ROLLBACK] Starting rollback procedure" >> "$INSTALL_LOG"
    echo "[$timestamp] [ROLLBACK] Error: $error_message" >> "$INSTALL_LOG"
    echo "[$timestamp] [ROLLBACK] Context: $error_context" >> "$INSTALL_LOG"
    
    # 1. Stop all running containers
    log "Stopping all containers..."
    echo "[$timestamp] [ROLLBACK] Stopping all containers" >> "$INSTALL_LOG"
    
    local compose_file=${COMPOSE_FILE:-docker-compose.yml}
    if [[ -f "$compose_file" ]]; then
        if docker compose -f "$compose_file" down 2>&1 | tee -a "$INSTALL_LOG"; then
            log "  ✓ Containers stopped successfully"
            echo "[$timestamp] [ROLLBACK] Containers stopped successfully" >> "$INSTALL_LOG"
        else
            warn "  ⚠ Failed to stop some containers"
            echo "[$timestamp] [ROLLBACK] Failed to stop some containers" >> "$INSTALL_LOG"
        fi
    else
        log "  ℹ No compose file found, skipping container cleanup"
    fi
    
    # Also try the other compose file if it exists
    if [[ "$compose_file" != "docker-compose.minimal.yml" ]] && [[ -f "docker-compose.minimal.yml" ]]; then
        docker compose -f docker-compose.minimal.yml down 2>&1 | tee -a "$INSTALL_LOG" || true
    fi
    
    # 2. Remove partially generated configuration files
    log "Cleaning up partially generated configurations..."
    echo "[$timestamp] [ROLLBACK] Cleaning up configurations" >> "$INSTALL_LOG"
    
    local configs_to_remove=(
        "data/proxy/configs/xray.json"
        "data/proxy/configs/trojan.json"
        "data/proxy/configs/singbox.json"
        "data/proxy/configs/wireguard/wg0.conf"
    )
    
    for config_file in "${configs_to_remove[@]}"; do
        if [[ -f "$config_file" ]]; then
            if rm -f "$config_file" 2>/dev/null; then
                log "  ✓ Removed: $config_file"
                echo "[$timestamp] [ROLLBACK] Removed: $config_file" >> "$INSTALL_LOG"
            else
                warn "  ⚠ Failed to remove: $config_file"
                echo "[$timestamp] [ROLLBACK] Failed to remove: $config_file" >> "$INSTALL_LOG"
            fi
        fi
    done
    
    # 3. Preserve .env file but mark installation as failed
    if [[ -f .env ]]; then
        log "Preserving .env file with failure marker..."
        echo "[$timestamp] [ROLLBACK] Marking .env as failed installation" >> "$INSTALL_LOG"
        
        # Add failure marker to .env
        if ! grep -q "INSTALLATION_FAILED" .env; then
            cat >> .env <<EOF

# ============================================================================
# INSTALLATION STATUS
# ============================================================================
INSTALLATION_FAILED=true
INSTALLATION_FAILED_AT=$timestamp
INSTALLATION_ERROR="$error_message"
INSTALLATION_ERROR_CONTEXT="$error_context"
EOF
            log "  ✓ .env file marked as failed installation"
            echo "[$timestamp] [ROLLBACK] .env file marked as failed" >> "$INSTALL_LOG"
        fi
    fi
    
    # 4. Remove Docker images if they were built
    log "Cleaning up Docker images..."
    echo "[$timestamp] [ROLLBACK] Cleaning up Docker images" >> "$INSTALL_LOG"
    
    local images_to_remove=(
        "stealth-vpn-server-admin"
        "stealth-vpn-server-xray"
        "stealth-vpn-server-trojan"
        "stealth-vpn-server-singbox"
        "stealth-vpn-server-wireguard"
    )
    
    for image in "${images_to_remove[@]}"; do
        if docker images | grep -q "$image"; then
            if docker rmi "$image" 2>&1 | tee -a "$INSTALL_LOG"; then
                log "  ✓ Removed image: $image"
                echo "[$timestamp] [ROLLBACK] Removed image: $image" >> "$INSTALL_LOG"
            else
                warn "  ⚠ Failed to remove image: $image"
                echo "[$timestamp] [ROLLBACK] Failed to remove image: $image" >> "$INSTALL_LOG"
            fi
        fi
    done
    
    # 5. Log rollback completion
    echo "[$timestamp] [ROLLBACK] Rollback procedure completed" >> "$INSTALL_LOG"
    log "Rollback procedure completed"
    
    # 6. Display troubleshooting guidance
    display_error_troubleshooting "$error_message" "$error_context"
    
    echo
    echo -e "${YELLOW}Installation log saved to: $INSTALL_LOG${NC}"
    echo "Review the log for detailed error information."
    echo
}

# Display error troubleshooting guidance
display_error_troubleshooting() {
    local error_message="$1"
    local error_context="$2"
    
    echo
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║              Troubleshooting Guidance                      ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo
    
    # Provide context-specific troubleshooting
    case "$error_context" in
        *"Docker"*|*"docker"*)
            echo -e "${YELLOW}Docker-related error detected${NC}"
            echo
            echo "Common solutions:"
            echo "  1. Ensure Docker is installed and running:"
            echo "     sudo systemctl status docker"
            echo
            echo "  2. Verify Docker Compose is available:"
            echo "     docker compose version"
            echo
            echo "  3. Check Docker permissions:"
            echo "     sudo usermod -aG docker \$USER"
            echo "     newgrp docker"
            echo
            echo "  4. Restart Docker service:"
            echo "     sudo systemctl restart docker"
            echo
            ;;
        *"DNS"*|*"domain"*)
            echo -e "${YELLOW}DNS-related error detected${NC}"
            echo
            echo "Common solutions:"
            echo "  1. Verify domain DNS configuration:"
            echo "     dig \$DOMAIN +short"
            echo
            echo "  2. Ensure domain points to server IP:"
            echo "     curl ifconfig.me"
            echo
            echo "  3. Wait for DNS propagation (5-30 minutes)"
            echo
            echo "  4. Check DNS provider settings"
            echo
            ;;
        *"port"*|*"Port"*)
            echo -e "${YELLOW}Port-related error detected${NC}"
            echo
            echo "Common solutions:"
            echo "  1. Check if ports are in use:"
            echo "     sudo lsof -i :80"
            echo "     sudo lsof -i :443"
            echo
            echo "  2. Configure firewall:"
            echo "     sudo ufw allow 80/tcp"
            echo "     sudo ufw allow 443/tcp"
            echo
            echo "  3. Check cloud provider security groups"
            echo
            ;;
        *"certificate"*|*"SSL"*|*"TLS"*)
            echo -e "${YELLOW}SSL/Certificate error detected${NC}"
            echo
            echo "Common solutions:"
            echo "  1. Verify DNS is configured correctly"
            echo
            echo "  2. Ensure ports 80 and 443 are accessible"
            echo
            echo "  3. Check Let's Encrypt rate limits:"
            echo "     https://letsencrypt.org/docs/rate-limits/"
            echo
            echo "  4. Review Caddy logs:"
            echo "     docker compose logs gateway"
            echo
            ;;
        *)
            echo -e "${YELLOW}General troubleshooting steps:${NC}"
            echo
            echo "  1. Review the installation log:"
            echo "     cat $INSTALL_LOG"
            echo
            echo "  2. Check system requirements:"
            echo "     • Ubuntu/Debian OS"
            echo "     • Docker and Docker Compose installed"
            echo "     • Ports 80 and 443 accessible"
            echo "     • Domain DNS configured"
            echo
            echo "  3. Verify system resources:"
            echo "     • At least 2 CPU cores (recommended)"
            echo "     • At least 2 GB RAM"
            echo "     • At least 10 GB disk space"
            echo
            echo "  4. Check Docker status:"
            echo "     sudo systemctl status docker"
            echo "     docker compose ps"
            echo
            ;;
    esac
    
    echo -e "${BLUE}Next steps:${NC}"
    echo "  1. Fix the issue based on guidance above"
    echo "  2. Remove the failure marker from .env:"
    echo "     sed -i '/INSTALLATION_FAILED/d' .env"
    echo "  3. Re-run the installation script:"
    echo "     ./install.sh"
    echo
    echo -e "${YELLOW}Need help?${NC}"
    echo "  • Check documentation: README.md"
    echo "  • Review logs: $INSTALL_LOG"
    echo "  • Search for similar issues in project repository"
    echo
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root for security reasons" "Root user check"
    fi
}

# Check if required commands exist
check_commands() {
    log "Checking for required commands..."
    
    local missing_commands=()
    
    # Check for essential commands
    if ! command -v docker &> /dev/null; then
        missing_commands+=("docker")
    fi
    
    if ! command -v docker &> /dev/null || ! docker compose version &> /dev/null; then
        if ! command -v docker-compose &> /dev/null; then
            missing_commands+=("docker-compose")
        fi
    fi
    
    # Check for optional but recommended commands
    local optional_missing=()
    
    if ! command -v python3 &> /dev/null; then
        optional_missing+=("python3")
    fi
    
    if ! command -v openssl &> /dev/null; then
        optional_missing+=("openssl")
    fi
    
    if ! command -v curl &> /dev/null; then
        optional_missing+=("curl")
    fi
    
    # Report missing essential commands
    if [ ${#missing_commands[@]} -gt 0 ]; then
        error "Missing required commands: ${missing_commands[*]}" "Command availability check"
        echo
        echo -e "${YELLOW}Installation instructions:${NC}"
        echo
        
        for cmd in "${missing_commands[@]}"; do
            case $cmd in
                docker)
                    echo -e "${BLUE}Docker:${NC}"
                    echo "  curl -fsSL https://get.docker.com -o get-docker.sh"
                    echo "  sudo sh get-docker.sh"
                    echo "  sudo usermod -aG docker \$USER"
                    echo "  newgrp docker"
                    echo
                    ;;
                docker-compose)
                    echo -e "${BLUE}Docker Compose:${NC}"
                    echo "  sudo apt-get update"
                    echo "  sudo apt-get install docker-compose-plugin"
                    echo "  # Or for standalone docker-compose:"
                    echo "  sudo curl -L \"https://github.com/docker/compose/releases/latest/download/docker-compose-\$(uname -s)-\$(uname -m)\" -o /usr/local/bin/docker-compose"
                    echo "  sudo chmod +x /usr/local/bin/docker-compose"
                    echo
                    ;;
            esac
        done
        
        echo "After installing the missing commands, run this script again."
        exit 1
    fi
    
    # Report missing optional commands as warnings
    if [ ${#optional_missing[@]} -gt 0 ]; then
        warn "Missing optional commands: ${optional_missing[*]}"
        echo
        echo -e "${YELLOW}These commands are recommended but not required:${NC}"
        
        for cmd in "${optional_missing[@]}"; do
            case $cmd in
                python3)
                    echo "  python3: sudo apt-get install python3 python3-pip"
                    ;;
                openssl)
                    echo "  openssl: sudo apt-get install openssl"
                    ;;
                curl)
                    echo "  curl: sudo apt-get install curl"
                    ;;
            esac
        done
        echo
        
        read -p "Continue without optional commands? (y/n): " CONTINUE
        if [[ ! "$CONTINUE" =~ ^[Yy]$ ]]; then
            log "Installation cancelled by user"
            exit 0
        fi
    else
        success "All required commands are available"
    fi
}

# Check system requirements
check_system() {
    log "Checking system requirements..."
    
    # Check OS
    if [[ ! -f /etc/debian_version ]] && [[ ! -f /etc/ubuntu_version ]]; then
        error "This script only supports Ubuntu/Debian systems" "Operating system check"
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
        error "Docker Compose is not available. Please install Docker Compose v2" "Docker Compose installation check"
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

# Validate domain name format
validate_domain() {
    local domain="$1"
    
    # Check if domain is empty
    if [[ -z "$domain" ]]; then
        return 1
    fi
    
    # Check for spaces
    if [[ "$domain" =~ [[:space:]] ]]; then
        return 1
    fi
    
    # Check basic domain format (alphanumeric, dots, hyphens)
    if [[ ! "$domain" =~ ^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$ ]]; then
        return 1
    fi
    
    # Check if domain has at least one dot (e.g., example.com)
    if [[ ! "$domain" =~ \. ]]; then
        return 1
    fi
    
    return 0
}

# Validate email format
validate_email() {
    local email="$1"
    
    # Check if email is empty
    if [[ -z "$email" ]]; then
        return 1
    fi
    
    # Check for spaces
    if [[ "$email" =~ [[:space:]] ]]; then
        return 1
    fi
    
    # Check basic email format
    if [[ ! "$email" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
        return 1
    fi
    
    return 0
}

# Generate configuration files
generate_config() {
    log "Generating configuration files..."
    
    # Copy environment template if .env doesn't exist
    if [[ ! -f .env ]]; then
        cp .env.example .env
        log "Created .env file from template"
        
        # Prompt for domain with validation
        local domain_valid=false
        local domain_attempts=0
        local max_attempts=3
        
        while [[ "$domain_valid" == "false" ]] && [[ $domain_attempts -lt $max_attempts ]]; do
            echo
            echo -e "${BLUE}Domain Configuration${NC}"
            echo "Enter your domain name (e.g., example.com or vpn.example.com)"
            echo "This domain must point to this server's IP address."
            read -p "Domain: " DOMAIN_INPUT
            
            if validate_domain "$DOMAIN_INPUT"; then
                sed -i "s/your-domain.com/$DOMAIN_INPUT/g" .env
                log "Domain set to: $DOMAIN_INPUT"
                domain_valid=true
            else
                ((domain_attempts++))
                echo -e "${RED}Invalid domain format.${NC}"
                echo "Domain must:"
                echo "  • Not contain spaces"
                echo "  • Use only letters, numbers, dots, and hyphens"
                echo "  • Have at least one dot (e.g., example.com)"
                echo "  • Follow standard domain naming conventions"
                
                if [[ $domain_attempts -lt $max_attempts ]]; then
                    echo
                    echo "Please try again (attempt $domain_attempts of $max_attempts)"
                else
                    error "Failed to provide valid domain after $max_attempts attempts" "Domain validation"
                fi
            fi
        done
        
        # Prompt for email with validation
        local email_valid=false
        local email_attempts=0
        
        while [[ "$email_valid" == "false" ]] && [[ $email_attempts -lt $max_attempts ]]; do
            echo
            echo -e "${BLUE}Email Configuration${NC}"
            echo "Enter your email address for Let's Encrypt certificate notifications."
            echo "This email will receive expiration warnings and important updates."
            read -p "Email: " EMAIL_INPUT
            
            if validate_email "$EMAIL_INPUT"; then
                sed -i "s/admin@your-domain.com/$EMAIL_INPUT/g" .env
                log "Email set to: $EMAIL_INPUT"
                email_valid=true
            else
                ((email_attempts++))
                echo -e "${RED}Invalid email format.${NC}"
                echo "Email must:"
                echo "  • Not contain spaces"
                echo "  • Have @ symbol"
                echo "  • Have valid domain after @"
                echo "  • Follow standard email format (user@domain.com)"
                
                if [[ $email_attempts -lt $max_attempts ]]; then
                    echo
                    echo "Please try again (attempt $email_attempts of $max_attempts)"
                else
                    error "Failed to provide valid email after $max_attempts attempts" "Email validation"
                fi
            fi
        done
        
        # Display configuration summary and ask for confirmation
        echo
        echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${BLUE}║         Installation Configuration Summary                 ║${NC}"
        echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
        echo
        echo -e "${GREEN}Domain:${NC}  $DOMAIN_INPUT"
        echo -e "${GREEN}Email:${NC}   $EMAIL_INPUT"
        echo
        echo -e "${YELLOW}Estimated Installation Time:${NC} 3-5 minutes"
        echo
        echo "The installation will:"
        echo "  1. Detect system resources (CPU, RAM)"
        echo "  2. Generate secure passwords and configurations"
        echo "  3. Create first user account automatically"
        echo "  4. Build and start Docker containers"
        echo "  5. Acquire SSL certificates from Let's Encrypt"
        echo "  6. Verify all services are healthy"
        echo
        echo -e "${YELLOW}Requirements:${NC}"
        echo "  • Domain DNS must point to this server"
        echo "  • Ports 80 and 443 must be accessible"
        echo "  • At least 2 GB RAM and 2 CPU cores recommended"
        echo
        
        read -p "Continue with installation? (y/n): " CONFIRM_INSTALL
        if [[ ! "$CONFIRM_INSTALL" =~ ^[Yy]$ ]]; then
            log "Installation cancelled by user"
            echo
            echo "Installation cancelled. You can restart by running:"
            echo "  ./install.sh"
            echo
            exit 0
        fi
        
        log "Installation confirmed by user"
        echo
        
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
        
        # Add resource limits if they were calculated
        if [[ -n "$CPU_LIMIT_PER_SERVICE" ]] && [[ -n "$RAM_LIMIT_PER_SERVICE" ]]; then
            log "Adding calculated resource limits to .env..."
            
            # Add resource configuration section if not present
            if ! grep -q "RESOURCE LIMITS" .env; then
                cat >> .env <<EOF

# ============================================================================
# RESOURCE LIMITS (Auto-detected)
# ============================================================================

# Detected System Resources
CPU_CORES=$DETECTED_CPU_CORES
RAM_MB=$DETECTED_MEMORY_MB

# Calculated Resource Limits per Service
# Based on 80% CPU and 70% RAM allocation across all services
CPU_LIMIT_PER_SERVICE=$CPU_LIMIT_PER_SERVICE
RAM_LIMIT_PER_SERVICE=$RAM_LIMIT_PER_SERVICE
EOF
                log "Resource limits added to .env"
            else
                log "Resource limits section already exists in .env"
            fi
        fi
    else
        log ".env file already exists, skipping generation"
    fi
    
    # Set proper permissions
    chmod 600 .env
    
    log "Configuration files generated"
}

# Create data directories
create_directories() {
    local timestamp=$(date +'%Y-%m-%d %H:%M:%S')
    log "Creating data directories..."
    echo "[$timestamp] [OPERATION] Creating data directory structure" >> "$INSTALL_LOG"
    
    # Create all necessary directories
    echo "[$timestamp] [OPERATION] Creating proxy directories" >> "$INSTALL_LOG"
    mkdir -p data/proxy/{configs,backups} 2>&1 | tee -a "$INSTALL_LOG"
    mkdir -p data/proxy/configs/{clients,wireguard} 2>&1 | tee -a "$INSTALL_LOG"
    mkdir -p data/proxy/logs/{xray,trojan,singbox,wireguard,caddy,admin,system} 2>&1 | tee -a "$INSTALL_LOG"
    mkdir -p data/caddy/{data,config,certificates} 2>&1 | tee -a "$INSTALL_LOG"
    mkdir -p data/www/{css,js,api/v1} 2>&1 | tee -a "$INSTALL_LOG"
    
    echo "[$timestamp] [SUCCESS] All directories created successfully" >> "$INSTALL_LOG"
    
    # Create initial users.json if it doesn't exist
    if [[ ! -f data/proxy/configs/users.json ]]; then
        echo '{"users": {}, "server": {}, "admin": {}}' > data/proxy/configs/users.json
        log "Created initial users.json"
    fi
    
    # Set proper directory permissions (755 for directories)
    log "Setting directory permissions to 755..."
    find data/ -type d -exec chmod 755 {} \;
    
    # Set proper file permissions (644 for files)
    log "Setting file permissions to 644..."
    find data/ -type f -exec chmod 644 {} \;
    
    # Make backup directory writable for containers (777)
    log "Setting backup directory to 777 for container write access..."
    chmod 777 data/proxy/backups
    
    # Make log directories writable for proxy service users (755 is sufficient with proper ownership)
    log "Setting log directories to 755..."
    chmod 755 data/proxy/logs
    chmod 755 data/proxy/logs/{xray,trojan,singbox,wireguard,caddy,admin,system}
    
    # Set ownership to current user (or UID 1000 if running with sudo)
    log "Setting ownership for data directories..."
    if [[ $EUID -eq 0 ]]; then
        # Running as root - set to UID 1000
        chown -R 1000:1000 data/proxy
        log "Set ownership to UID 1000 for admin data directory"
    else
        # Running as regular user - ensure current user owns the files
        CURRENT_USER=$(whoami)
        CURRENT_UID=$(id -u)
        CURRENT_GID=$(id -g)
        
        # Only change ownership if not already owned by current user
        if [[ "$(stat -c '%u' data/proxy 2>/dev/null || echo '0')" != "$CURRENT_UID" ]]; then
            log "Setting ownership to $CURRENT_USER (UID: $CURRENT_UID)..."
            chown -R $CURRENT_UID:$CURRENT_GID data/proxy
        fi
    fi
    
    log "Data directories created with proper permissions (755 for dirs, 644 for files)"
    log "Backup directory set to 777 for container write access"
    log "Log directories set to 755 with proper ownership"
}

# Generate Xray base configuration
generate_xray_config() {
    local config_file="data/proxy/configs/xray.json"
    
    # Skip if config already exists
    if [[ -f "$config_file" ]]; then
        log "Xray config already exists, skipping generation"
        return 0
    fi
    
    log "Generating base Xray configuration..."
    
    # Ensure directory exists
    local timestamp=$(date +'%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [OPERATION] Creating Xray config directory: $(dirname "$config_file")" >> "$INSTALL_LOG"
    
    mkdir -p "$(dirname "$config_file")" 2>/dev/null || {
        echo "[$timestamp] [ERROR] Failed to create directory: $(dirname "$config_file")" >> "$INSTALL_LOG"
        echo "[$timestamp] [ERROR] Permissions: $(ls -ld data/proxy/configs 2>&1)" >> "$INSTALL_LOG"
        soft_error "Failed to create Xray config directory" "Xray configuration generation"
        return 1
    }
    
    cat > "$config_file" <<'EOF'
{
  "log": {
    "loglevel": "warning",
    "access": "/var/log/xray/access.log",
    "error": "/var/log/xray/error.log"
  },
  "inbounds": [
    {
      "tag": "vless-xtls-vision",
      "port": 8001,
      "listen": "0.0.0.0",
      "protocol": "vless",
      "settings": {
        "clients": [],
        "decryption": "none"
      },
      "streamSettings": {
        "network": "tcp",
        "security": "none"
      },
      "sniffing": {
        "enabled": true,
        "destOverride": ["http", "tls"]
      }
    },
    {
      "tag": "vless-ws",
      "port": 8004,
      "listen": "0.0.0.0",
      "protocol": "vless",
      "settings": {
        "clients": [],
        "decryption": "none"
      },
      "streamSettings": {
        "network": "ws",
        "wsSettings": {
          "path": "/xray-ws"
        }
      },
      "sniffing": {
        "enabled": true,
        "destOverride": ["http", "tls"]
      }
    }
  ],
  "outbounds": [
    {
      "tag": "direct",
      "protocol": "freedom",
      "settings": {}
    },
    {
      "tag": "blocked",
      "protocol": "blackhole",
      "settings": {
        "response": {
          "type": "http"
        }
      }
    }
  ],
  "routing": {
    "domainStrategy": "IPIfNonMatch",
    "rules": [
      {
        "type": "field",
        "ip": ["geoip:private"],
        "outboundTag": "blocked"
      },
      {
        "type": "field",
        "protocol": ["bittorrent"],
        "outboundTag": "blocked"
      }
    ]
  },
  "api": {
    "tag": "api",
    "services": [
      "HandlerService",
      "StatsService"
    ]
  },
  "stats": {},
  "policy": {
    "levels": {
      "0": {
        "statsUserUplink": true,
        "statsUserDownlink": true
      }
    },
    "system": {
      "statsInboundUplink": true,
      "statsInboundDownlink": true
    }
  }
}
EOF
    
    if [[ $? -eq 0 ]]; then
        chmod 644 "$config_file" 2>/dev/null
        track_success "Xray configuration generated"
        return 0
    else
        soft_error "Failed to generate Xray configuration"
        return 1
    fi
}

# Generate Trojan base configuration
generate_trojan_config() {
    local config_file="data/proxy/configs/trojan.json"
    
    # Skip if config already exists
    if [[ -f "$config_file" ]]; then
        log "Trojan config already exists, skipping generation"
        return 0
    fi
    
    log "Generating base Trojan configuration..."
    
    # Ensure directory exists
    mkdir -p "$(dirname "$config_file")" 2>/dev/null || {
        soft_error "Failed to create Trojan config directory"
        return 1
    }
    
    cat > "$config_file" <<'EOF'
{
  "run_type": "server",
  "local_addr": "0.0.0.0",
  "local_port": 8002,
  "remote_addr": "127.0.0.1",
  "remote_port": 80,
  "password": [],
  "log_level": 1,
  "log_file": "/var/log/trojan-go/trojan.log",
  "ssl": {
    "cert": "",
    "key": "",
    "key_password": "",
    "cipher": "ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384",
    "cipher_tls13": "TLS_AES_128_GCM_SHA256:TLS_CHACHA20_POLY1305_SHA256:TLS_AES_256_GCM_SHA384",
    "prefer_server_cipher": true,
    "alpn": [
      "http/1.1",
      "h2"
    ],
    "reuse_session": true,
    "session_ticket": false,
    "session_timeout": 600,
    "plain_http_response": "",
    "curves": "",
    "dhparam": "",
    "fingerprint": "firefox"
  },
  "tcp": {
    "prefer_ipv4": false,
    "no_delay": true,
    "keep_alive": true,
    "reuse_port": false,
    "fast_open": false,
    "fast_open_qlen": 20
  },
  "websocket": {
    "enabled": true,
    "path": "/trojan-ws",
    "host": "",
    "add_headers": {}
  },
  "mux": {
    "enabled": false,
    "concurrency": 8,
    "idle_timeout": 60
  }
}
EOF
    
    if [[ $? -eq 0 ]]; then
        chmod 644 "$config_file" 2>/dev/null
        track_success "Trojan configuration generated"
        return 0
    else
        soft_error "Failed to generate Trojan configuration"
        return 1
    fi
}

# Generate Sing-box base configuration
generate_singbox_config() {
    local config_file="data/proxy/configs/singbox.json"
    
    # Skip if config already exists
    if [[ -f "$config_file" ]]; then
        log "Sing-box config already exists, skipping generation"
        return 0
    fi
    
    log "Generating base Sing-box configuration..."
    
    # Ensure directory exists
    mkdir -p "$(dirname "$config_file")" 2>/dev/null || {
        soft_error "Failed to create Sing-box config directory"
        return 1
    }
    
    # Generate random passwords for Sing-box protocols
    local shadowsocks_password=$(openssl rand -base64 32 2>/dev/null || echo "default-password-change-me")
    local hysteria2_obfs_password=$(openssl rand -base64 16 2>/dev/null || echo "default-obfs-password")
    
    cat > "$config_file" <<EOF
{
  "log": {
    "level": "warn",
    "output": "/var/log/sing-box/sing-box.log",
    "timestamp": true
  },
  "inbounds": [
    {
      "type": "shadowtls",
      "tag": "shadowtls-in",
      "listen": "0.0.0.0",
      "listen_port": 8003,
      "version": 3,
      "users": [],
      "handshake": {
        "server": "www.cloudflare.com",
        "server_port": 443
      },
      "strict_mode": true,
      "detour": "shadowsocks-in"
    },
    {
      "type": "shadowsocks",
      "tag": "shadowsocks-in",
      "listen": "127.0.0.1",
      "listen_port": 8013,
      "method": "2022-blake3-aes-256-gcm",
      "password": "$shadowsocks_password",
      "users": []
    },
    {
      "type": "hysteria2",
      "tag": "hysteria2-in",
      "listen": "0.0.0.0",
      "listen_port": 8005,
      "users": [],
      "masquerade": {
        "type": "proxy",
        "proxy": {
          "url": "https://www.cloudflare.com"
        }
      },
      "tls": {
        "enabled": false
      },
      "obfs": {
        "type": "salamander",
        "salamander": {
          "password": "$hysteria2_obfs_password"
        }
      },
      "ignore_client_bandwidth": false
    },
    {
      "type": "tuic",
      "tag": "tuic-in",
      "listen": "0.0.0.0",
      "listen_port": 8006,
      "users": [],
      "congestion_control": "bbr",
      "auth_timeout": "3s",
      "zero_rtt_handshake": false,
      "heartbeat": "10s",
      "tls": {
        "enabled": false
      }
    }
  ],
  "outbounds": [
    {
      "type": "direct",
      "tag": "direct"
    },
    {
      "type": "block",
      "tag": "block"
    }
  ],
  "route": {
    "rules": [
      {
        "geoip": "private",
        "outbound": "direct"
      }
    ],
    "final": "direct",
    "auto_detect_interface": true
  }
}
EOF
    
    if [[ $? -eq 0 ]]; then
        chmod 644 "$config_file" 2>/dev/null
        track_success "Sing-box configuration generated"
        log "  ShadowSocks server password: $shadowsocks_password"
        log "  Hysteria2 obfuscation password: $hysteria2_obfs_password"
        return 0
    else
        soft_error "Failed to generate Sing-box configuration"
        return 1
    fi
}

# Generate WireGuard base configuration
generate_wireguard_config() {
    local config_file="data/proxy/configs/wireguard/wg0.conf"
    
    # Skip if config already exists
    if [[ -f "$config_file" ]]; then
        log "WireGuard config already exists, skipping generation"
        return 0
    fi
    
    log "Generating base WireGuard configuration..."
    
    # Ensure directory exists
    mkdir -p "$(dirname "$config_file")" 2>/dev/null || {
        soft_error "Failed to create WireGuard config directory"
        return 1
    }
    
    # Generate server keys if they don't exist
    local server_private_key
    local server_public_key
    
    if command -v wg &> /dev/null; then
        server_private_key=$(wg genkey 2>/dev/null)
        server_public_key=$(echo "$server_private_key" | wg pubkey 2>/dev/null)
    else
        # Fallback: generate random base64 keys (not cryptographically secure for WireGuard)
        track_warning "WireGuard tools not installed. Generating placeholder keys."
        server_private_key=$(openssl rand -base64 32 2>/dev/null || echo "placeholder-private-key")
        server_public_key=$(openssl rand -base64 32 2>/dev/null || echo "placeholder-public-key")
    fi
    
    cat > "$config_file" <<EOF
[Interface]
# Server configuration
PrivateKey = $server_private_key
Address = 10.8.0.1/24
ListenPort = 51820
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

# Peers will be added here by the admin panel

EOF
    
    if [[ $? -eq 0 ]]; then
        chmod 600 "$config_file" 2>/dev/null
        track_success "WireGuard configuration generated"
        log "  Server public key: $server_public_key"
        return 0
    else
        soft_error "Failed to generate WireGuard configuration"
        return 1
    fi
}

# Create first user automatically
create_first_user() {
    log "Creating first user account..."
    
    # Check if users already exist
    if [[ -f data/proxy/configs/users.json ]]; then
        local user_count=$(python3 -c "import json; data=json.load(open('data/proxy/configs/users.json')); print(len(data.get('users', {})))" 2>/dev/null || echo "0")
        
        if [[ "$user_count" != "0" ]]; then
            log "Users already exist ($user_count user(s)). Skipping first user creation."
            return 0
        fi
    fi
    
    # Check if Python3 is available
    if ! command -v python3 &> /dev/null; then
        warn "Python3 not found. Skipping first user creation."
        warn "You can create users manually through the admin panel."
        return 0
    fi
    
    # Check if WireGuard tools are available
    if ! command -v wg &> /dev/null; then
        warn "WireGuard tools not found. Installing wireguard-tools..."
        if sudo apt-get update && sudo apt-get install -y wireguard-tools; then
            log "WireGuard tools installed successfully"
        else
            warn "Failed to install WireGuard tools. First user creation may fail."
        fi
    fi
    
    # Default username for first user
    local first_username="admin"
    
    # Prompt for custom username (optional)
    read -p "Enter username for first user [admin]: " USERNAME_INPUT
    if [[ -n "$USERNAME_INPUT" ]]; then
        first_username="$USERNAME_INPUT"
    fi
    
    log "Creating first user: $first_username"
    
    # Run the create-first-user.py script
    if [[ -f scripts/create-first-user.py ]]; then
        local user_credentials=$(python3 scripts/create-first-user.py "$first_username" "data/proxy/configs" 2>&1)
        
        if [[ $? -eq 0 ]]; then
            track_success "First user created: $first_username"
            
            # Save credentials to a secure file for reference
            local creds_file="first_user_credentials_$(date +'%Y%m%d_%H%M%S').json"
            echo "$user_credentials" > "$creds_file"
            chmod 600 "$creds_file"
            
            log "User credentials saved to: $creds_file"
            
            # Display credentials summary
            echo
            echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
            echo -e "${GREEN}║              First User Created Successfully               ║${NC}"
            echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
            echo
            echo -e "${BLUE}Username:${NC} $first_username"
            echo
            echo -e "${YELLOW}IMPORTANT: Save these credentials securely!${NC}"
            echo "Full credentials saved to: $creds_file"
            echo
            
            # Export username for use in display_summary
            export FIRST_USER_USERNAME="$first_username"
            export FIRST_USER_CREDENTIALS_FILE="$creds_file"
        else
            soft_error "Failed to create first user"
            echo "$user_credentials" | tee -a "$INSTALL_LOG"
            warn "You can create users manually through the admin panel after installation."
        fi
    else
        warn "First user creation script not found: scripts/create-first-user.py"
        warn "You can create users manually through the admin panel."
    fi
}

# Generate all proxy service configurations
generate_proxy_configs() {
    log "Generating proxy service configurations..."
    
    # Generate base configurations for all proxy services
    generate_xray_config
    generate_trojan_config
    generate_singbox_config
    generate_wireguard_config
    
    log "All proxy service configurations generated"
}

# Set proper ownership for container users
set_container_ownership() {
    log "Configuring ownership for container users..."
    
    # Get current user info
    CURRENT_UID=$(id -u)
    CURRENT_GID=$(id -g)
    
    # Admin panel runs as UID 1000, ensure data directory is owned by UID 1000
    log "Setting ownership of admin data directory to UID 1000..."
    if [[ $EUID -eq 0 ]]; then
        chown -R 1000:1000 data/proxy
    else
        # If not root, try to set ownership (may fail if current user is not UID 1000)
        if [[ "$CURRENT_UID" == "1000" ]]; then
            chown -R 1000:1000 data/proxy 2>/dev/null || warn "Could not set ownership to UID 1000. Run with sudo if needed."
        else
            warn "Current user is not UID 1000. Admin panel may have permission issues."
            warn "Consider running: sudo chown -R 1000:1000 data/proxy"
        fi
    fi
    
    # Ensure proxy service log directories are writable
    # Proxy services run as root inside containers but with read-only filesystem
    # Log directories need to be writable from host-mounted volumes
    log "Ensuring proxy service log directories are writable..."
    for log_dir in xray trojan singbox wireguard caddy admin system; do
        if [[ -d "data/proxy/logs/$log_dir" ]]; then
            chmod 755 "data/proxy/logs/$log_dir"
        fi
    done
    
    # Make sure backup directory is world-writable for any container user
    chmod 777 data/proxy/backups
    
    # Verify permissions are set correctly
    log "Verifying directory permissions..."
    if [[ -d data/proxy ]]; then
        log "  ✓ data/proxy exists"
        log "    Owner: $(stat -c '%U:%G (UID:%u GID:%g)' data/proxy 2>/dev/null || echo 'unknown')"
        log "    Permissions: $(stat -c '%a' data/proxy 2>/dev/null || echo 'unknown')"
    fi
    
    if [[ -d data/proxy/backups ]]; then
        log "  ✓ Backup directory permissions: $(stat -c '%a' data/proxy/backups 2>/dev/null || echo 'unknown')"
    fi
    
    log "Container ownership configured successfully"
    log "  - Admin data directory: UID 1000"
    log "  - Proxy log directories: 755 permissions"
    log "  - Backup directory: 777 permissions"
}

# Initialize configuration templates
init_templates() {
    log "Initializing configuration templates..."
    
    local template_failures=0
    
    # Generate initial proxy configurations
    if command -v python3 &> /dev/null; then
        # Generate Xray config
        if [[ -f scripts/xray-config-manager.py ]]; then
            if python3 scripts/xray-config-manager.py init 2>&1 | tee -a "$INSTALL_LOG"; then
                track_success "Xray template initialized"
            else
                track_warning "Failed to initialize Xray template"
                ((template_failures++))
            fi
        fi
        
        # Generate Trojan config
        if [[ -f scripts/trojan-config-manager.py ]]; then
            if python3 scripts/trojan-config-manager.py init 2>&1 | tee -a "$INSTALL_LOG"; then
                track_success "Trojan template initialized"
            else
                track_warning "Failed to initialize Trojan template"
                ((template_failures++))
            fi
        fi
        
        # Generate Sing-box config
        if [[ -f scripts/singbox-config-manager.py ]]; then
            if python3 scripts/singbox-config-manager.py init 2>&1 | tee -a "$INSTALL_LOG"; then
                track_success "Sing-box template initialized"
            else
                track_warning "Failed to initialize Sing-box template"
                ((template_failures++))
            fi
        fi
        
        # Generate WireGuard config
        if [[ -f scripts/wireguard-config-manager.py ]]; then
            if python3 scripts/wireguard-config-manager.py init 2>&1 | tee -a "$INSTALL_LOG"; then
                track_success "WireGuard template initialized"
            else
                track_warning "Failed to initialize WireGuard template"
                ((template_failures++))
            fi
        fi
        
        if [[ $template_failures -eq 0 ]]; then
            success "All configuration templates initialized"
        else
            warn "$template_failures template(s) failed to initialize"
        fi
    else
        track_warning "Python3 not found. Skipping template initialization"
    fi
}

# Select deployment mode
select_deployment_mode() {
    log "Selecting deployment mode..."
    echo
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║              Deployment Mode Selection                     ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo
    echo -e "${GREEN}1. Minimal Mode (Recommended for first-time setup)${NC}"
    echo "   • Deploys only Caddy and Admin Panel"
    echo "   • Faster startup and easier troubleshooting"
    echo "   • Verify SSL and basic functionality first"
    echo "   • Add proxy services later through admin panel"
    echo
    echo -e "${GREEN}2. Full Mode (Complete proxy deployment)${NC}"
    echo "   • Deploys all services: Caddy, Admin Panel, and all proxy protocols"
    echo "   • Xray, Trojan-Go, Sing-box, and WireGuard"
    echo "   • Requires more resources and longer startup time"
    echo "   • Recommended after verifying minimal mode works"
    echo
    
    read -p "Select deployment mode (1 for Minimal, 2 for Full) [1]: " DEPLOYMENT_MODE
    DEPLOYMENT_MODE=${DEPLOYMENT_MODE:-1}
    
    if [[ "$DEPLOYMENT_MODE" == "1" ]]; then
        COMPOSE_FILE="docker-compose.minimal.yml"
        log "Selected: Minimal Mode (Caddy + Admin Panel only)"
        echo
        echo -e "${YELLOW}Note: You can transition to full mode later by running:${NC}"
        echo "  docker compose -f docker-compose.yml up -d"
        echo
    elif [[ "$DEPLOYMENT_MODE" == "2" ]]; then
        COMPOSE_FILE="docker-compose.yml"
        log "Selected: Full Mode (All proxy services)"
    else
        warn "Invalid selection. Defaulting to Minimal Mode."
        COMPOSE_FILE="docker-compose.minimal.yml"
    fi
    
    # Export for use in other functions
    export COMPOSE_FILE
    
    log "Deployment mode configured: $COMPOSE_FILE"
}

# Build Docker images
build_images() {
    local timestamp=$(date +'%Y-%m-%d %H:%M:%S')
    log "Building Docker images..."
    
    # Use the selected compose file
    local compose_file=${COMPOSE_FILE:-docker-compose.yml}
    
    echo "[$timestamp] [OPERATION] Building Docker images from: $compose_file" >> "$INSTALL_LOG"
    echo "[$timestamp] [OPERATION] Docker version: $(docker --version 2>&1)" >> "$INSTALL_LOG"
    echo "[$timestamp] [OPERATION] Docker Compose version: $(docker compose version 2>&1)" >> "$INSTALL_LOG"
    
    if ! docker compose -f "$compose_file" build 2>&1 | tee -a "$INSTALL_LOG"; then
        echo "[$timestamp] [ERROR] Docker image build failed" >> "$INSTALL_LOG"
        echo "[$timestamp] [ERROR] Compose file: $compose_file" >> "$INSTALL_LOG"
        echo "[$timestamp] [ERROR] Docker disk usage: $(docker system df 2>&1)" >> "$INSTALL_LOG"
        error "Failed to build Docker images" "Docker image build"
    fi
    
    echo "[$timestamp] [SUCCESS] Docker images built successfully" >> "$INSTALL_LOG"
    echo "[$timestamp] [INFO] Built images: $(docker images --format '{{.Repository}}:{{.Tag}}' | grep -E 'stealth-vpn-server|proxy' | head -10)" >> "$INSTALL_LOG"
    log "Docker images built successfully"
}

# Check system resources
check_system_resources() {
    log "Checking system resources..."
    
    # Detect CPU cores
    local cpu_cores=$(nproc 2>/dev/null || echo "1")
    log "CPU cores: $cpu_cores"
    
    # Detect total memory in MB
    local total_memory_kb=$(grep MemTotal /proc/meminfo 2>/dev/null | awk '{print $2}')
    local total_memory_mb=$((total_memory_kb / 1024))
    local total_memory_gb=$((total_memory_mb / 1024))
    
    if [[ -n "$total_memory_mb" ]]; then
        log "Total memory: ${total_memory_mb} MB (${total_memory_gb} GB)"
    else
        warn "Could not detect memory size"
        total_memory_mb=0
    fi
    
    # Detect available disk space in GB
    local available_disk_gb=$(df -BG . 2>/dev/null | tail -1 | awk '{print $4}' | sed 's/G//')
    if [[ -n "$available_disk_gb" ]]; then
        log "Available disk space: ${available_disk_gb} GB"
    else
        warn "Could not detect disk space"
        available_disk_gb=0
    fi
    
    # Check minimum requirements
    local requirements_met=true
    
    # Minimum: 1 CPU core (warn if less than 2)
    if [[ $cpu_cores -lt 2 ]]; then
        warn "CPU cores ($cpu_cores) below recommended minimum (2 cores)"
        warn "Performance may be limited. Consider upgrading to a 2+ core server."
        requirements_met=false
    fi
    
    # Minimum: 2GB RAM
    if [[ $total_memory_mb -gt 0 ]] && [[ $total_memory_mb -lt 2048 ]]; then
        warn "Memory (${total_memory_mb} MB) below recommended minimum (2048 MB / 2 GB)"
        warn "System may experience performance issues or OOM errors."
        requirements_met=false
    fi
    
    # Minimum: 10GB disk space
    if [[ $available_disk_gb -gt 0 ]] && [[ $available_disk_gb -lt 10 ]]; then
        warn "Disk space (${available_disk_gb} GB) below recommended minimum (10 GB)"
        warn "May not have enough space for logs, backups, and Docker images."
        requirements_met=false
    fi
    
    # Display resource summary
    echo
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║              System Resource Summary                       ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo
    echo "  CPU Cores:       $cpu_cores $([ $cpu_cores -ge 2 ] && echo -e "${GREEN}✓${NC}" || echo -e "${YELLOW}⚠${NC}")"
    echo "  Memory:          ${total_memory_mb} MB (${total_memory_gb} GB) $([ $total_memory_mb -ge 2048 ] && echo -e "${GREEN}✓${NC}" || echo -e "${YELLOW}⚠${NC}")"
    echo "  Disk Space:      ${available_disk_gb} GB $([ $available_disk_gb -ge 10 ] && echo -e "${GREEN}✓${NC}" || echo -e "${YELLOW}⚠${NC}")"
    echo
    echo "  Recommended Minimum:"
    echo "    CPU:    2 cores"
    echo "    Memory: 2 GB"
    echo "    Disk:   10 GB"
    echo
    
    if [[ "$requirements_met" == "false" ]]; then
        warn "System resources below recommended minimum"
        echo
        read -p "Continue with installation anyway? (y/n): " CONTINUE_INSTALL
        if [[ ! "$CONTINUE_INSTALL" =~ ^[Yy]$ ]]; then
            log "Installation cancelled by user due to insufficient resources"
            exit 0
        fi
        track_warning "Installation proceeding with below-minimum resources"
    else
        success "System resources meet minimum requirements"
    fi
    
    # Calculate dynamic resource limits
    # Number of services that will consume resources
    local num_services=6  # gateway, web, proxy-a, proxy-b, proxy-c, proxy-d
    
    # CPU limits: 80% of available cores divided by number of services
    local cpu_limit_per_service=$(awk "BEGIN {printf \"%.2f\", ($cpu_cores * 0.8) / $num_services}")
    
    # Ensure minimum CPU limit of 0.1 per service
    if (( $(awk "BEGIN {print ($cpu_limit_per_service < 0.1)}") )); then
        cpu_limit_per_service="0.1"
    fi
    
    # Memory limits: 70% of available RAM divided by number of services
    local ram_limit_per_service_mb=$(awk "BEGIN {printf \"%.0f\", ($total_memory_mb * 0.7) / $num_services}")
    
    # Ensure minimum memory limit of 64MB per service
    if [[ $ram_limit_per_service_mb -lt 64 ]]; then
        ram_limit_per_service_mb=64
    fi
    
    # Format memory limit for Docker (e.g., "256M")
    local ram_limit_per_service="${ram_limit_per_service_mb}M"
    
    log "Calculated resource limits per service:"
    log "  CPU limit: ${cpu_limit_per_service} cores"
    log "  Memory limit: ${ram_limit_per_service}"
    
    # Export for use in other functions and docker-compose
    export DETECTED_CPU_CORES=$cpu_cores
    export DETECTED_MEMORY_MB=$total_memory_mb
    export CPU_LIMIT_PER_SERVICE=$cpu_limit_per_service
    export RAM_LIMIT_PER_SERVICE=$ram_limit_per_service
}

# Adjust Docker resource limits based on available CPU cores
adjust_resource_limits() {
    log "Adjusting Docker resource limits based on detected resources..."
    
    # Use detected CPU cores or fallback to nproc
    local cpu_cores=${DETECTED_CPU_CORES:-$(nproc 2>/dev/null || echo "2")}
    log "Adjusting for $cpu_cores CPU core(s)"
    
    # Backup original docker-compose.yml
    if [[ ! -f docker-compose.yml.backup ]]; then
        if cp docker-compose.yml docker-compose.yml.backup 2>/dev/null; then
            log "Created backup of docker-compose.yml"
        else
            soft_error "Failed to backup docker-compose.yml"
            return 1
        fi
    fi
    
    # Adjust CPU limits based on available cores
    if [[ $cpu_cores -eq 1 ]]; then
        log "Single-core server: Adjusting CPU limits to fractional values..."
        
        # For single-core servers, use fractional limits
        # Caddy: 0.8 (highest priority)
        sed -i "s/cpus: '2\.0'/cpus: '0.8'/g" docker-compose.yml
        
        # Proxy services: 0.5 each
        sed -i "s/cpus: '2\.0'/cpus: '0.5'/g" docker-compose.yml
        
        # Admin panel: 0.3
        sed -i "s/cpus: '1\.0'/cpus: '0.3'/g" docker-compose.yml
        
        # Adjust reservations as well
        sed -i "s/cpus: '0\.5'/cpus: '0.1'/g" docker-compose.yml
        sed -i "s/cpus: '0\.25'/cpus: '0.05'/g" docker-compose.yml
        
        track_success "CPU limits adjusted for single-core server"
    elif [[ $cpu_cores -eq 2 ]]; then
        log "Dual-core server: Using moderate CPU limits..."
        
        # For dual-core servers, reduce limits slightly
        sed -i "s/cpus: '2\.0'/cpus: '1.5'/g" docker-compose.yml
        sed -i "s/cpus: '1\.0'/cpus: '0.8'/g" docker-compose.yml
        
        track_success "CPU limits adjusted for dual-core server"
    else
        log "Multi-core server ($cpu_cores cores): Using default limits"
        track_success "Using default CPU limits for multi-core server"
    fi
}

# Validate Caddyfile syntax
validate_caddyfile() {
    log "Validating Caddyfile syntax..."
    
    # Check if Caddyfile exists
    if [[ ! -f config/Caddyfile ]]; then
        warn "Caddyfile not found at config/Caddyfile"
        return 0
    fi
    
    # Check if caddy command is available
    if ! command -v caddy &> /dev/null; then
        warn "Caddy command not found. Skipping Caddyfile validation."
        warn "Caddyfile will be validated when the container starts."
        return 0
    fi
    
    # Run caddy validate
    log "Running 'caddy validate' on config/Caddyfile..."
    if caddy validate --config config/Caddyfile --adapter caddyfile 2>&1 | tee /tmp/caddy-validate.log; then
        log "Caddyfile validation passed"
        rm -f /tmp/caddy-validate.log
        return 0
    else
        error "Caddyfile validation failed. Please check the syntax errors above."
        echo
        echo -e "${RED}Common issues:${NC}"
        echo "  • Invalid directive names (check Caddy v2 documentation)"
        echo "  • Incorrect global options (auto_https should be omitted or use valid values)"
        echo "  • Headers must be in site blocks, not global config"
        echo "  • HTTP/3 syntax: use 'protocols h1 h2 h3' in servers block"
        echo
        echo "Validation log saved to: /tmp/caddy-validate.log"
        return 1
    fi
}

# Validate configuration
validate_config() {
    log "Validating configuration..."
    
    # Check if .env file exists and has required variables
    if [[ ! -f .env ]]; then
        error ".env file not found" "Configuration validation"
    fi
    
    source .env
    
    # Validate required variables
    if [[ -z "$DOMAIN" ]] || [[ "$DOMAIN" == "your-domain.com" ]]; then
        error "DOMAIN not set in .env file" "Configuration validation - DOMAIN"
    fi
    
    if [[ -z "$ADMIN_PASSWORD_HASH" ]]; then
        error "ADMIN_PASSWORD_HASH not set in .env file" "Configuration validation - ADMIN_PASSWORD_HASH"
    fi
    
    if [[ -z "$SESSION_SECRET" ]]; then
        error "SESSION_SECRET not set in .env file" "Configuration validation - SESSION_SECRET"
    fi
    
    # Validate Caddyfile
    validate_caddyfile
    
    log "Configuration validation passed"
}

# Verify DNS configuration
verify_dns_configuration() {
    local domain="$1"
    
    log "Verifying DNS configuration for domain: $domain"
    
    # Skip if domain is not configured
    if [[ -z "$domain" ]] || [[ "$domain" == "your-domain.com" ]]; then
        warn "Domain not configured. Skipping DNS verification."
        return 0
    fi
    
    # Get server's public IP
    log "Detecting server's public IP address..."
    local server_ip=$(curl -s ifconfig.me 2>/dev/null || curl -s icanhazip.com 2>/dev/null || curl -s ipinfo.io/ip 2>/dev/null || echo "")
    
    if [[ -z "$server_ip" ]]; then
        warn "Could not determine server's public IP address"
        warn "Please verify DNS manually: dig $domain +short"
        return 0
    fi
    
    log "Server public IP: $server_ip"
    
    # Check if dig is available
    if ! command -v dig &> /dev/null; then
        warn "dig command not found. Installing dnsutils..."
        if sudo apt-get update && sudo apt-get install -y dnsutils; then
            log "dnsutils installed successfully"
        else
            warn "Failed to install dnsutils. Trying nslookup instead..."
            
            # Fallback to nslookup
            if command -v nslookup &> /dev/null; then
                log "Using nslookup for DNS verification..."
                local resolved_ip=$(nslookup "$domain" 2>/dev/null | grep -A1 "Name:" | grep "Address:" | awk '{print $2}' | head -1)
                
                if [[ -z "$resolved_ip" ]]; then
                    soft_error "DNS verification failed: Could not resolve domain $domain"
                    display_dns_configuration_instructions "$domain" "$server_ip"
                    return 1
                fi
                
                log "Domain $domain resolves to: $resolved_ip"
                
                # Compare IPs
                if [[ "$resolved_ip" == "$server_ip" ]]; then
                    success "DNS configuration verified: $domain → $server_ip"
                    return 0
                else
                    soft_error "DNS mismatch: $domain resolves to $resolved_ip but server IP is $server_ip"
                    display_dns_configuration_instructions "$domain" "$server_ip"
                    return 1
                fi
            else
                warn "Neither dig nor nslookup available. Skipping DNS verification."
                return 0
            fi
        fi
    fi
    
    # Use dig to resolve domain
    log "Resolving domain with dig..."
    local resolved_ip=$(dig +short "$domain" A 2>/dev/null | grep -E '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$' | head -1)
    
    if [[ -z "$resolved_ip" ]]; then
        soft_error "DNS verification failed: Could not resolve domain $domain"
        display_dns_configuration_instructions "$domain" "$server_ip"
        return 1
    fi
    
    log "Domain $domain resolves to: $resolved_ip"
    
    # Compare resolved IP with server IP
    if [[ "$resolved_ip" == "$server_ip" ]]; then
        success "DNS configuration verified: $domain → $server_ip"
        return 0
    else
        soft_error "DNS mismatch detected"
        log "  Domain resolves to: $resolved_ip"
        log "  Server IP is:       $server_ip"
        
        display_dns_configuration_instructions "$domain" "$server_ip"
        return 1
    fi
}

# Display DNS configuration instructions
display_dns_configuration_instructions() {
    local domain="$1"
    local server_ip="$2"
    
    echo
    echo -e "${RED}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║           DNS Configuration Required                       ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════════╝${NC}"
    echo
    echo -e "${YELLOW}Your domain does not point to this server.${NC}"
    echo
    echo "Domain:    $domain"
    echo "Server IP: $server_ip"
    echo
    echo -e "${BLUE}DNS Configuration Steps:${NC}"
    echo
    echo "1. Log in to your domain registrar or DNS provider"
    echo "   (e.g., Cloudflare, Namecheap, GoDaddy, Route53)"
    echo
    echo "2. Add or update an A record:"
    echo "   Type:  A"
    echo "   Name:  @ (or your subdomain)"
    echo "   Value: $server_ip"
    echo "   TTL:   300 (or automatic)"
    echo
    echo "3. Wait for DNS propagation (usually 5-30 minutes)"
    echo
    echo "4. Verify DNS configuration:"
    echo "   dig $domain +short"
    echo "   # Should return: $server_ip"
    echo
    echo -e "${YELLOW}Note:${NC} SSL certificate acquisition will fail if DNS is not configured correctly."
    echo "      You can continue installation, but HTTPS will not work until DNS is fixed."
    echo
    
    read -p "Continue installation anyway? (y/n): " CONTINUE_DNS
    if [[ ! "$CONTINUE_DNS" =~ ^[Yy]$ ]]; then
        log "Installation cancelled by user due to DNS configuration issue"
        exit 1
    fi
    
    track_warning "Installation proceeding with DNS mismatch"
}

# Check if ports 80 and 443 are accessible
check_port_accessibility() {
    log "Checking port accessibility..."
    
    # Check if nc (netcat) is available
    if ! command -v nc &> /dev/null; then
        warn "netcat (nc) not found. Installing..."
        if sudo apt-get update && sudo apt-get install -y netcat-openbsd; then
            log "netcat installed successfully"
        else
            warn "Failed to install netcat. Skipping port accessibility check."
            return 0
        fi
    fi
    
    # Get server's public IP
    local server_ip=$(curl -s ifconfig.me 2>/dev/null || curl -s icanhazip.com 2>/dev/null || echo "")
    
    if [[ -z "$server_ip" ]]; then
        warn "Could not determine server's public IP address"
        warn "Please ensure ports 80 and 443 are accessible from the internet"
        return 0
    fi
    
    log "Server public IP: $server_ip"
    
    # Check if ports are listening locally
    log "Checking if ports 80 and 443 are available locally..."
    
    # Check port 80
    if sudo lsof -i :80 -sTCP:LISTEN &> /dev/null; then
        warn "Port 80 is already in use by another process"
        sudo lsof -i :80 -sTCP:LISTEN | tee -a "$INSTALL_LOG"
        echo
        read -p "Continue anyway? (y/n): " CONTINUE_PORT_80
        if [[ ! "$CONTINUE_PORT_80" =~ ^[Yy]$ ]]; then
            error "Port 80 is required for Let's Encrypt certificate acquisition" "Port 80 accessibility check"
        fi
    else
        log "Port 80 is available"
    fi
    
    # Check port 443
    if sudo lsof -i :443 -sTCP:LISTEN &> /dev/null; then
        warn "Port 443 is already in use by another process"
        sudo lsof -i :443 -sTCP:LISTEN | tee -a "$INSTALL_LOG"
        echo
        read -p "Continue anyway? (y/n): " CONTINUE_PORT_443
        if [[ ! "$CONTINUE_PORT_443" =~ ^[Yy]$ ]]; then
            error "Port 443 is required for HTTPS access" "Port 443 accessibility check"
        fi
    else
        log "Port 443 is available"
    fi
    
    success "Port accessibility check completed"
    
    # Display firewall guidance
    echo
    echo -e "${YELLOW}Firewall Configuration:${NC}"
    echo "Ensure your firewall allows incoming connections on ports 80 and 443:"
    echo
    echo "  UFW (Ubuntu):"
    echo "    sudo ufw allow 80/tcp"
    echo "    sudo ufw allow 443/tcp"
    echo
    echo "  iptables:"
    echo "    sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT"
    echo "    sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT"
    echo
    echo "  Cloud provider: Configure security groups to allow ports 80 and 443"
    echo
}

# Wait for SSL certificate acquisition
wait_for_ssl_certificate() {
    local domain="$1"
    local max_wait=120
    local elapsed=0
    local check_interval=5
    
    log "Waiting for SSL certificate acquisition for domain: $domain"
    log "This may take up to $max_wait seconds..."
    
    # Wait for Caddy to start
    sleep 10
    
    while [[ $elapsed -lt $max_wait ]]; do
        # Check Caddy admin API for certificate status
        local cert_status=$(curl -s http://localhost:2019/config/apps/tls/certificates 2>/dev/null || echo "")
        
        if [[ -n "$cert_status" ]] && echo "$cert_status" | grep -q "$domain"; then
            log "Certificate found in Caddy's certificate store"
            return 0
        fi
        
        # Display progress
        echo -ne "\r  Waiting for certificate... ${elapsed}s / ${max_wait}s"
        
        sleep $check_interval
        elapsed=$((elapsed + check_interval))
    done
    
    echo  # New line after progress indicator
    warn "Certificate acquisition timeout after ${max_wait}s"
    return 1
}

# Validate SSL certificate
validate_ssl_certificate() {
    local domain="$1"
    
    log "Validating SSL certificate for domain: $domain"
    
    # Check if openssl is available
    if ! command -v openssl &> /dev/null; then
        warn "openssl not found. Skipping certificate validation."
        return 0
    fi
    
    # Test SSL connection
    log "Testing SSL connection to $domain..."
    
    local cert_info=$(echo | openssl s_client -servername "$domain" -connect "$domain:443" 2>/dev/null | openssl x509 -noout -text 2>/dev/null)
    
    if [[ -z "$cert_info" ]]; then
        warn "Could not retrieve certificate information"
        return 1
    fi
    
    # Extract certificate details
    local subject=$(echo "$cert_info" | grep "Subject:" | head -1)
    local issuer=$(echo "$cert_info" | grep "Issuer:" | head -1)
    local not_after=$(echo "$cert_info" | grep "Not After" | head -1)
    
    log "Certificate details:"
    log "  $subject"
    log "  $issuer"
    log "  $not_after"
    
    # Check if certificate matches domain
    if echo "$cert_info" | grep -q "CN.*$domain"; then
        success "Certificate matches domain: $domain"
    else
        warn "Certificate may not match domain: $domain"
    fi
    
    # Check if certificate is from Let's Encrypt
    if echo "$issuer" | grep -qi "Let's Encrypt"; then
        success "Certificate issued by Let's Encrypt"
    else
        warn "Certificate not issued by Let's Encrypt"
    fi
    
    # Check certificate expiration
    local expiry_date=$(echo | openssl s_client -servername "$domain" -connect "$domain:443" 2>/dev/null | openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2)
    
    if [[ -n "$expiry_date" ]]; then
        log "Certificate expires: $expiry_date"
        
        # Calculate days until expiration
        local expiry_epoch=$(date -d "$expiry_date" +%s 2>/dev/null || echo "0")
        local current_epoch=$(date +%s)
        local days_until_expiry=$(( (expiry_epoch - current_epoch) / 86400 ))
        
        if [[ $days_until_expiry -gt 0 ]]; then
            log "Certificate valid for $days_until_expiry more days"
            
            if [[ $days_until_expiry -lt 30 ]]; then
                warn "Certificate expires in less than 30 days"
            fi
        else
            error "Certificate has expired!"
        fi
    fi
    
    return 0
}

# Retry SSL certificate acquisition
retry_ssl_certificate_acquisition() {
    local domain="$1"
    local max_retries=3
    local retry_delay=30
    local attempt=1
    
    log "Starting SSL certificate acquisition with retry logic..."
    log "Domain: $domain"
    log "Max retries: $max_retries"
    
    while [[ $attempt -le $max_retries ]]; do
        local timestamp=$(date +'%Y-%m-%d %H:%M:%S')
        log "Attempt $attempt of $max_retries (at $timestamp)"
        
        # Wait for certificate
        if wait_for_ssl_certificate "$domain"; then
            success "Certificate acquired successfully on attempt $attempt"
            
            # Validate the certificate
            if validate_ssl_certificate "$domain"; then
                success "Certificate validation passed"
                return 0
            else
                warn "Certificate validation failed, but certificate was acquired"
                return 0
            fi
        fi
        
        # Certificate acquisition failed
        if [[ $attempt -lt $max_retries ]]; then
            warn "Certificate acquisition failed on attempt $attempt"
            log "Waiting ${retry_delay}s before retry..."
            sleep $retry_delay
            attempt=$((attempt + 1))
        else
            # Final attempt failed
            error_message="Certificate acquisition failed after $max_retries attempts"
            soft_error "$error_message"
            
            echo
            echo -e "${RED}╔════════════════════════════════════════════════════════════╗${NC}"
            echo -e "${RED}║     SSL Certificate Acquisition Failed                    ║${NC}"
            echo -e "${RED}╚════════════════════════════════════════════════════════════╝${NC}"
            echo
            echo -e "${YELLOW}Troubleshooting Steps:${NC}"
            echo
            echo "1. Verify DNS configuration:"
            echo "   • Ensure $domain points to this server's IP"
            echo "   • Use: dig $domain +short"
            echo "   • Or: nslookup $domain"
            echo
            echo "2. Check firewall and ports:"
            echo "   • Ports 80 and 443 must be accessible from the internet"
            echo "   • Check cloud provider security groups"
            echo "   • Verify UFW/iptables rules"
            echo
            echo "3. Check Caddy logs:"
            echo "   • docker compose logs gateway"
            echo "   • Look for ACME/Let's Encrypt errors"
            echo
            echo "4. Verify domain ownership:"
            echo "   • Let's Encrypt requires HTTP-01 or TLS-ALPN-01 challenge"
            echo "   • Ensure no other web server is running on ports 80/443"
            echo
            echo "5. Check Let's Encrypt rate limits:"
            echo "   • https://letsencrypt.org/docs/rate-limits/"
            echo "   • You may have hit the rate limit for this domain"
            echo
            echo "6. Manual certificate check:"
            echo "   • curl -I https://$domain"
            echo "   • openssl s_client -connect $domain:443 -servername $domain"
            echo
            echo -e "${BLUE}After fixing the issues, you can:${NC}"
            echo "  • Restart Caddy: docker compose restart gateway"
            echo "  • Check logs: docker compose logs -f gateway"
            echo "  • Force certificate renewal: docker compose exec gateway caddy reload"
            echo
            
            return 1
        fi
    done
}

# Verify container status
verify_container_status() {
    log "Verifying container status..."
    
    # Use the selected compose file
    local compose_file=${COMPOSE_FILE:-docker-compose.yml}
    
    # Get list of containers and their status
    local container_status=$(docker compose -f "$compose_file" ps --format json 2>/dev/null)
    
    if [[ -z "$container_status" ]]; then
        warn "Could not retrieve container status"
        return 1
    fi
    
    # Parse container status
    local all_running=true
    local container_count=0
    local running_count=0
    local stopped_count=0
    
    echo
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║              Container Status Verification                 ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo
    
    # Check each expected service
    local services=("gateway" "web" "proxy-a" "proxy-b" "proxy-c" "proxy-d")
    
    for service in "${services[@]}"; do
        ((container_count++))
        
        # Check if container exists and get its status
        local status=$(docker compose -f "$compose_file" ps "$service" --format "{{.State}}" 2>/dev/null)
        
        if [[ -z "$status" ]]; then
            # Container doesn't exist (might be minimal mode)
            if [[ "$compose_file" == "docker-compose.minimal.yml" ]] && [[ "$service" =~ ^proxy- ]]; then
                # In minimal mode, proxy services are expected to be absent
                echo -e "  ${BLUE}○${NC} $service: Not deployed (minimal mode)"
                ((container_count--))
            else
                echo -e "  ${RED}✗${NC} $service: Not found"
                all_running=false
                ((stopped_count++))
            fi
        elif [[ "$status" == "running" ]]; then
            echo -e "  ${GREEN}✓${NC} $service: Running"
            ((running_count++))
        else
            echo -e "  ${RED}✗${NC} $service: $status"
            all_running=false
            ((stopped_count++))
            
            # Get error details for stopped containers
            local container_name=$(docker compose -f "$compose_file" ps "$service" --format "{{.Name}}" 2>/dev/null)
            if [[ -n "$container_name" ]]; then
                log "Error details for $service:"
                docker logs "$container_name" --tail 20 2>&1 | tee -a "$INSTALL_LOG"
            fi
        fi
    done
    
    echo
    echo "Summary: $running_count running, $stopped_count stopped"
    echo
    
    if [[ "$all_running" == "true" ]] && [[ $running_count -gt 0 ]]; then
        success "All containers are running"
        return 0
    else
        soft_error "Some containers are not running"
        return 1
    fi
}

# Verify health endpoints
verify_health_endpoints() {
    log "Verifying health endpoints..."
    
    local all_healthy=true
    local max_wait=60
    local check_interval=5
    local elapsed=0
    
    echo
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║              Health Endpoint Verification                  ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo
    
    # Wait a bit for services to initialize
    log "Waiting for services to initialize..."
    sleep 10
    
    # Check Caddy admin API health endpoint (port 2019)
    log "Testing Caddy admin API (port 2019)..."
    while [[ $elapsed -lt $max_wait ]]; do
        local caddy_response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:2019/config/ 2>/dev/null || echo "000")
        
        if [[ "$caddy_response" == "200" ]]; then
            echo -e "  ${GREEN}✓${NC} Caddy admin API: HTTP $caddy_response"
            break
        else
            if [[ $elapsed -ge $max_wait ]]; then
                echo -e "  ${RED}✗${NC} Caddy admin API: HTTP $caddy_response (timeout)"
                all_healthy=false
                
                # Show diagnostic info
                log "Caddy diagnostic info:"
                docker compose logs gateway --tail 20 2>&1 | tee -a "$INSTALL_LOG"
                break
            fi
            
            echo -ne "\r  Waiting for Caddy... ${elapsed}s / ${max_wait}s"
            sleep $check_interval
            elapsed=$((elapsed + check_interval))
        fi
    done
    
    # Reset elapsed time for next check
    elapsed=0
    
    # Check admin panel health endpoint (port 8010)
    log "Testing admin panel (port 8010)..."
    while [[ $elapsed -lt $max_wait ]]; do
        local admin_response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8010/health 2>/dev/null || echo "000")
        
        if [[ "$admin_response" == "200" ]]; then
            echo -e "  ${GREEN}✓${NC} Admin panel: HTTP $admin_response"
            break
        else
            if [[ $elapsed -ge $max_wait ]]; then
                echo -e "  ${RED}✗${NC} Admin panel: HTTP $admin_response (timeout)"
                all_healthy=false
                
                # Show diagnostic info
                log "Admin panel diagnostic info:"
                docker compose logs web --tail 20 2>&1 | tee -a "$INSTALL_LOG"
                break
            fi
            
            echo -ne "\r  Waiting for admin panel... ${elapsed}s / ${max_wait}s"
            sleep $check_interval
            elapsed=$((elapsed + check_interval))
        fi
    done
    
    echo
    
    if [[ "$all_healthy" == "true" ]]; then
        success "All health endpoints responding"
        return 0
    else
        soft_error "Some health endpoints failed"
        
        echo
        echo -e "${YELLOW}Troubleshooting:${NC}"
        echo "  • Check service logs: docker compose logs -f <service>"
        echo "  • Verify port bindings: docker compose ps"
        echo "  • Check container status: docker compose ps"
        echo "  • Restart failed services: docker compose restart <service>"
        echo
        
        return 1
    fi
}

# Verify admin interface accessibility
verify_admin_interface() {
    local domain="$1"
    
    log "Verifying admin interface accessibility..."
    
    if [[ -z "$domain" ]] || [[ "$domain" == "your-domain.com" ]]; then
        warn "Domain not configured. Skipping admin interface accessibility check."
        return 0
    fi
    
    echo
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║         Admin Interface Accessibility Check                ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo
    
    # Admin panel URL (obfuscated endpoint)
    local admin_url="https://${domain}/api/v2/storage/upload"
    
    log "Testing admin interface at: $admin_url"
    
    # Send HTTPS GET request to admin panel
    local response_code=$(curl -s -o /dev/null -w "%{http_code}" -k "$admin_url" 2>/dev/null || echo "000")
    
    if [[ "$response_code" == "200" ]]; then
        echo -e "  ${GREEN}✓${NC} Admin interface accessible: HTTP $response_code"
        success "Admin interface is accessible via domain"
        
        # Verify login page loads
        log "Verifying login page content..."
        local page_content=$(curl -s -k "$admin_url" 2>/dev/null || echo "")
        
        if echo "$page_content" | grep -qi "login\|password\|username"; then
            echo -e "  ${GREEN}✓${NC} Login page loads successfully"
            success "Login page content verified"
        else
            warn "Login page content could not be verified"
        fi
        
        return 0
    elif [[ "$response_code" == "000" ]]; then
        echo -e "  ${RED}✗${NC} Admin interface: Connection failed"
        soft_error "Could not connect to admin interface"
        
        echo
        echo -e "${YELLOW}Possible issues:${NC}"
        echo "  • SSL certificate not yet acquired"
        echo "  • DNS not pointing to this server"
        echo "  • Firewall blocking HTTPS (port 443)"
        echo "  • Caddy not running or misconfigured"
        echo
        echo -e "${BLUE}Troubleshooting:${NC}"
        echo "  • Check DNS: dig $domain +short"
        echo "  • Check Caddy logs: docker compose logs gateway"
        echo "  • Verify SSL cert: curl -vI https://$domain"
        echo "  • Test locally: curl http://localhost:8010/health"
        echo
        
        return 1
    else
        echo -e "  ${YELLOW}⚠${NC} Admin interface: HTTP $response_code"
        warn "Admin interface returned unexpected status code: $response_code"
        
        if [[ "$response_code" == "404" ]]; then
            echo "  The domain is accessible but the admin endpoint was not found."
            echo "  This may indicate a Caddyfile configuration issue."
        elif [[ "$response_code" == "502" ]] || [[ "$response_code" == "503" ]]; then
            echo "  The gateway is accessible but the admin panel is not responding."
            echo "  Check if the admin panel container is running."
        fi
        
        return 1
    fi
}

# Generate comprehensive verification report
generate_verification_report() {
    local domain="$1"
    local report_file="deployment_verification_$(date +'%Y%m%d_%H%M%S').txt"
    
    log "Generating comprehensive verification report..."
    
    # Create report header
    cat > "$report_file" <<EOF
╔════════════════════════════════════════════════════════════╗
║      Deployment Verification Report                        ║
╚════════════════════════════════════════════════════════════╝

Generated: $(date +'%Y-%m-%d %H:%M:%S')
Domain: ${domain:-Not configured}
Deployment Mode: ${COMPOSE_FILE:-docker-compose.yml}

════════════════════════════════════════════════════════════

VERIFICATION CHECKS
════════════════════════════════════════════════════════════

EOF
    
    # Track verification results
    local total_checks=0
    local passed_checks=0
    local failed_checks=0
    local warning_checks=0
    
    # 1. Container Status Check
    ((total_checks++))
    echo "1. Container Status" >> "$report_file"
    if verify_container_status >> "$report_file" 2>&1; then
        echo "   Status: ✓ PASS" >> "$report_file"
        ((passed_checks++))
    else
        echo "   Status: ✗ FAIL" >> "$report_file"
        ((failed_checks++))
    fi
    echo >> "$report_file"
    
    # 2. Health Endpoints Check
    ((total_checks++))
    echo "2. Health Endpoints" >> "$report_file"
    if verify_health_endpoints >> "$report_file" 2>&1; then
        echo "   Status: ✓ PASS" >> "$report_file"
        ((passed_checks++))
    else
        echo "   Status: ✗ FAIL" >> "$report_file"
        ((failed_checks++))
    fi
    echo >> "$report_file"
    
    # 3. SSL Certificate Check
    ((total_checks++))
    echo "3. SSL Certificate" >> "$report_file"
    if [[ -n "$domain" ]] && [[ "$domain" != "your-domain.com" ]]; then
        if validate_ssl_certificate "$domain" >> "$report_file" 2>&1; then
            echo "   Status: ✓ PASS" >> "$report_file"
            ((passed_checks++))
        else
            echo "   Status: ✗ FAIL" >> "$report_file"
            ((failed_checks++))
        fi
    else
        echo "   Status: ⚠ SKIPPED (domain not configured)" >> "$report_file"
        ((warning_checks++))
    fi
    echo >> "$report_file"
    
    # 4. Admin Interface Accessibility Check
    ((total_checks++))
    echo "4. Admin Interface Accessibility" >> "$report_file"
    if [[ -n "$domain" ]] && [[ "$domain" != "your-domain.com" ]]; then
        if verify_admin_interface "$domain" >> "$report_file" 2>&1; then
            echo "   Status: ✓ PASS" >> "$report_file"
            ((passed_checks++))
        else
            echo "   Status: ✗ FAIL" >> "$report_file"
            ((failed_checks++))
        fi
    else
        echo "   Status: ⚠ SKIPPED (domain not configured)" >> "$report_file"
        ((warning_checks++))
    fi
    echo >> "$report_file"
    
    # Generate summary
    cat >> "$report_file" <<EOF
════════════════════════════════════════════════════════════

SUMMARY
════════════════════════════════════════════════════════════

Total Checks:    $total_checks
Passed:          $passed_checks
Failed:          $failed_checks
Warnings/Skipped: $warning_checks

EOF
    
    # Overall status
    if [[ $failed_checks -eq 0 ]] && [[ $passed_checks -gt 0 ]]; then
        cat >> "$report_file" <<EOF
Overall Status: ✓ SUCCESS

All verification checks passed. The deployment is ready for use.

EOF
    elif [[ $failed_checks -gt 0 ]] && [[ $passed_checks -gt $failed_checks ]]; then
        cat >> "$report_file" <<EOF
Overall Status: ⚠ PARTIAL SUCCESS

Some checks failed but core functionality may still work.
Review the failed checks above and consult troubleshooting guidance.

EOF
    else
        cat >> "$report_file" <<EOF
Overall Status: ✗ FAILED

Multiple critical checks failed. The deployment may not be functional.
Review the installation log and failed checks for details.

EOF
    fi
    
    # Add troubleshooting guidance for failures
    if [[ $failed_checks -gt 0 ]]; then
        cat >> "$report_file" <<EOF
════════════════════════════════════════════════════════════

TROUBLESHOOTING GUIDANCE
════════════════════════════════════════════════════════════

Common Issues and Solutions:

1. Container Not Running
   • Check logs: docker compose logs <service>
   • Restart service: docker compose restart <service>
   • Check resource limits: docker stats
   • Verify configuration files exist

2. Health Endpoints Failing
   • Verify port bindings: docker compose ps
   • Check if ports are accessible: netstat -tlnp | grep <port>
   • Review service logs for errors
   • Ensure containers have proper permissions

3. SSL Certificate Issues
   • Verify DNS points to server: dig $domain +short
   • Check firewall allows ports 80/443
   • Review Caddy logs: docker compose logs gateway
   • Check Let's Encrypt rate limits

4. Admin Interface Not Accessible
   • Verify SSL certificate is acquired
   • Check Caddyfile configuration
   • Ensure admin panel container is running
   • Test local access: curl http://localhost:8010/health

For detailed logs, see: $INSTALL_LOG

════════════════════════════════════════════════════════════
EOF
    fi
    
    # Save report
    chmod 644 "$report_file"
    
    # Display report summary
    echo
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║         Deployment Verification Summary                    ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo
    echo "Total Checks:     $total_checks"
    echo -e "Passed:           ${GREEN}$passed_checks${NC}"
    if [[ $failed_checks -gt 0 ]]; then
        echo -e "Failed:           ${RED}$failed_checks${NC}"
    else
        echo "Failed:           $failed_checks"
    fi
    if [[ $warning_checks -gt 0 ]]; then
        echo -e "Warnings/Skipped: ${YELLOW}$warning_checks${NC}"
    else
        echo "Warnings/Skipped: $warning_checks"
    fi
    echo
    
    if [[ $failed_checks -eq 0 ]] && [[ $passed_checks -gt 0 ]]; then
        echo -e "${GREEN}Overall Status: ✓ SUCCESS${NC}"
        echo "All verification checks passed."
    elif [[ $failed_checks -gt 0 ]] && [[ $passed_checks -gt $failed_checks ]]; then
        echo -e "${YELLOW}Overall Status: ⚠ PARTIAL SUCCESS${NC}"
        echo "Some checks failed. Review the report for details."
    else
        echo -e "${RED}Overall Status: ✗ FAILED${NC}"
        echo "Multiple checks failed. Review the report for troubleshooting."
    fi
    echo
    echo "Detailed report saved to: $report_file"
    echo
    
    # Export report file for use in summary
    export VERIFICATION_REPORT_FILE="$report_file"
    
    # Return status based on results
    if [[ $failed_checks -eq 0 ]]; then
        return 0
    else
        return 1
    fi
}

# Start services
start_services() {
    log "Starting services..."
    
    # Use the selected compose file
    local compose_file=${COMPOSE_FILE:-docker-compose.yml}
    
    read -p "Do you want to start services now? (y/n): " START_NOW
    if [[ "$START_NOW" =~ ^[Yy]$ ]]; then
        if docker compose -f "$compose_file" up -d; then
            log "Services started successfully"
            
            # Wait for services to be healthy
            log "Waiting for services to become healthy..."
            sleep 10
            
            # Check service status
            docker compose -f "$compose_file" ps
            
            # Verify SSL certificate acquisition
            source .env 2>/dev/null || true
            if [[ -n "$DOMAIN" ]] && [[ "$DOMAIN" != "your-domain.com" ]]; then
                log "Verifying SSL certificate acquisition..."
                
                if retry_ssl_certificate_acquisition "$DOMAIN"; then
                    track_success "SSL certificate acquired and validated"
                else
                    track_warning "SSL certificate acquisition failed - see troubleshooting guidance above"
                fi
            else
                warn "Domain not configured. Skipping SSL certificate verification."
            fi
            
            # Run comprehensive verification
            log "Running comprehensive deployment verification..."
            source .env 2>/dev/null || true
            if generate_verification_report "$DOMAIN"; then
                track_success "Deployment verification completed successfully"
            else
                track_warning "Deployment verification completed with failures"
            fi
        else
            error "Failed to start services" "Docker Compose service startup"
        fi
    else
        log "Skipping service start. Run 'docker compose -f $compose_file up -d' when ready"
    fi
}

# Display installation summary
display_installation_summary() {
    echo
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║           Installation Summary                             ║${NC}"
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
        echo "All critical operations completed successfully."
    elif [ ${#SUCCESSFUL_STEPS[@]} -gt ${#FAILED_STEPS[@]} ]; then
        echo -e "${YELLOW}Overall Status: PARTIAL SUCCESS${NC}"
        echo "Some operations failed but core functionality may still work."
        echo "Review the failures above and check the log file: $INSTALL_LOG"
    else
        echo -e "${RED}Overall Status: FAILED${NC}"
        echo "Multiple critical operations failed."
        echo "Review the log file for details: $INSTALL_LOG"
    fi
    
    echo
    echo "Installation log saved to: $INSTALL_LOG"
    echo
}

# Display summary
display_summary() {
    source .env 2>/dev/null || true
    
    local compose_file=${COMPOSE_FILE:-docker-compose.yml}
    local deployment_mode="Full"
    if [[ "$compose_file" == "docker-compose.minimal.yml" ]]; then
        deployment_mode="Minimal"
    fi
    
    # Create comprehensive credentials file
    local credentials_file="installation_credentials_$(date +'%Y%m%d_%H%M%S').txt"
    
    cat > "$credentials_file" <<EOF
╔════════════════════════════════════════════════════════════╗
║    Multi-Protocol Proxy Server - Installation Credentials  ║
╚════════════════════════════════════════════════════════════╝

Generated: $(date +'%Y-%m-%d %H:%M:%S')
Installation Log: $INSTALL_LOG

════════════════════════════════════════════════════════════
ADMIN PANEL ACCESS
════════════════════════════════════════════════════════════

Admin Panel URL:  https://${DOMAIN:-your-domain.com}/api/v2/storage/upload
Admin Username:   ${ADMIN_USERNAME:-admin}
Admin Password:   [Set during installation - check .env file]

Note: The admin panel is accessible via the obfuscated endpoint above.
      Bookmark this URL for easy access.

════════════════════════════════════════════════════════════
FIRST USER ACCOUNT
════════════════════════════════════════════════════════════

EOF
    
    # Add first user information if available
    if [[ -n "$FIRST_USER_USERNAME" ]]; then
        cat >> "$credentials_file" <<EOF
Username: $FIRST_USER_USERNAME

Connection Details:
  • View full connection details in the admin panel
  • Download client configurations from admin panel
  • QR codes available for mobile clients

EOF
        
        if [[ -n "$FIRST_USER_CREDENTIALS_FILE" ]] && [[ -f "$FIRST_USER_CREDENTIALS_FILE" ]]; then
            cat >> "$credentials_file" <<EOF
Detailed Credentials File: $FIRST_USER_CREDENTIALS_FILE

EOF
        fi
    else
        cat >> "$credentials_file" <<EOF
No first user created during installation.
Create users through the admin panel.

EOF
    fi
    
    cat >> "$credentials_file" <<EOF
════════════════════════════════════════════════════════════
DEPLOYMENT INFORMATION
════════════════════════════════════════════════════════════

Deployment Mode:  $deployment_mode
Domain:           ${DOMAIN:-Not configured}
Email:            ${EMAIL:-Not configured}

Services Running:
EOF
    
    if [[ "$deployment_mode" == "Minimal" ]]; then
        cat >> "$credentials_file" <<EOF
  • Caddy (Gateway/Reverse Proxy)
  • Admin Panel (Web Management Interface)

Note: Proxy services not deployed in minimal mode.
      Transition to full mode when ready.
EOF
    else
        cat >> "$credentials_file" <<EOF
  • Caddy (Gateway/Reverse Proxy)
  • Admin Panel (Web Management Interface)
  • Xray (VLESS with XTLS-Vision and WebSocket)
  • Trojan-Go (Trojan protocol with WebSocket)
  • Sing-box (ShadowTLS, Hysteria2, TUIC)
  • WireGuard (with obfuscation)
EOF
    fi
    
    cat >> "$credentials_file" <<EOF

════════════════════════════════════════════════════════════
NEXT STEPS
════════════════════════════════════════════════════════════

1. Access Admin Panel
   • Open: https://${DOMAIN:-your-domain.com}/api/v2/storage/upload
   • Login with admin credentials
   • Verify all services are running

2. Add More Users
   • Use admin panel to create additional users
   • Generate client configurations automatically
   • Download QR codes for mobile clients

3. Configure Clients
   • Download client configurations from admin panel
   • Use appropriate client apps:
     - Xray: v2rayN, v2rayNG, Shadowrocket
     - Trojan: Clash, Shadowrocket
     - Sing-box: SFI, SFA
     - WireGuard: Official WireGuard app

4. Monitor Services
   • Check service status: docker compose ps
   • View logs: docker compose logs -f
   • Run health check: ./scripts/health-check.sh

EOF
    
    if [[ "$deployment_mode" == "Minimal" ]]; then
        cat >> "$credentials_file" <<EOF
5. Transition to Full Mode (Optional)
   • Stop minimal services:
     docker compose -f docker-compose.minimal.yml down
   
   • Start full deployment:
     docker compose -f docker-compose.yml up -d
   
   • Verify all services:
     docker compose ps
     ./scripts/health-check.sh

EOF
    fi
    
    cat >> "$credentials_file" <<EOF
════════════════════════════════════════════════════════════
SERVICE MANAGEMENT COMMANDS
════════════════════════════════════════════════════════════

Start services:    docker compose -f $compose_file up -d
Stop services:     docker compose -f $compose_file down
Restart service:   docker compose -f $compose_file restart <service>
View logs:         docker compose -f $compose_file logs -f
Service status:    docker compose -f $compose_file ps
Health check:      ./scripts/health-check.sh

════════════════════════════════════════════════════════════
TROUBLESHOOTING
════════════════════════════════════════════════════════════

If you encounter issues:

1. Check service logs:
   docker compose logs <service>

2. Verify DNS configuration:
   dig ${DOMAIN:-your-domain.com} +short

3. Check SSL certificates:
   docker compose logs gateway | grep -i certificate

4. Verify ports are accessible:
   sudo lsof -i :80
   sudo lsof -i :443

5. Review installation log:
   cat $INSTALL_LOG

6. Check verification report:
EOF
    
    if [[ -n "$VERIFICATION_REPORT_FILE" ]] && [[ -f "$VERIFICATION_REPORT_FILE" ]]; then
        cat >> "$credentials_file" <<EOF
   cat $VERIFICATION_REPORT_FILE
EOF
    else
        cat >> "$credentials_file" <<EOF
   (No verification report generated)
EOF
    fi
    
    cat >> "$credentials_file" <<EOF

════════════════════════════════════════════════════════════
SECURITY NOTES
════════════════════════════════════════════════════════════

⚠ IMPORTANT SECURITY REMINDERS:

• Store this file securely and delete it after saving credentials
• Change default admin password through admin panel
• Regularly update the system: docker compose pull && docker compose up -d
• Monitor logs for suspicious activity
• Keep backups of configuration files
• Restrict SSH access to trusted IPs only

════════════════════════════════════════════════════════════
EOF
    
    # Set secure permissions on credentials file
    chmod 600 "$credentials_file"
    
    # Display summary to console
    echo
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║      Multi-Protocol Proxy Server Installation Complete    ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  ADMIN PANEL ACCESS${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo
    echo -e "${GREEN}  URL:${NC}      https://${DOMAIN:-your-domain.com}/api/v2/storage/upload"
    echo -e "${GREEN}  Username:${NC} ${ADMIN_USERNAME:-admin}"
    echo -e "${GREEN}  Password:${NC} [Check .env file or installation log]"
    echo
    
    # Display first user information if created
    if [[ -n "$FIRST_USER_USERNAME" ]]; then
        echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
        echo -e "${BLUE}  FIRST USER ACCOUNT${NC}"
        echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
        echo
        echo -e "${GREEN}  Username:${NC} $FIRST_USER_USERNAME"
        echo
        if [[ -n "$FIRST_USER_CREDENTIALS_FILE" ]] && [[ -f "$FIRST_USER_CREDENTIALS_FILE" ]]; then
            echo -e "${YELLOW}  ⚠ Connection credentials saved to:${NC}"
            echo "    $FIRST_USER_CREDENTIALS_FILE"
            echo
            echo "  View full connection details in the admin panel."
        fi
    fi
    
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  DEPLOYMENT INFORMATION${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo
    echo -e "${GREEN}  Mode:${NC}     $deployment_mode"
    echo -e "${GREEN}  Domain:${NC}   ${DOMAIN:-Not configured}"
    if [[ "$deployment_mode" == "Minimal" ]]; then
        echo -e "${GREEN}  Services:${NC} Caddy + Admin Panel only"
    else
        echo -e "${GREEN}  Services:${NC} Caddy + Admin Panel + All proxy protocols"
    fi
    echo
    
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  NEXT STEPS${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo
    echo "  1. Access the admin panel at the URL above"
    echo "  2. Login with your admin credentials"
    echo "  3. Add more users through the admin interface"
    echo "  4. Download client configurations and QR codes"
    echo "  5. Configure your client applications"
    echo
    
    if [[ "$deployment_mode" == "Minimal" ]]; then
        echo -e "${YELLOW}  Minimal Mode Active:${NC}"
        echo "  Proxy services not deployed. To enable all protocols:"
        echo
        echo "    docker compose -f docker-compose.minimal.yml down"
        echo "    docker compose -f docker-compose.yml up -d"
        echo
    fi
    
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  CREDENTIALS FILE${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo
    echo -e "${GREEN}  All credentials and next steps saved to:${NC}"
    echo "    $credentials_file"
    echo
    echo -e "${YELLOW}  ⚠ IMPORTANT:${NC}"
    echo "    • Save this file securely"
    echo "    • Delete it after copying credentials"
    echo "    • File permissions: 600 (owner read/write only)"
    echo
    echo
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  SERVICE MANAGEMENT${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo
    echo "  Start:    docker compose -f $compose_file up -d"
    echo "  Stop:     docker compose -f $compose_file down"
    echo "  Restart:  docker compose -f $compose_file restart <service>"
    echo "  Logs:     docker compose -f $compose_file logs -f"
    echo "  Status:   docker compose -f $compose_file ps"
    echo "  Health:   ./scripts/health-check.sh"
    echo
    
    # Display verification report if available
    if [[ -n "$VERIFICATION_REPORT_FILE" ]] && [[ -f "$VERIFICATION_REPORT_FILE" ]]; then
        echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
        echo -e "${BLUE}  VERIFICATION REPORT${NC}"
        echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
        echo
        echo "  Detailed verification report: $VERIFICATION_REPORT_FILE"
        echo "  View with: cat $VERIFICATION_REPORT_FILE"
        echo
    fi
    
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  INSTALLATION LOGS${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo
    echo "  Installation log: $INSTALL_LOG"
    echo "  Credentials file: $credentials_file"
    if [[ -n "$VERIFICATION_REPORT_FILE" ]] && [[ -f "$VERIFICATION_REPORT_FILE" ]]; then
        echo "  Verification report: $VERIFICATION_REPORT_FILE"
    fi
    echo
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                 Installation Complete!                     ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo
}

# Main installation function
main() {
    # Record installation start time
    export INSTALL_START_TIME=$(date +%s)
    
    echo
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║    Multi-Protocol Proxy Server Installation                ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo
    log "Starting Multi-Protocol Proxy Server installation..."
    log "Installation log: $INSTALL_LOG"
    echo
    
    # Log comprehensive system information at the start
    log_system_info
    
    show_progress "Checking prerequisites"
    check_root
    check_commands
    check_system
    
    show_progress "Detecting system resources"
    check_system_resources
    
    show_progress "Installing Docker (if needed)"
    install_docker
    
    show_progress "Configuring firewall"
    setup_firewall
    
    show_progress "Generating configuration"
    generate_config
    select_deployment_mode
    
    show_progress "Creating directory structure"
    create_directories
    
    show_progress "Creating first user account"
    create_first_user
    
    show_progress "Generating proxy configurations"
    generate_proxy_configs
    set_container_ownership
    init_templates
    adjust_resource_limits
    
    show_progress "Validating configuration"
    validate_config
    
    # Verify DNS configuration before starting services
    source .env 2>/dev/null || true
    if [[ -n "$DOMAIN" ]]; then
        verify_dns_configuration "$DOMAIN"
    fi
    
    show_progress "Checking port accessibility"
    check_port_accessibility
    
    show_progress "Building Docker images"
    build_images
    
    show_progress "Starting services and verifying deployment"
    start_services
    
    show_progress "Finalizing installation"
    display_installation_summary
    display_summary
    
    # Calculate total installation time
    local total_time=$(($(date +%s) - INSTALL_START_TIME))
    local total_min=$((total_time / 60))
    local total_sec=$((total_time % 60))
    
    echo
    echo -e "${BLUE}Total installation time: ${total_min}m ${total_sec}s${NC}"
    echo
    
    if [ ${#FAILED_STEPS[@]} -eq 0 ]; then
        log "Installation completed successfully!"
    else
        warn "Installation completed with ${#FAILED_STEPS[@]} failure(s). Check $INSTALL_LOG for details."
    fi
}

# Run main function
main "$@"