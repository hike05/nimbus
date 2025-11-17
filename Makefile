.PHONY: help install start stop restart status logs health backup restore update clean

# Default target
help:
	@echo "Stealth VPN Server - Available Commands"
	@echo ""
	@echo "Installation:"
	@echo "  make install          Install and configure the system"
	@echo ""
	@echo "Service Management:"
	@echo "  make start            Start all services"
	@echo "  make stop             Stop all services"
	@echo "  make restart          Restart all services"
	@echo "  make status           Show service status"
	@echo "  make logs             Show logs for all services"
	@echo "  make logs-SERVICE     Show logs for specific service (e.g., make logs-xray)"
	@echo ""
	@echo "Health & Monitoring:"
	@echo "  make health           Run health checks"
	@echo "  make ps               Show running containers"
	@echo ""
	@echo "User Management:"
	@echo "  make add-user USER=username    Add a new VPN user"
	@echo "  make list-users                List all VPN users"
	@echo "  make remove-user USER=username Remove a VPN user"
	@echo ""
	@echo "Maintenance:"
	@echo "  make backup           Create configuration backup"
	@echo "  make restore FILE=... Restore from backup"
	@echo "  make update           Update system and services"
	@echo "  make rebuild          Rebuild all Docker images"
	@echo "  make clean            Clean up unused Docker resources"
	@echo ""
	@echo "Security:"
	@echo "  make security-test    Run security hardening tests"
	@echo "  make apply-obfuscation Apply traffic obfuscation"
	@echo "  make security-audit   Full security audit"
	@echo ""
	@echo "Development:"
	@echo "  make build            Build Docker images"
	@echo "  make test             Run integration tests"
	@echo "  make validate         Validate configurations"
	@echo ""

# Installation
install:
	@echo "Running installation script..."
	@chmod +x install.sh
	@./install.sh

# Service Management
start:
	@echo "Starting all services..."
	@docker compose up -d
	@echo "Services started. Run 'make status' to check."

stop:
	@echo "Stopping all services..."
	@docker compose down
	@echo "Services stopped."

restart:
	@echo "Restarting all services..."
	@docker compose restart
	@echo "Services restarted. Run 'make status' to check."

status:
	@docker compose ps

logs:
	@docker compose logs -f

logs-%:
	@docker compose logs -f $*

ps:
	@docker compose ps

# Health & Monitoring
health:
	@echo "Running health checks..."
	@./scripts/health-check.sh

# User Management
add-user:
ifndef USER
	@echo "Error: USER not specified. Usage: make add-user USER=username"
	@exit 1
endif
	@echo "Adding user: $(USER)"
	@python3 scripts/xray-config-manager.py add-user $(USER)

list-users:
	@python3 scripts/xray-config-manager.py list-users

remove-user:
ifndef USER
	@echo "Error: USER not specified. Usage: make remove-user USER=username"
	@exit 1
endif
	@echo "Removing user: $(USER)"
	@python3 scripts/xray-config-manager.py remove-user $(USER)

# Maintenance
backup:
	@echo "Creating backup..."
	@./scripts/service-manager.sh backup

restore:
ifndef FILE
	@echo "Error: FILE not specified. Usage: make restore FILE=backup.tar.gz"
	@exit 1
endif
	@echo "Restoring from: $(FILE)"
	@./scripts/service-manager.sh restore $(FILE)

update:
	@echo "Updating system..."
	@./scripts/update-system.sh update

rebuild:
	@echo "Rebuilding all Docker images..."
	@docker compose build --no-cache
	@docker compose up -d
	@echo "Rebuild complete."

clean:
	@echo "Cleaning up unused Docker resources..."
	@docker container prune -f
	@docker image prune -f
	@docker network prune -f
	@echo "Cleanup complete."

# Development
build:
	@echo "Building Docker images..."
	@docker compose build

test:
	@echo "Running integration tests..."
	@python3 scripts/test-xray-integration.py
	@python3 scripts/test-trojan-integration.py
	@python3 scripts/test-singbox-integration.py
	@python3 scripts/test-wireguard-integration.py

validate:
	@echo "Validating configurations..."
	@python3 scripts/xray-config-manager.py validate
	@python3 scripts/trojan-config-manager.py validate
	@python3 scripts/singbox-config-manager.py validate
	@echo "Validation complete."

# Security
security-test:
	@echo "Running security hardening tests..."
	@python3 scripts/test-security-hardening.py

apply-obfuscation:
	@echo "Applying traffic obfuscation to all protocols..."
	@python3 scripts/apply-traffic-obfuscation.py
	@echo "Restarting services to apply changes..."
	@docker compose restart xray trojan singbox wireguard
	@echo "Traffic obfuscation applied."

security-audit: security-test
	@echo ""
	@echo "Running additional security checks..."
	@echo "Checking for security updates..."
	@docker compose images
	@echo ""
	@echo "Checking container vulnerabilities..."
	@echo "Note: Install trivy for vulnerability scanning: https://github.com/aquasecurity/trivy"
	@echo ""
	@echo "Security audit complete. Review results above."

# Quick shortcuts
up: start
down: stop
