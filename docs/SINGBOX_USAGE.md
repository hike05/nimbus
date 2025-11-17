# Sing-box Multi-Protocol Service Usage Guide

## Overview

The Sing-box service provides three advanced VPN protocols with full HTTPS masking:

1. **ShadowTLS v3** - Full TLS handshake imitation with fallback to real websites
2. **Hysteria 2** - QUIC-based protocol with HTTP/3 masking and salamander obfuscation
3. **TUIC v5** - QUIC protocol with HTTP/3 ALPN for Chrome/Firefox compatibility

## Architecture

- **Container**: `stealth-singbox` (based on `sagernet/sing-box:latest`)
- **Ports**: 
  - 8003: ShadowTLS v3
  - 8004: Shadowsocks (underlying protocol for ShadowTLS)
  - 8005: Hysteria 2
  - 8006: TUIC v5
- **Configuration**: `/data/stealth-vpn/configs/singbox.json`
- **Logs**: `/data/stealth-vpn/logs/singbox/`

## Configuration Management

### Generate Server Configuration

```bash
python3 scripts/singbox-config-manager.py generate-server [domain] [config_dir]
```

Example:
```bash
python3 scripts/singbox-config-manager.py generate-server example.com data/stealth-vpn/configs
```

### Generate Client Configurations

```bash
python3 scripts/singbox-config-manager.py generate-client <username> [domain] [config_dir]
```

Example:
```bash
python3 scripts/singbox-config-manager.py generate-client alice example.com data/stealth-vpn/configs
```

This generates:
- `singbox-shadowtls.json` - ShadowTLS client config
- `singbox-shadowtls-link.txt` - ShadowTLS connection URL
- `singbox-hysteria2.json` - Hysteria 2 client config
- `singbox-hysteria2-link.txt` - Hysteria 2 connection URL
- `singbox-tuic.json` - TUIC v5 client config
- `singbox-tuic-link.txt` - TUIC v5 connection URL

### Add Sing-box Credentials to Existing User

```bash
python3 scripts/singbox-config-manager.py add-credentials <username> [config_dir]
```

Example:
```bash
python3 scripts/singbox-config-manager.py add-credentials alice data/stealth-vpn/configs
```

### Test Configuration

```bash
python3 scripts/singbox-config-manager.py test
```

## Protocol Details

### ShadowTLS v3

- **Port**: 8003 (internal), 443 (external via Caddy)
- **SNI**: `api.your-domain.com`
- **Features**:
  - Full TLS handshake imitation
  - Fallback to real HTTPS server
  - Strict mode for enhanced security
  - Underlying Shadowsocks 2022 encryption

### Hysteria 2

- **Port**: 8005 (internal), 443 (external via Caddy)
- **SNI**: `cdn.your-domain.com`
- **Features**:
  - QUIC-based for better performance
  - HTTP/3 masking
  - Salamander obfuscation
  - Configurable bandwidth limits
  - BBR congestion control

### TUIC v5

- **Port**: 8006 (internal), 443 (external via Caddy)
- **SNI**: `files.your-domain.com`
- **Features**:
  - QUIC protocol with HTTP/3 ALPN
  - BBR congestion control
  - Zero-RTT handshake support
  - Native UDP relay mode
  - Compatible with Chrome/Firefox HTTP/3

## Caddy Routing

All protocols are routed through Caddy on port 443:

```caddyfile
# ShadowTLS routing
@shadowtls tls sni api.your-domain.com
handle @shadowtls {
    reverse_proxy singbox:8003
}

# Hysteria 2 routing
@hysteria tls sni cdn.your-domain.com
handle @hysteria {
    reverse_proxy singbox:8005
}

# TUIC routing
@tuic tls sni files.your-domain.com
handle @tuic {
    reverse_proxy singbox:8006
}
```

## Service Management

### Start Sing-box Service

```bash
docker-compose up -d singbox
```

### Restart Sing-box Service

```bash
docker restart stealth-singbox
```

### View Logs

```bash
docker logs stealth-singbox
# or
tail -f data/stealth-vpn/logs/singbox/sing-box.log
```

### Check Service Health

```bash
docker ps | grep singbox
# or
python3 -c "from core.service_manager import DockerServiceManager; sm = DockerServiceManager(); print(sm.check_service_health('singbox'))"
```

## Client Setup

### Using JSON Configuration

1. Download the appropriate JSON config file for your protocol
2. Install Sing-box client on your device
3. Run: `sing-box run -c <config-file>.json`

### Using Connection URLs

1. Copy the connection URL from the `-link.txt` file
2. Import into compatible VPN client (v2rayN, NekoBox, etc.)
3. Connect to the server

## Testing

Run the comprehensive integration test:

```bash
python3 scripts/test-singbox-integration.py
```

This tests:
- Credential generation
- Server configuration generation
- Client configuration generation
- Service integration
- All protocol configurations

## Troubleshooting

### Service Won't Start

1. Check logs: `docker logs stealth-singbox`
2. Validate configuration: `sing-box check -c data/stealth-vpn/configs/singbox.json`
3. Ensure certificates exist: `ls -la data/caddy/certificates/`

### Connection Issues

1. Verify Caddy is routing correctly: `docker logs stealth-caddy`
2. Check SNI matches the protocol subdomain
3. Ensure firewall allows port 443 (TCP and UDP)
4. Test with different protocols (some may work better in certain networks)

### Configuration Errors

1. Regenerate server config: `python3 scripts/singbox-config-manager.py generate-server`
2. Verify user credentials exist in `users.json`
3. Check template file is valid JSON: `data/stealth-vpn/configs/singbox.template.json`

## Security Considerations

- All protocols use TLS 1.3 encryption
- QUIC protocols (Hysteria 2, TUIC) provide additional obfuscation
- ShadowTLS v3 provides the strongest DPI resistance
- Regular credential rotation is recommended
- Monitor logs for suspicious activity

## Performance Tips

- **Hysteria 2**: Best for high-speed connections, adjust bandwidth limits as needed
- **TUIC v5**: Excellent for mobile devices with connection migration
- **ShadowTLS v3**: Best for censored networks, slightly higher latency

## Integration with Admin Panel

The admin panel automatically:
- Generates Sing-box credentials when creating users
- Updates server configuration when users are added/removed
- Provides download links for all protocol configurations
- Displays QR codes for mobile client setup

## References

- [Sing-box Documentation](https://sing-box.sagernet.org/)
- [ShadowTLS Specification](https://github.com/ihciah/shadow-tls)
- [Hysteria 2 Documentation](https://v2.hysteria.network/)
- [TUIC Protocol](https://github.com/EAimTY/tuic)