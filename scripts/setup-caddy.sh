#!/bin/bash
"""
Setup script for Caddy configuration
Configures domain name and generates obfuscated endpoints
"""

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Configuration
CADDYFILE_TEMPLATE="config/Caddyfile.template"
CADDYFILE_OUTPUT="config/Caddyfile"
ENDPOINTS_SCRIPT="scripts/generate-endpoints.py"

show_banner() {
    echo "🚀 Stealth VPN Server - Caddy Setup"
    echo "===================================="
    echo ""
}

check_prerequisites() {
    log_step "Checking prerequisites..."
    
    # Check if template exists
    if [ ! -f "$CADDYFILE_TEMPLATE" ]; then
        log_error "Caddyfile template not found: $CADDYFILE_TEMPLATE"
        exit 1
    fi
    
    # Check if Python script exists
    if [ ! -f "$ENDPOINTS_SCRIPT" ]; then
        log_error "Endpoint generation script not found: $ENDPOINTS_SCRIPT"
        exit 1
    fi
    
    # Check if Python is available
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is required but not installed"
        exit 1
    fi
    
    log_info "✓ All prerequisites met"
}

get_domain_name() {
    log_step "Domain configuration..."
    
    if [ -n "${DOMAIN_NAME:-}" ]; then
        log_info "Using domain from environment: $DOMAIN_NAME"
        return 0
    fi
    
    echo ""
    echo "Please enter your domain name (e.g., example.com):"
    echo "This will be used for SSL certificates and VPN configuration."
    echo ""
    read -p "Domain name: " domain_input
    
    if [ -z "$domain_input" ]; then
        log_error "Domain name cannot be empty"
        exit 1
    fi
    
    # Basic domain validation
    if [[ ! "$domain_input" =~ ^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]?\.[a-zA-Z]{2,}$ ]]; then
        log_warn "Domain format may be invalid: $domain_input"
        read -p "Continue anyway? (y/N): " confirm
        if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    export DOMAIN_NAME="$domain_input"
    log_info "✓ Domain configured: $DOMAIN_NAME"
}

generate_endpoints() {
    log_step "Generating obfuscated endpoints..."
    
    if python3 "$ENDPOINTS_SCRIPT" > /dev/null 2>&1; then
        log_info "✓ Endpoints generated successfully"
        
        # Load generated endpoints
        if [ -f "data/stealth-vpn/endpoints.json" ]; then
            ADMIN_ENDPOINT=$(python3 -c "import json; print(json.load(open('data/stealth-vpn/endpoints.json'))['admin_panel'])")
            XRAY_WS_ENDPOINT=$(python3 -c "import json; print(json.load(open('data/stealth-vpn/endpoints.json'))['xray_websocket'])")
            WG_WS_ENDPOINT=$(python3 -c "import json; print(json.load(open('data/stealth-vpn/endpoints.json'))['wireguard_websocket'])")
            HEALTH_ENDPOINT=$(python3 -c "import json; print(json.load(open('data/stealth-vpn/endpoints.json'))['health_check'])")
            WEBRTC_ENDPOINT=$(python3 -c "import json; print(json.load(open('data/stealth-vpn/endpoints.json'))['webrtc_signal'])")
            
            log_info "Generated endpoints:"
            log_info "  Admin Panel:      $ADMIN_ENDPOINT"
            log_info "  Xray WebSocket:   $XRAY_WS_ENDPOINT"
            log_info "  WireGuard WS:     $WG_WS_ENDPOINT"
            log_info "  Health Check:     $HEALTH_ENDPOINT"
            log_info "  WebRTC Signal:    $WEBRTC_ENDPOINT"
        else
            log_error "Failed to load generated endpoints"
            exit 1
        fi
    else
        log_error "Failed to generate endpoints"
        exit 1
    fi
}

