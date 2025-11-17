# Client Configuration Generation Guide

## Overview

The Stealth VPN Server automatically generates client configurations for all supported protocols when users are created. This guide explains how the configuration generation system works and how to use it.

## Supported Protocols

### 1. Xray Protocols
- **XTLS-Vision**: Best performance, recommended for desktop
- **WebSocket**: Fallback option, works through HTTP proxies

### 2. Trojan-Go
- WebSocket-based protocol with TLS masquerading
- Good compatibility with restrictive networks

### 3. Sing-box Protocols
- **ShadowTLS v3**: Maximum obfuscation, DPI bypass
- **Hysteria2**: High-speed UDP-based protocol
- **TUIC v5**: Low-latency QUIC-based protocol

### 4. WireGuard
- **Native**: Standard WireGuard configuration
- **WebSocket**: Obfuscated through HTTPS WebSocket tunnel

## Automatic Generation

### When User is Created
```bash
# Via API
curl -X POST https://your-domain.com/api/v2/storage/files \
  -H "Content-Type: application/json" \
  -d '{"filename": "alice"}'
```

**Automatically Generated:**
1. All protocol configurations (JSON and links)
2. QR codes for mobile clients
3. Connection instructions
4. Saved to `/data/stealth-vpn/configs/clients/alice/`

### Generated Files

```
clients/alice/
├── xray-xtls.json              # Xray XTLS-Vision client config
├── xray-ws.json                # Xray WebSocket client config
├── trojan.json                 # Trojan-Go client config
├── singbox-shadowtls.json      # ShadowTLS v3 config
├── singbox-hysteria2.json      # Hysteria2 config
├── singbox-tuic.json           # TUIC v5 config
├── wireguard.conf              # Native WireGuard config
├── wireguard-websocket.conf    # Obfuscated WireGuard config
├── xray-links.txt              # All connection links and instructions
├── xray-xtls-qr.png           # QR codes for mobile
├── xray-ws-qr.png
├── trojan-qr.png
├── hysteria2-qr.png
└── wireguard-qr.png
```

## Configuration Formats

### Connection Links (for Mobile Apps)

**Xray XTLS-Vision:**
```
vless://uuid@domain.com:443?type=tcp&security=xtls&flow=xtls-rprx-vision&sni=domain.com&fp=chrome#alice-xtls
```

**Xray WebSocket:**
```
vless://uuid@domain.com:443?type=ws&path=/cdn/assets/js/analytics.min.js&host=domain.com&security=tls&sni=domain.com#alice-ws
```

**Trojan-Go:**
```
trojan://password@domain.com:443?type=ws&path=/api/v1/files/sync&host=domain.com&sni=domain.com#alice-trojan
```

**Hysteria2:**
```
hysteria2://password@domain.com:443?sni=cdn.domain.com&obfs=salamander&obfs-password=pass#alice-hy2
```

### JSON Configurations (for Desktop Clients)

**Xray XTLS-Vision:**
```json
{
  "outbounds": [{
    "protocol": "vless",
    "settings": {
      "vnext": [{
        "address": "domain.com",
        "port": 443,
        "users": [{
          "id": "uuid",
          "flow": "xtls-rprx-vision",
          "encryption": "none"
        }]
      }]
    },
    "streamSettings": {
      "network": "tcp",
      "security": "xtls",
      "xtlsSettings": {
        "serverName": "domain.com",
        "fingerprint": "chrome"
      }
    }
  }]
}
```

**Sing-box Hysteria2:**
```json
{
  "type": "hysteria2",
  "server": "domain.com",
  "server_port": 443,
  "password": "password",
  "tls": {
    "enabled": true,
    "server_name": "cdn.domain.com",
    "insecure": false,
    "alpn": ["h3"]
  },
  "obfs": {
    "type": "salamander",
    "password": "obfs-password"
  },
  "up_mbps": 100,
  "down_mbps": 100
}
```

**WireGuard:**
```ini
[Interface]
PrivateKey = client-private-key
Address = 10.0.0.2/32
DNS = 1.1.1.1, 8.8.8.8

[Peer]
PublicKey = server-public-key
Endpoint = domain.com:51820
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
```

## QR Code Generation

### Automatic QR Codes
QR codes are automatically generated for:
- Xray XTLS-Vision
- Xray WebSocket
- Trojan-Go
- Hysteria2
- WireGuard

### Accessing QR Codes

**Via Admin Panel:**
1. Login to admin panel
2. Click "View" for any user
3. Navigate to "QR Codes" tab
4. Scan with mobile app

**Via API:**
```bash
# Get all QR codes as base64 JSON
curl https://domain.com/api/v2/storage/files/alice/qrcodes

# Get individual QR code as PNG image
curl https://domain.com/api/v2/storage/files/alice/qrcode/xray-xtls > qr.png
curl https://domain.com/api/v2/storage/files/alice/qrcode/hysteria2 > hy2-qr.png
```

### Supported QR Code Formats
- **xray-xtls**: Xray XTLS-Vision link
- **xray-ws**: Xray WebSocket link
- **trojan**: Trojan-Go link
- **hysteria2**: Hysteria2 link
- **wireguard**: WireGuard configuration file
- **shadowtls**: ShadowTLS JSON config
- **tuic**: TUIC JSON config

## Mobile Client Setup

### iOS

**Xray/Trojan:**
1. Install Shadowrocket from App Store
2. Scan QR code or import link
3. Connect

