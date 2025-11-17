# Security Features

This document provides a quick reference for the security features implemented in the Stealth VPN Server.

## Quick Start

### Apply Security Hardening

After installation or configuration changes:

```bash
# Apply traffic obfuscation to all protocols
make apply-obfuscation

# Run security tests
make security-test

# Full security audit
make security-audit
```

## Container Security

All containers run with enhanced security:

- ✓ Non-root users (UID 1000)
- ✓ Minimal Linux capabilities
- ✓ Read-only filesystems
- ✓ Resource limits (CPU, memory)
- ✓ Security options (no-new-privileges, AppArmor)

### Verify Container Security

```bash
# Check container users
docker exec stealth-xray whoami

# Check security options
docker inspect stealth-xray --format '{{.HostConfig.SecurityOpt}}'

# Check resource limits
docker stats stealth-xray
```

## Traffic Analysis Protection

### Features

1. **Timing Randomization**: Prevents timing-based traffic analysis
2. **Packet Size Normalization**: Normalizes packets to common HTTPS/QUIC sizes
3. **Anti-Fingerprinting**: Protects against TLS, HTTP/2, and QUIC fingerprinting
4. **Dummy Packets**: Sends dummy packets during idle periods

### Traffic Patterns

Choose patterns based on your use case:

- `WEB_BROWSING`: General web browsing (default)
- `VIDEO_STREAMING`: Video streaming services
- `FILE_DOWNLOAD`: Large file downloads
- `API_REQUESTS`: API and REST services
- `WEBSOCKET`: WebSocket applications

### Apply Obfuscation

```bash
# Apply to all protocols
python3 scripts/apply-traffic-obfuscation.py

# Restart services
docker compose restart xray trojan singbox wireguard
```

## Anti-Fingerprinting

### TLS Fingerprinting Protection

- Randomized TLS extension order
- Realistic cipher suites
- ALPN randomization

### HTTP/2 Fingerprinting Protection

- Realistic browser headers
- User-Agent rotation
- Proper Accept headers

### QUIC Fingerprinting Protection

- Randomized transport parameters
- HTTP/3 ALPN
- Realistic connection IDs

## Security Testing

### Run All Tests

```bash
make security-test
```

### Individual Tests

```bash
# Test traffic obfuscation module
python3 -c "from core.traffic_obfuscation import *; print('OK')"

# Test container security
docker inspect stealth-xray --format '{{.Config.User}}'

# Test resource limits
docker stats --no-stream
```

## Monitoring

### Check Security Status

```bash
# View container security
docker compose ps

# Check logs for security events
docker compose logs | grep -i "security\|error\|fail"

# Monitor resource usage
docker stats
```

### Health Checks

```bash
# Run health checks
make health

# Check specific service
docker compose exec xray pgrep xray
```

## Maintenance

### Regular Tasks

**Weekly:**
```bash
make security-test
```

**Monthly:**
```bash
# Update obfuscation parameters
make apply-obfuscation

# Full security audit
make security-audit

# Update containers
docker compose pull
docker compose up -d
```

### Update Security Features

```bash
# Rebuild containers with latest security patches
make rebuild

# Apply new obfuscation settings
make apply-obfuscation
```

## Troubleshooting

### Permission Errors

```bash
# Fix ownership
sudo chown -R 1000:1000 data/stealth-vpn/

# Fix permissions
sudo chmod -R 755 data/stealth-vpn/configs/
```

### Container Won't Start

```bash
# Check logs
docker logs stealth-xray

# Verify configuration
docker compose config

# Test without read-only (temporarily)
# Edit docker-compose.yml: read_only: false
```

### High Resource Usage

```bash
# Check current usage
docker stats

# Adjust limits in docker-compose.yml if needed
# Then restart:
docker compose up -d
```

## Security Best Practices

1. **Keep Updated**: Regularly update all containers
2. **Monitor Logs**: Check logs for suspicious activity
3. **Rotate Parameters**: Change obfuscation parameters monthly
4. **Test Regularly**: Run security tests weekly
5. **Backup Configs**: Backup configurations before changes
6. **Limit Access**: Restrict admin panel access
7. **Use Strong Passwords**: Use strong passwords for admin panel
8. **Enable Firewall**: Use host firewall in addition to Docker

## Advanced Configuration

### Custom Traffic Patterns

Edit `core/traffic_obfuscation.py` to add custom patterns:

```python
TIMING_PROFILES = {
    TrafficPattern.CUSTOM: TimingProfile(
        min_delay_ms=20,
        max_delay_ms=300,
        burst_probability=0.5,
        burst_size_range=(5, 15),
        inter_burst_delay_ms=(200, 1000)
    )
}
```

### Custom Resource Limits

Edit `docker-compose.yml`:

```yaml
deploy:
  resources:
    limits:
      cpus: '4.0'      # Increase CPU limit
      memory: 1G       # Increase memory limit
```

## Documentation

- Full security guide: [docs/SECURITY_HARDENING.md](docs/SECURITY_HARDENING.md)
- Container security: [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- Traffic analysis: [Wikipedia - Traffic Analysis](https://en.wikipedia.org/wiki/Traffic_analysis)

## Support

For security issues or questions:

1. Check logs: `docker compose logs`
2. Run tests: `make security-test`
3. Review documentation: `docs/SECURITY_HARDENING.md`
4. Check container status: `docker compose ps`

## Security Checklist

Before deployment:

- [ ] All containers run as non-root
- [ ] Resource limits configured
- [ ] Traffic obfuscation applied
- [ ] Security tests passed
- [ ] Logs monitored
- [ ] Backups configured
- [ ] Firewall rules set
- [ ] Strong passwords used
- [ ] SSL certificates valid
- [ ] Regular updates scheduled