create_caddyfile() {
    log_step "Creating Caddyfile from template..."
    
    # Create backup if Caddyfile exists
    if [ -f "$CADDYFILE_OUTPUT" ]; then
        backup_file="${CADDYFILE_OUTPUT}.backup.$(date +%Y%m%d_%H%M%S)"
        cp "$CADDYFILE_OUTPUT" "$backup_file"
        log_info "✓ Backed up existing Caddyfile to $backup_file"
    fi
    
    # Replace placeholders in template
    sed -e "s/DOMAIN_NAME/$DOMAIN_NAME/g" \
        -e "s|ADMIN_ENDPOINT|$ADMIN_ENDPOINT|g" \
        -e "s|XRAY_WS_ENDPOINT|$XRAY_WS_ENDPOINT|g" \
        -e "s|WG_WS_ENDPOINT|$WG_WS_ENDPOINT|g" \
        -e "s|HEALTH_ENDPOINT|$HEALTH_ENDPOINT|g" \
        -e "s|WEBRTC_ENDPOINT|$WEBRTC_ENDPOINT|g" \
        "$CADDYFILE_TEMPLATE" > "$CADDYFILE_OUTPUT"
    
    log_info "✓ Caddyfile created successfully"
}

create_directories() {
    log_step "Creating required directories..."
    
    directories=(
        "data/caddy"
        "data/www"
        "data/stealth-vpn"
        "data/stealth-vpn/configs"
        "data/stealth-vpn/backups"
    )
    
    for dir in "${directories[@]}"; do
        mkdir -p "$dir"
        log_info "✓ Created directory: $dir"
    done
}

validate_configuration() {
    log_step "Validating configuration..."
    
    # Check if Docker Compose is available
    if command -v docker-compose &> /dev/null; then
        # Validate Caddyfile syntax (if Caddy container is available)
        if docker-compose config > /dev/null 2>&1; then
            log_info "✓ Docker Compose configuration is valid"
        else
            log_warn "⚠ Could not validate Docker Compose configuration"
        fi
    else
        log_warn "⚠ Docker Compose not available for validation"
    fi
    
    # Basic Caddyfile syntax check
    if grep -q "$DOMAIN_NAME" "$CADDYFILE_OUTPUT"; then
        log_info "✓ Domain name properly configured in Caddyfile"
    else
        log_error "✗ Domain name not found in Caddyfile"
        exit 1
    fi
}

show_next_steps() {
    echo ""
    log_step "Setup complete! Next steps:"
    echo ""
    echo "1. 🔧 Configure DNS records for your domain:"
    echo "   A     $DOMAIN_NAME        -> YOUR_SERVER_IP"
    echo "   A     www.$DOMAIN_NAME    -> YOUR_SERVER_IP"
    echo "   A     api.$DOMAIN_NAME    -> YOUR_SERVER_IP"
    echo "   A     cdn.$DOMAIN_NAME    -> YOUR_SERVER_IP"
    echo "   A     files.$DOMAIN_NAME  -> YOUR_SERVER_IP"
    echo ""
    echo "2. 🚀 Start the services:"
    echo "   docker-compose up -d"
    echo ""
    echo "3. 🔍 Check service health:"
    echo "   ./scripts/caddy-health.sh"
    echo ""
    echo "4. 🌐 Access your services:"
    echo "   Website:     https://$DOMAIN_NAME"
    echo "   Admin Panel: https://$DOMAIN_NAME$ADMIN_ENDPOINT"
    echo "   API Docs:    https://$DOMAIN_NAME/api/v1/docs"
    echo ""
    echo "5. 🔐 Configure VPN clients with the generated endpoints"
    echo ""
    log_warn "⚠️  Important: Keep the endpoints.json file secure!"
    log_warn "⚠️  The admin panel endpoint should only be shared with authorized users."
}

main() {
    show_banner
    
    check_prerequisites
    get_domain_name
    create_directories
    generate_endpoints
    create_caddyfile
    validate_configuration
    show_next_steps
    
    echo ""
    log_info "🎉 Caddy setup completed successfully!"
}

# Handle script interruption
trap 'echo ""; log_error "Setup interrupted by user"; exit 1' INT TERM

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi