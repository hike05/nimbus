#!/bin/bash

# Trojan-Go Setup Script
# Sets up Trojan-Go service with proper configuration and integration

set -e

echo "Setting up Trojan-Go service..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    print_error "This script should not be run as root"
    exit 1
fi

# Check if Docker is installed and running
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! docker info &> /dev/null; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    print_error "Docker Compose is not available. Please install Docker Compose."
    exit 1
fi

# Create necessary directories
print_status "Creating directory structure..."
mkdir -p data/proxy/logs/trojan
mkdir -p data/proxy/configs/clients
chmod 755 data/proxy/logs/trojan

# Set proper permissions
print_status "Setting permissions..."
if [ -f "data/proxy/configs/trojan.json" ]; then
    chmod 600 data/proxy/configs/trojan.json
fi

if [ -f "data/proxy/configs/trojan.template.json" ]; then
    chmod 644 data/proxy/configs/trojan.template.json
fi

# Test Trojan configuration
print_status "Testing Trojan configuration..."
if python3 scripts/test-trojan-integration.py; then
    print_status "✓ Trojan configuration tests passed"
else
    print_error "✗ Trojan configuration tests failed"
    exit 1
fi

# Generate initial Trojan configuration
print_status "Generating initial Trojan server configuration..."
if python3 scripts/trojan-config-manager.py generate-server; then
    print_status "✓ Trojan server configuration generated"
else
    print_error "✗ Failed to generate Trojan server configuration"
    exit 1
fi

# Build Trojan container
print_status "Building Trojan-Go container..."
if docker build -t trojan ./trojan; then
    print_status "✓ Trojan-Go container built successfully"
else
    print_error "✗ Failed to build Trojan-Go container"
    exit 1
fi

# Check if services are already running
if docker-compose ps | grep -q "trojan"; then
    print_warning "Trojan proxy service is already running. Restarting..."
    docker-compose restart trojan
else
    print_status "Starting Trojan proxy service..."
    docker-compose up -d trojan
fi

# Wait for service to start
print_status "Waiting for Trojan proxy service to start..."
sleep 10

# Check service health
if docker-compose ps trojan | grep -q "Up"; then
    print_status "✓ Trojan proxy service is running"
else
    print_error "✗ Trojan proxy service failed to start"
    print_error "Checking logs..."
    docker-compose logs trojan
    exit 1
fi

# Verify configuration
print_status "Verifying Trojan configuration..."
if [ -f "data/proxy/configs/trojan.json" ]; then
    if python3 -m json.tool data/proxy/configs/trojan.json > /dev/null; then
        print_status "✓ Trojan configuration is valid JSON"
    else
        print_error "✗ Trojan configuration is invalid JSON"
        exit 1
    fi
else
    print_error "✗ Trojan configuration file not found"
    exit 1
fi

# Test service connectivity
print_status "Testing Trojan proxy service connectivity..."
if docker exec trojan pgrep trojan-go > /dev/null; then
    print_status "✓ Trojan-Go process is running"
else
    print_error "✗ Trojan-Go process is not running"
    docker-compose logs trojan
    exit 1
fi

# Display service information
print_status "Trojan-Go proxy service setup completed!"
echo
echo "Service Information:"
echo "  - Container: trojan"
echo "  - Internal Port: 8002"
echo "  - External Port: 443 (via Caddy)"
echo "  - Protocol: Trojan-Go with TLS"
echo "  - WebSocket Path: /api/v1/files/sync"
echo "  - SNI: www.your-domain.com"
echo
echo "Configuration Files:"
echo "  - Server Config: data/proxy/configs/trojan.json"
echo "  - Template: data/proxy/configs/trojan.template.json"
echo "  - Logs: data/proxy/logs/trojan/"
echo
echo "Management Commands:"
echo "  - Generate server config: python3 scripts/trojan-config-manager.py generate-server"
echo "  - Generate client config: python3 scripts/trojan-config-manager.py generate-client <username>"
echo "  - Add user password: python3 scripts/trojan-config-manager.py add-password <username>"
echo "  - View logs: docker-compose logs trojan"
echo "  - Restart service: docker-compose restart trojan"
echo
print_status "Trojan-Go proxy service is ready for use!"

# Check if domain is configured
if grep -q "your-domain.com" data/proxy/configs/trojan.json; then
    print_warning "Remember to replace 'your-domain.com' with your actual domain name"
    print_warning "Update the configuration files and restart the service after domain setup"
fi