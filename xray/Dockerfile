FROM teddysun/xray:latest

# Install additional security tools
RUN apk add --no-cache \
    su-exec \
    tini

# Create non-root user for security
RUN addgroup -g 1000 xray && \
    adduser -D -s /bin/sh -u 1000 -G xray xray

# Create necessary directories with proper permissions
RUN mkdir -p /var/log/xray /var/lib/xray /etc/xray && \
    chown -R xray:xray /var/log/xray /var/lib/xray /etc/xray

# Create a startup script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD pgrep xray || exit 1

# Use tini as init system for proper signal handling
ENTRYPOINT ["/sbin/tini", "--", "/entrypoint.sh"]