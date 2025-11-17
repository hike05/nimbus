#!/bin/bash

# Stealth VPN Server Installation Script
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
    echo -e "${RED}[$timestamp] $message${NC}"
    echo "[$timestamp] $message" >> "$INSTALL_LOG"
    echo "[$timestamp] Installation failed. Check $INSTALL_LOG for details." >> "$INSTALL_LOG"
    exit 1
}

success() {
    local timestamp=$(date +'%Y-%m-%d %H:%M:%S')
    local message="[SUCCESS] $1"
    echo -e "${GREEN}[$timestamp] ✓ $message${NC}"
    echo "[$timestamp] $message" >> "$INSTALL_LOG"
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

# Non-fatal error - log but continue
soft_error() {
    local timestamp=$(date +'%Y-%m-%d %H:%M:%S')
    local message="[ERROR] $1"
    echo -e "${RED}[$timestamp] $message${NC}"
    echo "[$timestamp] $message" >> "$INSTALL_LOG"
    FAILED_STEPS+=("$1")
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root for security reasons"
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
        error "Missing required commands: ${missing_commands[*]}"
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
    mkdir -p data/stealth-vpn/logs/{xray,trojan,singbox,wireguard,caddy,admin,system}
    mkdir -p data/caddy/{data,config,certificates}
    mkdir -p data/www/{css,js,api/v1}
    
    # Create initial users.json if it doesn't exist
    if [[ ! -f data/stealth-vpn/configs/users.json ]]; then
        echo '{"users": {}, "server": {}, "admin": {}}' > data/stealth-vpn/configs/users.json
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
    chmod 777 data/stealth-vpn/backups
    
    # Make log directories writable for VPN service users (755 is sufficient with proper ownership)
    log "Setting log directories to 755..."
    chmod 755 data/stealth-vpn/logs
    chmod 755 data/stealth-vpn/logs/{xray,trojan,singbox,wireguard,caddy,admin,system}
    
    # Set ownership to current user (or UID 1000 if running with sudo)
    log "Setting ownership for data directories..."
    if [[ $EUID -eq 0 ]]; then
        # Running as root - set to UID 1000
        chown -R 1000:1000 data/stealth-vpn
        log "Set ownership to UID 1000 for admin data directory"
    else
        # Running as regular user - ensure current user owns the files
        CURRENT_USER=$(whoami)
        CURRENT_UID=$(id -u)
        CURRENT_GID=$(id -g)
        
        # Only change ownership if not already owned by current user
        if [[ "$(stat -c '%u' data/stealth-vpn 2>/dev/null || echo '0')" != "$CURRENT_UID" ]]; then
            log "Setting ownership to $CURRENT_USER (UID: $CURRENT_UID)..."
            chown -R $CURRENT_UID:$CURRENT_GID data/stealth-vpn
        fi
    fi
    
    log "Data directories created with proper permissions (755 for dirs, 644 for files)"
    log "Backup directory set to 777 for container write access"
    log "Log directories set to 755 with proper ownership"
}

# Generate Xray base configuration
generate_xray_config() {
    local config_file="data/stealth-vpn/configs/xray.json"
    
    # Skip if config already exists
    if [[ -f "$config_file" ]]; then
        log "Xray config already exists, skipping generation"
        return 0
    fi
    
    log "Generating base Xray configuration..."
    
    # Ensure directory exists
    mkdir -p "$(dirname "$config_file")" 2>/dev/null || {
        soft_error "Failed to create Xray config directory"
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
    local config_file="data/stealth-vpn/configs/trojan.json"
    
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
    local config_file="data/stealth-vpn/configs/singbox.json"
    
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
    local config_file="data/stealth-vpn/configs/wireguard/wg0.conf"
    
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

# Generate all VPN service configurations
generate_vpn_configs() {
    log "Generating VPN service configurations..."
    
    # Generate base configurations for all VPN services
    generate_xray_config
    generate_trojan_config
    generate_singbox_config
    generate_wireguard_config
    
    log "All VPN service configurations generated"
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
        chown -R 1000:1000 data/stealth-vpn
    else
        # If not root, try to set ownership (may fail if current user is not UID 1000)
        if [[ "$CURRENT_UID" == "1000" ]]; then
            chown -R 1000:1000 data/stealth-vpn 2>/dev/null || warn "Could not set ownership to UID 1000. Run with sudo if needed."
        else
            warn "Current user is not UID 1000. Admin panel may have permission issues."
            warn "Consider running: sudo chown -R 1000:1000 data/stealth-vpn"
        fi
    fi
    
    # Ensure VPN service log directories are writable
    # VPN services run as root inside containers but with read-only filesystem
    # Log directories need to be writable from host-mounted volumes
    log "Ensuring VPN service log directories are writable..."
    for log_dir in xray trojan singbox wireguard caddy admin system; do
        if [[ -d "data/stealth-vpn/logs/$log_dir" ]]; then
            chmod 755 "data/stealth-vpn/logs/$log_dir"
        fi
    done
    
    # Make sure backup directory is world-writable for any container user
    chmod 777 data/stealth-vpn/backups
    
    # Verify permissions are set correctly
    log "Verifying directory permissions..."
    if [[ -d data/stealth-vpn ]]; then
        log "  ✓ data/stealth-vpn exists"
        log "    Owner: $(stat -c '%U:%G (UID:%u GID:%g)' data/stealth-vpn 2>/dev/null || echo 'unknown')"
        log "    Permissions: $(stat -c '%a' data/stealth-vpn 2>/dev/null || echo 'unknown')"
    fi
    
    if [[ -d data/stealth-vpn/backups ]]; then
        log "  ✓ Backup directory permissions: $(stat -c '%a' data/stealth-vpn/backups 2>/dev/null || echo 'unknown')"
    fi
    
    log "Container ownership configured successfully"
    log "  - Admin data directory: UID 1000"
    log "  - VPN log directories: 755 permissions"
    log "  - Backup directory: 777 permissions"
}

# Initialize configuration templates
init_templates() {
    log "Initializing configuration templates..."
    
    local template_failures=0
    
    # Generate initial VPN configurations
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
    echo "   • Add VPN services later through admin panel"
    echo
    echo -e "${GREEN}2. Full Mode (Complete VPN deployment)${NC}"
    echo "   • Deploys all services: Caddy, Admin Panel, and all VPN protocols"
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
        log "Selected: Full Mode (All VPN services)"
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
    log "Building Docker images..."
    
    # Use the selected compose file
    local compose_file=${COMPOSE_FILE:-docker-compose.yml}
    
    if ! docker compose -f "$compose_file" build; then
        error "Failed to build Docker images"
    fi
    
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
    
    # Export for use in adjust_resource_limits
    export DETECTED_CPU_CORES=$cpu_cores
    export DETECTED_MEMORY_MB=$total_memory_mb
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
        
        # VPN services: 0.5 each
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
    
    # Validate Caddyfile
    validate_caddyfile
    
    log "Configuration validation passed"
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
        else
            error "Failed to start services"
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
    
    echo
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║         Stealth VPN Server Installation Complete          ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo
    echo -e "${BLUE}Deployment Mode: ${deployment_mode}${NC}"
    if [[ "$deployment_mode" == "Minimal" ]]; then
        echo "  Services: Caddy + Admin Panel only"
        echo
    else
        echo "  Services: Caddy + Admin Panel + All VPN protocols"
        echo
    fi
    
    echo -e "${BLUE}Configuration Summary:${NC}"
    echo "  Domain: ${DOMAIN:-Not set}"
    echo "  Admin Panel: https://${DOMAIN:-your-domain.com}/api/v2/storage/upload"
    echo "  Admin Username: ${ADMIN_USERNAME:-admin}"
    echo
    echo -e "${BLUE}Service Management:${NC}"
    echo "  Start services:   docker compose -f $compose_file up -d"
    echo "  Stop services:    docker compose -f $compose_file down"
    echo "  View logs:        docker compose -f $compose_file logs -f"
    echo "  Restart service:  docker compose -f $compose_file restart <service>"
    echo "  Service status:   docker compose -f $compose_file ps"
    echo
    
    if [[ "$deployment_mode" == "Minimal" ]]; then
        echo -e "${YELLOW}╔════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${YELLOW}║        Transitioning from Minimal to Full Mode            ║${NC}"
        echo -e "${YELLOW}╚════════════════════════════════════════════════════════════╝${NC}"
        echo
        echo "After verifying that Caddy and Admin Panel work correctly:"
        echo
        echo "1. Stop minimal services:"
        echo "   docker compose -f docker-compose.minimal.yml down"
        echo
        echo "2. Start full deployment:"
        echo "   docker compose -f docker-compose.yml up -d"
        echo
        echo "3. Verify all services are running:"
        echo "   docker compose -f docker-compose.yml ps"
        echo "   ./scripts/health-check.sh"
        echo
        echo "Note: Your SSL certificates, user data, and configurations"
        echo "      will be preserved during the transition."
        echo
    fi
    
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
    echo "  • Check logs if services fail to start: docker compose -f $compose_file logs -f"
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
    log "Installation log: $INSTALL_LOG"
    echo
    
    check_root
    check_commands
    check_system
    check_system_resources
    install_docker
    setup_firewall
    generate_config
    select_deployment_mode  # NEW: Prompt for deployment mode
    create_directories
    generate_vpn_configs
    set_container_ownership
    init_templates
    adjust_resource_limits
    validate_config
    build_images
    start_services
    display_installation_summary
    display_summary
    
    if [ ${#FAILED_STEPS[@]} -eq 0 ]; then
        log "Installation completed successfully!"
    else
        warn "Installation completed with ${#FAILED_STEPS[@]} failure(s). Check $INSTALL_LOG for details."
    fi
}

# Run main function
main "$@"