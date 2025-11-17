# Security Hardening Guide

This document describes the security hardening measures implemented in the Stealth VPN Server to protect against various attacks and ensure secure operation.

## Table of Contents

1. [Container Security](#container-security)
2. [Traffic Analysis Protection](#traffic-analysis-protection)
3. [Anti-Fingerprinting Measures](#anti-fingerprinting-measures)
4. [Resource Limits](#resource-limits)
5. [Best Practices](#best-practices)

## Container Security

### Non-Root Users

All containers run as non-root users to minimize the impact of potential security breaches:

- **Xray**: Runs as user `xray` (UID 1000)
- **Trojan**: Runs as user `trojan` (UID 1000)
- **Sing-box**: Runs as user `singbox` (UID 1000)
- **WireGuard**: Runs as user `wireguard` (UID 1000)
- **Admin Panel**: Runs as user `appuser` (UID 1000)

### Capability Management

Containers use minimal Linux capabilities:

```yaml
# Default for most containers
cap_drop:
  - ALL
cap_add:
  - NET_BIND_SERVICE  # Only for binding to ports < 1024

# WireGuard requires additional capabilities
cap_add:
  - NET_ADMIN  # For network interface management
  - NET_RAW    # For raw socket operations
  - SYS_MODULE # For kernel module loading
```

### Read-Only Filesystems

Most containers use read-only root filesystems with specific writable directories:

```yaml
read_only: true
tmpfs:
  - /tmp:noexec,nosuid,nodev,size=100m
  - /run:noexec,nosuid,nodev,size=10m
```

### Security Options

All containers enforce additional security measures:

```yaml
security_opt:
  - no-new-privileges:true  # Prevent privilege escalation
  - apparmor=docker-default # Use AppArmor profile
```

### Volume Permissions

Configuration volumes are mounted read-only where possible:

```yaml
volumes:
  - ./data/stealth-vpn/configs:/etc/xray:ro
  - ./data/caddy/certificates:/etc/letsencrypt:ro
```

## Traffic Analysis Protection

### Timing Randomization

The system implements sophisticated timing randomization to prevent timing-based traffic analysis:

#### Traffic Patterns

Different traffic patterns are supported to mimic legitimate applications:

- **Web Browsing**: Variable delays (10-500ms) with occasional bursts
- **Video Streaming**: Consistent high-throughput with short delays (5-50ms)
- **File Download**: Minimal delays (1-20ms) with large bursts
- **API Requests**: Longer delays (50-1000ms) with sparse bursts
- **WebSocket**: Medium delays (20-200ms) with moderate bursts

#### Implementation

```python
from core.traffic_obfuscation import TrafficObfuscator, TrafficPattern

# Initialize obfuscator
obfuscator = TrafficObfuscator(TrafficPattern.WEB_BROWSING)

# Get randomized delay before sending packet
delay = obfuscator.get_next_delay()
time.sleep(delay)

# Send packet
send_packet(data)
obfuscator.update_last_packet_time()
```

#### Burst Behavior

- Bursts occur randomly based on pattern probability
- Burst sizes vary within configured ranges
- Inter-burst delays add realistic pauses
- Jitter (±10%) prevents predictable patterns

### Packet Size Normalization

All packets are normalized to common sizes to prevent size-based fingerprinting:

#### Common HTTPS Packet Sizes

```python
HTTPS_COMMON_SIZES = [
    52, 64, 128, 256, 512, 1024, 1280, 1400, 1460, 1500
]
```

#### Common QUIC Packet Sizes

```python
QUIC_COMMON_SIZES = [
    1200, 1252, 1280, 1350, 1400, 1452
]
```

#### Padding Strategy

```python
# Calculate padding needed
padding_size = obfuscator.calculate_padding(len(data), protocol="https")

# Generate cryptographically secure random padding
padding = obfuscator.generate_padding(padding_size)

# Add padding to data
padded_data = data + padding
```

### Dummy Packets

The system sends dummy packets during idle periods to prevent traffic analysis:

- **Long idle (>5s)**: 30% probability of dummy packet
- **Medium idle (>2s)**: 10% probability
- **Active traffic**: 2% probability

## Anti-Fingerprinting Measures

### TLS Fingerprinting Protection

#### Extension Order Randomization

TLS extension order is randomized to prevent JA3 fingerprinting:

```python
extensions = [
    0,   # server_name
    5,   # status_request
    10,  # supported_groups
    13,  # signature_algorithms
    16,  # ALPN
    # ... more extensions
]

# Shuffle order
random.shuffle(extensions)
```

#### ALPN Randomization

Application-Layer Protocol Negotiation is randomized:

```json
{
  "alpn": ["h2", "http/1.1"]  // Randomized order
}
```

### HTTP/2 Fingerprinting Protection

#### Realistic Headers

All HTTP requests use realistic browser headers:

```python
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9...",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
}
```

#### User-Agent Rotation

User-Agent strings rotate between popular browsers:

- Chrome on Windows/macOS/Linux
- Firefox on Windows/macOS
- Safari on macOS

### QUIC Fingerprinting Protection

#### Transport Parameter Randomization

QUIC transport parameters are randomized:

```python
{
    "initial_max_stream_data_bidi_local": random.randint(1048576, 10485760),
    "initial_max_stream_data_bidi_remote": random.randint(1048576, 10485760),
    "initial_max_data": random.randint(10485760, 104857600),
    "initial_max_streams_bidi": random.randint(100, 1000),
    "max_idle_timeout": random.randint(30000, 60000),
    "max_udp_payload_size": random.choice([1200, 1252, 1350, 1452]),
}
```

#### Connection ID Randomization

Connection IDs use cryptographically secure random generation.

## Resource Limits

### CPU Limits

Each container has CPU limits to prevent resource exhaustion:

```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'      # Maximum 2 CPU cores
    reservations:
      cpus: '0.5'      # Minimum 0.5 CPU cores
```

### Memory Limits

Memory is limited to prevent OOM conditions:

```yaml
deploy:
  resources:
    limits:
      memory: 512M     # Maximum 512MB
    reservations:
      memory: 128M     # Minimum 128MB
```

### File Descriptor Limits

File descriptors are limited appropriately:

```yaml
ulimits:
  nofile:
    soft: 65536
    hard: 65536
  nproc:
    soft: 4096
    hard: 4096
```

### Container-Specific Limits

| Container | CPU Limit | Memory Limit | Purpose |
|-----------|-----------|--------------|---------|
| Caddy | 2.0 cores | 512M | Web server and reverse proxy |
| Xray | 2.0 cores | 512M | VPN protocol handling |
| Trojan | 2.0 cores | 512M | VPN protocol handling |
| Sing-box | 2.0 cores | 512M | Multi-protocol VPN |
| WireGuard | 2.0 cores | 512M | VPN with obfuscation |
| Admin | 1.0 core | 256M | Management interface |

## Best Practices

### 1. Regular Updates

Keep all containers updated:

```bash
# Pull latest images
docker compose pull

# Rebuild custom images
docker compose build --no-cache

# Restart services
docker compose up -d
```

### 2. Monitor Resource Usage

Check resource consumption regularly:

```bash
# View container stats
docker stats

# Check specific container
docker stats stealth-xray
```

### 3. Review Logs

Monitor logs for suspicious activity:

```bash
# View all logs
docker compose logs -f

# View specific service
docker compose logs -f xray

# Check for errors
docker compose logs --tail=100 | grep -i error
```

### 4. Apply Traffic Obfuscation

Apply traffic obfuscation after configuration changes:

```bash
# Apply to all protocols
python3 scripts/apply-traffic-obfuscation.py

# Restart services to apply changes
docker compose restart xray trojan singbox wireguard
```

### 5. Backup Configurations

Regular backups are essential:

```bash
# Backup all configurations
tar -czf backup-$(date +%Y%m%d).tar.gz data/stealth-vpn/configs/

# Backup user data
cp data/stealth-vpn/configs/users.json data/stealth-vpn/backups/
```

### 6. Test Security

Regularly test security measures:

```bash
# Test container security
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image stealth-xray:latest

# Test network security
nmap -sV -p 443 your-domain.com

# Test TLS configuration
testssl.sh your-domain.com
```

### 7. Rotate Obfuscation Parameters

Periodically rotate obfuscation parameters:

```bash
# Regenerate obfuscated endpoints
python3 scripts/generate-endpoints.py

# Apply new traffic patterns
python3 scripts/apply-traffic-obfuscation.py

# Restart services
docker compose restart
```

## Security Checklist

- [ ] All containers run as non-root users
- [ ] Read-only filesystems enabled where possible
- [ ] Minimal Linux capabilities assigned
- [ ] Resource limits configured
- [ ] Traffic obfuscation applied
- [ ] Anti-fingerprinting measures enabled
- [ ] Regular security updates scheduled
- [ ] Log monitoring configured
- [ ] Backup system in place
- [ ] Security testing performed

## Troubleshooting

### Permission Denied Errors

If you encounter permission errors:

```bash
# Fix ownership of data directories
sudo chown -R 1000:1000 data/stealth-vpn/

# Fix permissions
sudo chmod -R 755 data/stealth-vpn/configs/
sudo chmod 700 data/stealth-vpn/configs/wireguard/keys/
```

### Container Fails to Start

Check security settings:

```bash
# View container logs
docker logs stealth-xray

# Check AppArmor status
sudo aa-status

# Temporarily disable read-only for debugging
# Edit docker-compose.yml: read_only: false
```

### High Resource Usage

Adjust resource limits if needed:

```bash
# Edit docker-compose.yml
# Increase limits for specific container
deploy:
  resources:
    limits:
      cpus: '4.0'
      memory: 1G
```

## References

- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [Linux Capabilities](https://man7.org/linux/man-pages/man7/capabilities.7.html)
- [AppArmor Documentation](https://gitlab.com/apparmor/apparmor/-/wikis/home)
- [Traffic Analysis Attacks](https://en.wikipedia.org/wiki/Traffic_analysis)
- [TLS Fingerprinting](https://engineering.salesforce.com/tls-fingerprinting-with-ja3-and-ja3s-247362855967)
