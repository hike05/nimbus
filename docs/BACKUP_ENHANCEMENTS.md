# Backup System Enhancements

## Overview

The backup system has been enhanced to include additional system components and provide better metadata tracking.

## What's New

### Enhanced Backup Contents (v2.0)

Backups now include:
- **User configurations** (users.json)
- **VPN server configs** (Xray, Trojan, Sing-box, WireGuard)
- **Client configurations** (all generated client configs)
- **SSL certificates** (from Caddy, if accessible)
- **Caddyfile** (reverse proxy configuration)
- **docker-compose.yml** (container orchestration config)

### Improved Metadata

Each backup now includes:
- **Version number** (v2.0 for enhanced backups)
- **Timestamp** (both filename format and ISO 8601)
- **Description** (user-provided or default)
- **File size** (bytes and human-readable format)
- **Included items list** (what was successfully backed up)

### UI Improvements

- **Create Backup Modal**: Add optional descriptions when creating backups
- **Enhanced Backup List**: Shows version, size, and included items for each backup
- **Better Visualization**: Version badges and item counts for quick identification
- **Backward Compatibility**: Old v1.0 backups are still supported and displayed

## Usage

### Creating a Backup

1. Click "Create Backup" button
2. Enter an optional description (e.g., "Before major update", "Weekly backup")
3. Click "Create Backup" to confirm
4. The system will create a compressed archive with all available components

### Managing Backups

1. Click "Manage Backups" to view all backups
2. Each backup shows:
   - Creation timestamp
   - Description
   - Size
   - Version (v1.0 or v2.0)
   - Included items
3. Available actions:
   - **Restore**: Restore configurations from backup
   - **Download**: Download backup file
   - **Delete**: Remove backup

### Restoring a Backup

1. Open "Manage Backups"
2. Click the restore button (↻) for the desired backup
3. Confirm the restoration
4. The system will:
   - Create a safety backup before restoring
   - Extract and restore all configurations
   - Reload affected services

## Technical Details

### Volume Mounts Required

The following volume mounts have been added to the admin container in `docker-compose.yml`:

```yaml
- ./data/caddy/certificates:/data/caddy/certificates:ro
- ./config/Caddyfile:/etc/caddy/Caddyfile:ro
- ./docker-compose.yml:/app/docker-compose.yml:ro
```

### Backup Structure

Enhanced backups (v2.0) use the following structure:

```
backup_YYYYMMDD_HHMMSS.tar.gz
├── configs/
│   ├── users.json
│   ├── xray.json
│   ├── trojan.json
│   ├── singbox.json
│   ├── wireguard/
│   └── clients/
├── certificates/
│   └── [SSL certificate files]
├── Caddyfile
└── docker-compose.yml
```

### Metadata File

Each backup has an accompanying JSON metadata file:

```json
{
  "version": "2.0",
  "timestamp": "20241118_143022",
  "description": "Manual backup",
  "filename": "backup_20241118_143022.tar.gz",
  "size": 1048576,
  "included_items": [
    "users.json",
    "xray.json",
    "trojan.json",
    "singbox.json",
    "wireguard configs",
    "client configs",
    "SSL certificates",
    "Caddyfile",
    "docker-compose.yml"
  ],
  "created_at": "2024-11-18T14:30:22Z"
}
```

## API Changes

### POST /admin/backup

**Request:**
```json
{
  "description": "Optional backup description"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Backup created successfully",
  "backup_name": "backup_20241118_143022.tar.gz",
  "metadata": {
    "version": "2.0",
    "timestamp": "20241118_143022",
    "description": "Manual backup",
    "filename": "backup_20241118_143022.tar.gz",
    "size": 1048576,
    "size_human": "1.00 MB",
    "included_items": [...],
    "created_at": "2024-11-18T14:30:22Z"
  }
}
```

### GET /admin/backup

Returns list of all backups with enhanced metadata including `size_human` and `included_items`.

### GET /admin/backup/<backup_name>

New endpoint to get metadata for a specific backup.

**Response:**
```json
{
  "success": true,
  "metadata": {
    "version": "2.0",
    "timestamp": "20241118_143022",
    "description": "Manual backup",
    "filename": "backup_20241118_143022.tar.gz",
    "size": 1048576,
    "size_human": "1.00 MB",
    "included_items": [...],
    "created_at": "2024-11-18T14:30:22Z"
  }
}
```

## Backward Compatibility

- Old v1.0 backups are fully supported
- Missing metadata fields are automatically filled with defaults
- Restoration works for both v1.0 and v2.0 backups
- UI displays appropriate information for both versions

## Notes

- SSL certificates, Caddyfile, and docker-compose.yml are backed up only if accessible (read permissions)
- If any component cannot be backed up, a warning is logged but the backup continues
- docker-compose.yml is NOT automatically restored (requires manual intervention and container restart)
- A safety backup is automatically created before any restoration
- The system keeps the last 20 backups automatically
