# Endpoint Obfuscation System

## Overview

The endpoint obfuscation system generates realistic-looking paths for VPN services to avoid detection. All VPN endpoints are disguised as legitimate web resources like JavaScript files, fonts, and API endpoints.

## Features

- **Realistic Path Generation**: Generates paths that look like real web resources
- **Automatic Rotation**: Supports scheduled rotation of endpoints
- **Backup System**: Automatically backs up old endpoints before rotation
- **Validation**: Validates endpoint configurations before applying
- **Integration**: Seamlessly integrates with all VPN services

## Components

### 1. EndpointManager (`core/endpoint_manager.py`)

Core module for managing obfuscated endpoints.

**Key Methods:**
- `generate_endpoints()` - Generate new obfuscated endpoints
- `rotate_endpoints()` - Rotate endpoints if needed
- `validate_endpoints()` - Validate endpoint configuration
- `get_endpoint_by_service()` - Get endpoint for specific service
- `should_rotate()` - Check if rotation is needed

### 2. Generate Endpoints Script (`scripts/generate-endpoints.py`)

CLI tool for managing endpoints.

**Usage:**
```bash
# Generate initial endpoints
python3 scripts/generate-endpoints.py

# Show current endpoint statistics
python3 scripts/generate-endpoints.py --stats

# Validate current endpoints
python3 scripts/generate-endpoints.py --validate

# Force rotation regardless of age
python3 scripts/generate-endpoints.py --force
```

### 3. Admin Panel Integration

The admin panel automatically loads and uses obfuscated endpoints.

**New API Endpoints:**
- `GET /api/v2/storage/endpoints` - Get current endpoints
- `POST /api/v2/storage/endpoints/rotate` - Rotate endpoints

## Endpoint Types

### Admin Panel
Disguised as storage/file API endpoints:
- `/api/v2/cloud/process`
- `/rest/v1/storage/upload`
- `/api/v3/files/metadata`

### Xray WebSocket
Disguised as JavaScript files:
- `/cdn/libs/jquery/3.6.1/jquery.min.js`
- `/assets/js/analytics-a3f2.bundle.js`
- `/static/js/tracking-5.2.0.prod.js`

### WireGuard WebSocket
Disguised as font files:
- `/static/fonts/woff2/roboto-regular.woff2`
- `/assets/fonts/opensans/opensans-bold.woff2`
- `/fonts/lato-medium-7a3c.woff2`

### Trojan WebSocket
Disguised as API endpoints:
- `/api/v1/files/sync`
- `/rest/v2/backup/download`
- `/v3/api/cloud/thumbnail`

### Health Check
Disguised as monitoring endpoints:
- `/api/v1/microservices/health`
- `/monitoring/services/status`
- `/internal/system/ping`

### WebRTC Signal
Disguised as media/streaming endpoints:
- `/media/webrtc/conference/signal`
- `/streaming/rtc/ice`
- `/rtc/meeting/sdp`

## Configuration File

Endpoints are stored in `data/stealth-vpn/endpoints.json`:

```json
{
  "admin_panel": "/api/v2/cloud/process",
  "xray_websocket": "/cdn/libs/lodash/5.3.3/lodash.min.js",
  "wireguard_websocket": "/static/fonts/woff2/raleway-light.woff2",
  "trojan_websocket": "/v2/api/media/thumbnail",
  "health_check": "/monitoring/api/status",
  "webrtc_signal": "/rtc/meeting/ice",
  "generated_at": "2f58b9fd53710aaf56c58345d95532d8",
  "timestamp": "2025-11-08T16:00:01.092679Z",
  "version": "1.0"
}
```

## Rotation Strategy

### Automatic Rotation
Endpoints should be rotated periodically to avoid pattern detection:
- **Recommended**: Every 30 days
- **Minimum**: Every 90 days
- **Maximum**: Every 7 days (for high-security environments)

### Manual Rotation
Force rotation when:
- Suspected detection or blocking
- After security incidents
- During maintenance windows
- When adding new services

### Rotation Process

1. **Generate new endpoints**:
   ```bash
   python3 scripts/generate-endpoints.py --force
   ```

2. **Backup is created automatically** in `data/stealth-vpn/backups/`

3. **Update Caddyfile** (done automatically by script)

4. **Restart Caddy**:
   ```bash
   docker compose restart caddy
   ```

5. **Update client configurations**:
   - Regenerate all client configs through admin panel
   - Distribute new configs to users

## Integration with Services

### Xray Configuration
The Xray server configuration automatically uses the obfuscated WebSocket path from `endpoints.json`.

### Trojan Configuration
The Trojan server configuration automatically uses the obfuscated WebSocket path from `endpoints.json`.

### Admin Panel
The admin panel dynamically loads endpoints and uses them for:
- Client configuration generation
- Server configuration updates
- QR code generation

### Client Configurations
All generated client configurations automatically include the current obfuscated endpoints.

## Security Considerations

### Path Characteristics
- **Realistic**: Paths look like real web resources
- **Varied**: Different types for different services
- **Unpredictable**: Random generation prevents patterns
- **Consistent**: Same format as legitimate web applications

### Rotation Benefits
- **Prevents Pattern Recognition**: Regular changes avoid detection
- **Limits Exposure**: Compromised endpoints have limited lifetime
- **Maintains Stealth**: Continuous adaptation to detection methods

### Best Practices
1. **Rotate regularly** but not too frequently (30 days recommended)
2. **Keep backups** of old endpoints for rollback
3. **Test after rotation** to ensure all services work
4. **Update clients promptly** after rotation
5. **Monitor for blocks** and rotate if detected

## Troubleshooting

### Endpoints Not Loading
```bash
# Check if endpoints file exists
ls -la data/stealth-vpn/endpoints.json

# Validate endpoints
python3 scripts/generate-endpoints.py --validate
```

### Services Not Using New Endpoints
```bash
# Regenerate server configs
docker compose exec admin python3 -c "from config_generator import ConfigGenerator; ConfigGenerator().update_server_configs()"

# Restart all services
docker compose restart
```

### Client Configs Not Updated
1. Delete old client configs: `rm -rf data/stealth-vpn/configs/clients/*`
2. Regenerate through admin panel
3. Download new configs for all users

## Testing

Run integration tests:
```bash
python3 scripts/test-endpoint-integration.py
```

This tests:
- Endpoint generation
- Validation
- Rotation
- Integration with ConfigGenerator

## Monitoring

### Check Endpoint Age
```bash
python3 scripts/generate-endpoints.py --stats
```

Output:
```
📊 Current Endpoint Statistics:
   Age: 15 days, 3 hours
   Generated ID: 2f58b9fd53710aaf56c58345d95532d8
   Version: 1.0
   Services: 6
```

### View Current Endpoints
```bash
cat data/stealth-vpn/endpoints.json | jq
```

### List Backups
```bash
ls -lh data/stealth-vpn/backups/endpoints_*.json
```

## Future Enhancements

Potential improvements:
- Scheduled automatic rotation via cron
- Endpoint usage analytics
- Detection of blocked endpoints
- A/B testing of endpoint patterns
- Machine learning for optimal path generation
- Integration with CDN patterns
