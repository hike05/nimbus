# Multi-Protocol Proxy Server - Admin Panel

Flask-based admin panel for managing proxy users and configurations, masqueraded as a cloud storage management interface.

## Features

### User Management
- Create new proxy users with auto-generated credentials
- View all users with status and activity information
- Delete users and their configurations
- Generate client configurations for all protocols

### Configuration Management
- Update all proxy server configurations
- Graceful service reload without disconnecting users
- Backup and restore functionality
- Download client configuration files

### Supported Protocols
- **Xray**: VLESS-XTLS-Vision and WebSocket
- **Trojan-Go**: With WebSocket transport
- **Sing-box**: ShadowTLS v3, Hysteria2, TUIC v5
- **WireGuard**: With obfuscation options

### Client Configuration Generation
- JSON configuration files
- Connection links (vless://, trojan://, etc.)
- QR codes for mobile apps
- WireGuard .conf files

## Environment Variables

```bash
# Admin credentials
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=<bcrypt_hash>

# Server configuration
DOMAIN=your-domain.com
DATA_DIR=/app/data

# Session security
SESSION_SECRET=<random_secret>
```

## Generating Admin Password Hash

```python
import bcrypt
password = b"your_secure_password"
hash = bcrypt.hashpw(password, bcrypt.gensalt())
print(hash.decode('utf-8'))
```

## API Endpoints

All endpoints are masqueraded as cloud storage API:

### Authentication
- `GET /api/v2/storage/login` - Login page
- `POST /api/v2/storage/auth` - Authenticate
- `POST /api/v2/storage/logout` - Logout

### User Management (masqueraded as "files")
- `GET /api/v2/storage/upload` - Admin panel UI
- `GET /api/v2/storage/files` - List users
- `POST /api/v2/storage/files` - Create user
- `DELETE /api/v2/storage/files/<username>` - Delete user
- `GET /api/v2/storage/files/<username>/download` - Get configs
- `GET /api/v2/storage/files/<username>/qrcode/<protocol>` - Get QR code

### Configuration Management
- `GET /api/v2/storage/status` - System status
- `POST /api/v2/storage/configs/update` - Update all configs
- `POST /api/v2/storage/services/<service>/reload` - Reload service

### Backup Management
- `POST /api/v2/storage/backup` - Create backup
- `GET /api/v2/storage/backup` - List backups
- `DELETE /api/v2/storage/backup/<name>` - Delete backup
- `POST /api/v2/storage/backup/<name>/restore` - Restore backup
- `GET /api/v2/storage/backup/<name>/download` - Download backup

## Directory Structure

```
admin-panel/
├── app.py                      # Main Flask application
├── core/                       # Core modules
│   ├── user_storage.py        # User data management
│   ├── config_generator.py    # Config generation
│   ├── service_manager.py     # Service management
│   ├── client_config_manager.py # Client configs
│   └── backup_manager.py      # Backup/restore
├── templates/                  # HTML templates
│   ├── base.html              # Base template
│   ├── login.html             # Login page
│   └── admin.html             # Admin panel
├── static/                     # Static assets (CSS/JS)
├── Dockerfile                  # Container definition
└── requirements.txt            # Python dependencies
```

## Usage

### Creating a User

1. Log in to admin panel at `/api/v2/storage/login`
2. Click "Upload New File" button
3. Enter username (e.g., "alice")
4. System automatically generates:
   - UUID for Xray
   - WireGuard key pair
   - Trojan password
   - Sing-box credentials
5. Client configurations saved to `/data/proxy/configs/clients/<username>/`

### Downloading Client Configs

1. Click the eye icon next to a user
2. View configurations in tabs:
   - Xray XTLS (JSON + link)
   - Xray WebSocket (JSON + link)
   - Trojan (JSON + link)
   - WireGuard (.conf file)
   - QR Codes (for mobile)
3. Copy links or download files

### Backup and Restore

1. Click "Create Backup" to save current state
2. Click "View Backups" to see all backups
3. Restore a backup to revert to previous state
4. Download backups for external storage

### Service Management

- Click "Reload All Services" to apply configuration changes
- Services reload gracefully without disconnecting users
- Health status shown in dashboard

## Security Features

- **Obfuscated Interface**: Looks like cloud storage management
- **Session Management**: 24-hour sessions with secure cookies
- **Password Hashing**: bcrypt for admin password
- **Automatic Backups**: Before any destructive operation
- **Rate Limiting**: Protection against brute force (via Caddy)

## Integration with Proxy Services

The admin panel automatically:
1. Updates server configurations when users are added/removed
2. Generates client configs for all protocols
3. Reloads services gracefully
4. Maintains backup history

## Troubleshooting

### Cannot login
- Check `ADMIN_PASSWORD_HASH` environment variable
- Verify bcrypt hash is correct
- Check container logs: `docker logs web`

### Configs not updating
- Check file permissions in `/data/proxy/`
- Verify Docker socket access for service management
- Check service logs for errors

### QR codes not generating
- Ensure `qrcode[pil]` package is installed
- Check Pillow dependencies in container

## Development

Run locally for testing:

```bash
cd admin-panel
pip install -r requirements.txt
export ADMIN_USERNAME=admin
export ADMIN_PASSWORD_HASH=<hash>
export DOMAIN=localhost
export DATA_DIR=./test-data
python app.py
```

Access at: http://localhost:8010/api/v2/storage/login