**Sing-box Protocols:**
1. Install Sing-box app
2. Import JSON configuration
3. Connect

**WireGuard:**
1. Install WireGuard from App Store
2. Scan QR code
3. Connect

### Android

**Xray/Trojan:**
1. Install v2rayNG from Play Store or GitHub
2. Scan QR code or import link
3. Connect

**Sing-box Protocols:**
1. Install Sing-box app
2. Import JSON configuration
3. Connect

**WireGuard:**
1. Install WireGuard from Play Store
2. Scan QR code or import .conf file
3. Connect

## Desktop Client Setup

### Windows

**Xray:**
1. Download v2rayN from GitHub
2. Import JSON configuration
3. Connect

**Trojan:**
1. Download Clash for Windows
2. Import Trojan configuration
3. Connect

**Sing-box:**
1. Download Sing-box client
2. Import JSON configuration
3. Connect

**WireGuard:**
1. Download WireGuard from official site
2. Import .conf file
3. Connect

### macOS

**Xray:**
1. Download Qv2ray or v2rayN
2. Import JSON configuration
3. Connect

**Sing-box:**
1. Download Sing-box client
2. Import JSON configuration
3. Connect

**WireGuard:**
1. Download WireGuard from App Store
2. Import .conf file
3. Connect

### Linux

**Xray:**
```bash
# Install Xray-core
bash -c "$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)"

# Use generated config
xray -c /path/to/xray-xtls.json
```

**Sing-box:**
```bash
# Install Sing-box
bash <(curl -fsSL https://sing-box.app/install.sh)

# Use generated config
sing-box run -c /path/to/singbox-hysteria2.json
```

**WireGuard:**
```bash
# Install WireGuard
sudo apt install wireguard

# Import config
sudo cp wireguard.conf /etc/wireguard/wg0.conf
sudo wg-quick up wg0
```

## Protocol Recommendations

### By Use Case

**Maximum Speed:**
- Primary: Hysteria2 (UDP-based, high throughput)
- Fallback: Xray XTLS-Vision

**Maximum Compatibility:**
- Primary: Xray XTLS-Vision
- Fallback: Xray WebSocket

**Maximum Obfuscation:**
- Primary: ShadowTLS v3
- Fallback: WireGuard over WebSocket

**Simplest Setup:**
- Primary: WireGuard native
- Fallback: Xray XTLS-Vision

**Mobile Data:**
- Primary: Hysteria2 (handles network changes)
- Fallback: TUIC v5

### By Network Environment

**Corporate Network (HTTP proxy):**
- Xray WebSocket
- Trojan-Go WebSocket

**Restrictive DPI:**
- ShadowTLS v3
- Trojan-Go
- WireGuard over WebSocket

**High-Speed Fiber:**
- Hysteria2
- TUIC v5
- Xray XTLS-Vision

**Mobile/Unstable:**
- Hysteria2 (QUIC connection migration)
- TUIC v5

## API Reference

### Get User Configurations
```bash
GET /api/v2/storage/files/<username>/download
```

**Response:**
```json
{
  "success": true,
  "username": "alice",
  "configs": {
    "xray_xtls_link": "vless://...",
    "xray_xtls_json": "{...}",
    "xray_ws_link": "vless://...",
    "xray_ws_json": "{...}",
    "trojan_link": "trojan://...",
    "trojan_json": "{...}",
    "hysteria2_link": "hysteria2://...",
    "hysteria2_json": "{...}",
    "shadowtls_json": "{...}",
    "tuic_json": "{...}",
    "wireguard_conf": "[Interface]...",
    "wireguard_obfs_conf": "[Interface]..."
  }
}
```

### Get QR Codes
```bash
GET /api/v2/storage/files/<username>/qrcodes
```

**Response:**
```json
{
  "success": true,
  "username": "alice",
  "qr_codes": {
    "xray_xtls": "base64-encoded-png...",
    "xray_ws": "base64-encoded-png...",
    "trojan": "base64-encoded-png...",
    "hysteria2": "base64-encoded-png...",
    "wireguard": "base64-encoded-png..."
  }
}
```

### Get Individual QR Code
```bash
GET /api/v2/storage/files/<username>/qrcode/<protocol>
```

**Protocols:** xray-xtls, xray-ws, trojan, hysteria2, wireguard, shadowtls, tuic

**Response:** PNG image

## Troubleshooting

### QR Code Not Scanning
- Ensure good lighting
- Try different QR code scanner app
- Use manual link import instead

### Configuration Not Working
1. Check server is running: `docker compose ps`
2. Verify user is active in admin panel
3. Check protocol is supported by client app
4. Try different protocol

### Connection Fails
1. Verify domain resolves correctly
2. Check firewall allows port 443
3. Ensure SSL certificate is valid
4. Try fallback protocol (WebSocket)

### Mobile App Issues
- Update app to latest version
- Clear app cache
- Re-import configuration
- Try different protocol

## Security Notes

1. **QR Codes**: Contain sensitive credentials, share securely
2. **Configuration Files**: Store securely, don't commit to git
3. **Links**: Contain passwords, use secure channels
4. **Backups**: Encrypt before storing

## Updates

When server configurations change:
1. Regenerate client configs via admin panel
2. Users need to re-import configurations
3. QR codes are automatically updated
4. Old configurations will stop working

## Support

For issues with:
- **Configuration generation**: Check admin panel logs
- **QR codes**: Verify qrcode library is installed
- **Client apps**: Consult app documentation
- **Protocols**: Check protocol-specific documentation
