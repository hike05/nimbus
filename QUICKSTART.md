# Stealth VPN Server - Quick Start Guide

This guide will help you get your Stealth VPN Server up and running in minutes.

## Prerequisites

- Ubuntu 20.04+ or Debian 11+ server
- Root or sudo access
- Domain name pointing to your server's IP address
- Ports 80 and 443 accessible from the internet

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/stealth-vpn-server.git
cd stealth-vpn-server
```

### 2. Run the Installation Script

The installation script will:
- Install Docker and Docker Compose
- Configure firewall rules
- Generate configuration files
- Set up data directories
- Build Docker images

```bash
chmod +x install.sh
./install.sh
```

During installation, you'll be prompted for:
- **Domain name**: Your domain (e.g., example.com)
- **Email**: For Let's Encrypt SSL certificates
- **Admin password**: For the admin panel (or leave empty for random)

### 3. Verify Configuration

Check your `.env` file to ensure all settings are correct:

```bash
cat .env
```

Key settings to verify:
- `DOMAIN`: Your actual domain name
- `ADMIN_PASSWORD_HASH`: Should be populated
- `SESSION_SECRET`: Should be populated

### 4. Start Services

If you didn't start services during installation:

```bash
docker compose up -d
```

### 5. Check Service Status

```bash
docker compose ps
```

All services should show as "healthy" after a minute or two.

## Accessing the Admin Panel

The admin panel is disguised as a storage API endpoint:

```
https://your-domain.com/api/v2/storage/upload
```

Login with:
- **Username**: `admin` (or what you set in `.env`)
- **Password**: The password you set during installation

## Adding Your First VPN User

### Option 1: Using the Admin Panel

1. Navigate to the admin panel
2. Click "Add New User"
3. Enter a username
4. Click "Create"
5. Download the client configurations

### Option 2: Using Command Line

```bash
# Add a user
python3 scripts/xray-config-manager.py add-user alice

# List all users
python3 scripts/xray-config-manager.py list-users

# Generate client configs
python3 admin-panel/core/client_config_manager.py alice
```

## Client Configuration

After creating a user, you'll receive configuration files for different protocols:

### Xray (VLESS)
- **XTLS-Vision**: Best performance, TCP-based
- **WebSocket**: Fallback option, works through most firewalls

### Trojan-Go
- TLS-based protocol with WebSocket support

### Sing-box
- **ShadowTLS v3**: Advanced obfuscation
- **Hysteria 2**: High-speed UDP-based (QUIC)
- **TUIC v5**: Modern QUIC protocol

### WireGuard
- **WebSocket**: WireGuard over HTTPS WebSocket
- **udp2raw**: UDP disguised as TCP

## Service Management

### Using the Service Manager Script

```bash
# Start all services
./scripts/service-manager.sh start

# Stop all services
./scripts/service-manager.sh stop

# Restart a specific service
./scripts/service-manager.sh restart xray

# View logs
./scripts/service-manager.sh logs caddy 100

# Check health
./scripts/service-manager.sh health

# Create backup
./scripts/service-manager.sh backup
```

### Using Docker Compose Directly

```bash
# Start services
docker compose up -d

# Stop services
docker compose down

# Restart a service
docker compose restart xray

# View logs
docker compose logs -f xray

# Check status
docker compose ps
```

## Health Checks

Run the health check script to verify all services are working:

```bash
./scripts/health-check.sh
```

This will check:
- Caddy web server
- SSL certificates
- VPN services (Xray, Trojan, Sing-box, WireGuard)
- Admin panel
- Network connectivity

## Updating the System

To update your Stealth VPN Server:

```bash
./scripts/update-system.sh update
```

This will:
1. Create a backup
2. Pull latest code
3. Update Docker images
4. Migrate configurations
5. Restart services
6. Verify the update

If something goes wrong, rollback:

```bash
./scripts/update-system.sh rollback
```

## Troubleshooting

### Services Won't Start

Check logs for errors:
```bash
docker compose logs -f
```

### SSL Certificate Issues

Ensure:
- Your domain points to the server's IP
- Ports 80 and 443 are accessible
- No other web server is running

Check Caddy logs:
```bash
docker compose logs -f caddy
```

### VPN Connection Issues

1. Check service status:
   ```bash
   docker compose ps
   ```

2. Verify configurations:
   ```bash
   python3 scripts/xray-config-manager.py test
   python3 scripts/trojan-config-manager.py test
   ```

3. Check firewall:
   ```bash
   sudo ufw status
   ```

### Admin Panel Not Accessible

1. Check admin service:
   ```bash
   docker compose logs -f admin
   ```

2. Verify Caddy routing:
   ```bash
   docker compose logs -f caddy | grep admin
   ```

3. Check `.env` configuration:
   ```bash
   grep ADMIN .env
   ```

## Security Best Practices

1. **Change Default Passwords**: Always use strong, unique passwords
2. **Keep System Updated**: Run `./scripts/update-system.sh update` regularly
3. **Monitor Logs**: Check logs periodically for suspicious activity
4. **Backup Regularly**: Use `./scripts/service-manager.sh backup`
5. **Limit Admin Access**: Use VPN or IP whitelist for admin panel
6. **Rotate Endpoints**: Enable endpoint rotation in `.env` for additional obfuscation

## Next Steps

- Read the full documentation in `docs/`
- Configure additional protocols
- Set up monitoring and alerting
- Customize the cover website
- Enable endpoint rotation

## Getting Help

- Check the documentation in `docs/`
- Review logs: `docker compose logs -f`
- Run health checks: `./scripts/health-check.sh`
- Check GitHub issues

## Useful Commands Reference

```bash
# Service Management
./scripts/service-manager.sh start|stop|restart [service]
./scripts/service-manager.sh logs [service] [lines]
./scripts/service-manager.sh health
./scripts/service-manager.sh backup

# User Management
python3 scripts/xray-config-manager.py add-user <username>
python3 scripts/xray-config-manager.py remove-user <username>
python3 scripts/xray-config-manager.py list-users

# System Updates
./scripts/update-system.sh update
./scripts/update-system.sh rollback

# Health Checks
./scripts/health-check.sh
./scripts/caddy-health.sh

# Docker Commands
docker compose ps                    # Service status
docker compose logs -f [service]     # View logs
docker compose restart [service]     # Restart service
docker compose down                  # Stop all
docker compose up -d                 # Start all
```

## Support

For issues and questions:
- GitHub Issues: https://github.com/yourusername/stealth-vpn-server/issues
- Documentation: `docs/` directory
- Admin Panel Guide: `docs/ADMIN_PANEL_USAGE.md`
