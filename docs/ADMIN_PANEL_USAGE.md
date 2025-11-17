# Admin Panel Usage Guide

Complete guide for using the Stealth VPN Server admin panel.

## Table of Contents

1. [Initial Setup](#initial-setup)
2. [Accessing the Admin Panel](#accessing-the-admin-panel)
3. [User Management](#user-management)
4. [Configuration Management](#configuration-management)
5. [Backup and Restore](#backup-and-restore)
6. [Client Setup](#client-setup)
7. [Troubleshooting](#troubleshooting)

## Initial Setup

### 1. Generate Admin Credentials

Before starting the admin panel, generate a secure password hash:

```bash
# Generate password hash and session secret
python3 admin-panel/setup_admin.py your-secure-password
```

This will output:

```
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=$2b$12$...
SESSION_SECRET=abc123...
```

### 2. Update .env File

Add the generated values to your `.env` file:

```bash
# Copy from .env.example if not exists
cp .env.example .env

# Edit .env and add:
DOMAIN=your-domain.com
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=$2b$12$...
SESSION_SECRET=abc123...
```

### 3. Start Services

```bash
docker compose up -d
```

The admin panel will be available at: `https://your-domain.com/api/v2/storage/login`

## Accessing the Admin Panel

### Login URL

The admin panel is obfuscated to look like a cloud storage API:

```
https://your-domain.com/api/v2/storage/login
```

### Login Credentials

- **Username**: Value from `ADMIN_USERNAME` (default: `admin`)
- **Password**: The password you used to generate the hash

### Security Features

- **Session Duration**: 24 hours
- **Rate Limiting**: 5 login attempts per minute (configured in Caddy)
- **HTTPS Only**: All traffic encrypted
- **Obfuscated Paths**: Looks like cloud storage API

## User Management

### Creating a New User

1. Click **"Upload New File"** button
2. Enter a username (e.g., `alice`, `bob`, `user1`)
3. Click **"Upload"**

The system automatically generates:
- Unique UUID for Xray protocols
- WireGuard key pair (private and public keys)
- Trojan-Go password
- Sing-box credentials (ShadowTLS, Hysteria2, TUIC)
- Client configuration files

### Viewing Users

The main dashboard shows all users with:
- **Filename**: Username
- **Created**: Creation timestamp
- **Last Access**: Last connection time (if available)
- **Status**: Active/Inactive badge
- **Actions**: View configs, Delete

### Viewing Client Configurations

1. Click the **eye icon** (👁️) next to a user
2. View configurations in tabs:
   - **Xray XTLS**: VLESS-XTLS-Vision protocol
   - **Xray WS**: VLESS-WebSocket protocol
   - **Trojan**: Trojan-Go protocol
   - **WireGuard**: WireGuard configuration
   - **QR Codes**: QR codes for mobile apps

### Downloading Configurations

**Connection Links** (for mobile apps):
- Click the clipboard icon to copy
- Paste into VPN client app

**JSON Configs** (for desktop):
- Copy the JSON configuration
- Save to a file
- Import into VPN client

**WireGuard .conf**:
- Click "Download .conf" button
- Import into WireGuard app

**QR Codes** (for mobile):
- Open QR Codes tab
- Scan with mobile VPN app

### Deleting a User

1. Click the **trash icon** (🗑️) next to a user
2. Confirm deletion
3. User and all configurations are removed
4. Server configurations are automatically updated

## Configuration Management

### Dashboard Overview

The dashboard shows:
- **Services**: Number of active VPN services
- **Total Files**: Total number of users
- **Active Files**: Number of active users
- **Server**: Your domain name

### Service Status

Each VPN service shows its health status:
- ✅ **Green**: Service running
- ❌ **Red**: Service down

### Updating Configurations

When you add or remove users, configurations are automatically updated. To manually reload:

1. Click **"Reload All Services"**
2. Confirm the action
3. All VPN services reload gracefully (no disconnections)

### Manual Service Reload

To reload a specific service:

```bash
# Via API (requires authentication)
curl -X POST https://your-domain.com/api/v2/storage/services/xray/reload \
  -H "Cookie: session=..."
```

## Backup and Restore

### Creating a Backup

1. Click **"Create Backup"** button
2. Backup is created with timestamp
3. Includes:
   - All user data
   - Server configurations
   - Client configuration files

### Viewing Backups

1. Click **"View Backups"** button
2. See list of all backups with:
   - Timestamp
   - Description
   - File size
   - Actions (Restore, Download, Delete)

### Restoring a Backup

1. Click **"View Backups"**
2. Find the backup to restore
3. Click the **restore icon** (↻)
4. Confirm restoration
5. All services automatically reload

**⚠️ Warning**: Restoring a backup will overwrite current configurations. A safety backup is created automatically before restoration.

### Downloading Backups

1. Click **"View Backups"**
2. Click the **download icon** (⬇️) next to a backup
3. Save the `.tar.gz` file to your computer

Store backups externally for disaster recovery.

### Deleting Backups

1. Click **"View Backups"**
2. Click the **trash icon** (🗑️) next to a backup
3. Confirm deletion

**Note**: The system keeps the 20 most recent backups automatically.

## Client Setup

### Mobile Clients

#### iOS

**Xray Protocols**:
1. Install **Shadowrocket** from App Store
2. Open admin panel and view user configs
3. Go to QR Codes tab
4. Scan QR code with Shadowrocket

**WireGuard**:
1. Install **WireGuard** from App Store
2. Scan WireGuard QR code
3. Or download .conf file and import

#### Android

**Xray Protocols**:
1. Install **v2rayNG** from Play Store
2. Scan QR code from admin panel
3. Or copy connection link and import

**Trojan**:
1. Install **Clash for Android**
2. Copy Trojan link
3. Import into Clash

**WireGuard**:
1. Install **WireGuard** from Play Store
2. Scan QR code or import .conf file

### Desktop Clients

#### Windows

**Xray**:
1. Download **v2rayN** client
2. Copy JSON config from admin panel
3. Import into v2rayN

**WireGuard**:
1. Download **WireGuard** for Windows
2. Import .conf file

#### macOS

**Xray**:
1. Download **V2RayX** or **Qv2ray**
2. Import JSON configuration

**WireGuard**:
1. Install **WireGuard** from App Store
2. Import .conf file

#### Linux

**Xray**:
```bash
# Install xray-core
sudo apt install xray

# Copy config to /etc/xray/config.json
sudo systemctl start xray
```

**WireGuard**:
```bash
# Install WireGuard
sudo apt install wireguard

# Copy .conf to /etc/wireguard/wg0.conf
sudo wg-quick up wg0
```

### Connection Testing

After setup, test the connection:

1. Connect to VPN
2. Check IP address: `curl ifconfig.me`
3. Should show your VPS IP
4. Test DNS: `nslookup google.com`

## Troubleshooting

### Cannot Login to Admin Panel

**Problem**: Login fails with "Invalid credentials"

**Solutions**:
1. Verify password hash in `.env` file
2. Regenerate hash: `python3 admin-panel/setup_admin.py new-password`
3. Update `.env` and restart: `docker compose restart admin`
4. Check logs: `docker logs stealth-admin`

### User Creation Fails

**Problem**: Error when creating new user

**Solutions**:
1. Check disk space: `df -h`
2. Verify permissions: `ls -la data/stealth-vpn/`
3. Check logs: `docker logs stealth-admin`
4. Ensure WireGuard tools available in container

### Configurations Not Updating

**Problem**: Changes not reflected in VPN services

**Solutions**:
1. Click "Reload All Services" in admin panel
2. Manually restart services:
   ```bash
   docker compose restart xray trojan singbox wireguard
   ```
3. Check service logs:
   ```bash
   docker logs stealth-xray
   docker logs stealth-trojan
   ```

### QR Codes Not Generating

**Problem**: QR code images don't load

**Solutions**:
1. Check if `qrcode[pil]` is installed in container
2. Rebuild admin container:
   ```bash
   docker compose build admin
   docker compose up -d admin
   ```
3. Check logs for PIL/Pillow errors

### Backup Fails

**Problem**: Cannot create or restore backup

**Solutions**:
1. Check disk space: `df -h`
2. Verify backup directory permissions:
   ```bash
   ls -la data/stealth-vpn/backups/
   ```
3. Check logs: `docker logs stealth-admin`

### Service Won't Reload

**Problem**: Service reload fails

**Solutions**:
1. Check if Docker socket is mounted:
   ```bash
   docker exec stealth-admin ls -la /var/run/docker.sock
   ```
2. Verify container names match in docker-compose.yml
3. Manually restart service:
   ```bash
   docker restart stealth-xray
   ```

### Admin Panel Not Accessible

**Problem**: Cannot access admin panel URL

**Solutions**:
1. Check Caddy configuration:
   ```bash
   docker logs stealth-caddy
   ```
2. Verify admin container is running:
   ```bash
   docker ps | grep admin
   ```
3. Check Caddyfile has admin panel route:
   ```bash
   grep "api/v2/storage" config/Caddyfile
   ```
4. Test admin panel directly:
   ```bash
   curl http://localhost:8010/health
   ```

## API Reference

For advanced users, the admin panel exposes a REST API:

### Authentication
```bash
POST /api/v2/storage/auth
Content-Type: application/json

{
  "username": "admin",
  "password": "your-password"
}
```

### List Users
```bash
GET /api/v2/storage/files
Cookie: session=...
```

### Create User
```bash
POST /api/v2/storage/files
Cookie: session=...
Content-Type: application/json

{
  "filename": "newuser"
}
```

### Delete User
```bash
DELETE /api/v2/storage/files/username
Cookie: session=...
```

### Get Configurations
```bash
GET /api/v2/storage/files/username/download
Cookie: session=...
```

### Create Backup
```bash
POST /api/v2/storage/backup
Cookie: session=...
Content-Type: application/json

{
  "description": "Manual backup"
}
```

### Restore Backup
```bash
POST /api/v2/storage/backup/backup_20250107_120000.tar.gz/restore
Cookie: session=...
```

## Security Best Practices

1. **Strong Password**: Use a long, random password for admin account
2. **Regular Backups**: Create backups before major changes
3. **External Storage**: Download and store backups externally
4. **Monitor Logs**: Regularly check logs for suspicious activity
5. **Update Regularly**: Keep Docker images updated
6. **Limit Access**: Use firewall rules to restrict admin panel access
7. **HTTPS Only**: Never access admin panel over HTTP
8. **Session Timeout**: Sessions expire after 24 hours

## Additional Resources

- [Main README](../README.md)
- [Installation Guide](../install.sh)
- [Xray Configuration](./XRAY_USAGE.md)
- [WireGuard Configuration](./WIREGUARD_USAGE.md)
- [Sing-box Configuration](./SINGBOX_USAGE.md)
