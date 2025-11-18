#!/bin/bash
# Health check script for Caddy container
# Verifies that Caddy is running and responding correctly

set -euo pipefail

# Configuration
CADDY_ADMIN_URL="http://localhost:2019"
CADDY_WEB_URL="https://localhost"
TIMEOUT=10
RETRIES=3

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

check_caddy_admin() {
    log_info "Checking Caddy admin API..."
    
    for i in $(seq 1 $RETRIES); do
        if curl -s --max-time $TIMEOUT "$CADDY_ADMIN_URL/config/" > /dev/null 2>&1; then
            log_info "✓ Caddy admin API is responding"
            return 0
        else
            log_warn "✗ Caddy admin API check failed (attempt $i/$RETRIES)"
            sleep 2
        fi
    done
    
    log_error "✗ Caddy admin API is not responding"
    return 1
}

check_caddy_web() {
    log_info "Checking Caddy web server..."
    
    for i in $(seq 1 $RETRIES); do
        if curl -s --max-time $TIMEOUT --insecure "$CADDY_WEB_URL" > /dev/null 2>&1; then
            log_info "✓ Caddy web server is responding"
            return 0
        else
            log_warn "✗ Caddy web server check failed (attempt $i/$RETRIES)"
            sleep 2
        fi
    done
    
    log_error "✗ Caddy web server is not responding"
    return 1
}

check_certificates() {
    log_info "Checking SSL certificates..."
    
    # Check if certificates directory exists
    if [ -d "data/caddy/certificates" ]; then
        cert_count=$(find data/caddy/certificates -name "*.crt" 2>/dev/null | wc -l)
        if [ "$cert_count" -gt 0 ]; then
            log_info "✓ Found $cert_count SSL certificate(s)"
        else
            log_warn "⚠ No SSL certificates found (may be normal for new installation)"
        fi
    else
        log_warn "⚠ Certificates directory not found"
    fi
}

check_config_syntax() {
    log_info "Checking Caddyfile syntax..."
    
    if docker-compose exec caddy caddy validate --config /etc/caddy/Caddyfile > /dev/null 2>&1; then
        log_info "✓ Caddyfile syntax is valid"
        return 0
    else
        log_error "✗ Caddyfile syntax error detected"
        return 1
    fi
}

check_endpoints() {
    log_info "Checking obfuscated endpoints..."
    
    if [ -f "data/proxy/endpoints.json" ]; then
        endpoint_count=$(jq -r 'keys | length' data/proxy/endpoints.json 2>/dev/null || echo "0")
        if [ "$endpoint_count" -gt 0 ]; then
            log_info "✓ Found $endpoint_count configured endpoint(s)"
        else
            log_warn "⚠ No endpoints configured"
        fi
    else
        log_warn "⚠ Endpoints configuration file not found"
    fi
}

check_docker_container() {
    log_info "Checking Caddy Docker container..."
    
    if docker-compose ps caddy | grep -q "Up"; then
        log_info "✓ Caddy container is running"
        
        # Check container health
        health_status=$(docker inspect --format='{{.State.Health.Status}}' stealth-caddy 2>/dev/null || echo "unknown")
        case $health_status in
            "healthy")
                log_info "✓ Container health status: healthy"
                ;;
            "unhealthy")
                log_error "✗ Container health status: unhealthy"
                return 1
                ;;
            "starting")
                log_warn "⚠ Container health status: starting"
                ;;
            *)
                log_warn "⚠ Container health status: $health_status"
                ;;
        esac
        
        return 0
    else
        log_error "✗ Caddy container is not running"
        return 1
    fi
}

show_container_logs() {
    log_info "Recent Caddy container logs:"
    echo "----------------------------------------"
    docker-compose logs --tail=10 caddy 2>/dev/null || echo "Could not retrieve logs"
    echo "----------------------------------------"
}

main() {
    echo "🔍 Caddy Health Check - Multi-Protocol Proxy Server"
    echo "===================================================="
    
    local exit_code=0
    
    # Run all checks
    check_docker_container || exit_code=1
    check_config_syntax || exit_code=1
    check_caddy_admin || exit_code=1
    check_caddy_web || exit_code=1
    check_certificates
    check_endpoints
    
    echo ""
    
    if [ $exit_code -eq 0 ]; then
        log_info "🎉 All health checks passed!"
        echo ""
        log_info "Caddy is running properly and ready to serve traffic."
    else
        log_error "❌ Some health checks failed!"
        echo ""
        show_container_logs
        echo ""
        log_error "Please check the logs and configuration."
    fi
    
    exit $exit_code
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi