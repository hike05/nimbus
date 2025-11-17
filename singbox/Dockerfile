FROM sagernet/sing-box:latest

# Install tini for proper signal handling
RUN apk add --no-cache tini

# Create non-root user for security
RUN addgroup -g 1000 singbox && \
    adduser -D -s /bin/sh -u 1000 -G singbox singbox

# Create necessary directories with proper permissions
RUN mkdir -p /var/log/sing-box /var/lib/sing-box /etc/sing-box && \
    chown -R singbox:singbox /var/log/sing-box /var/lib/sing-box /etc/sing-box && \
    chmod 755 /var/log/sing-box /var/lib/sing-box

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Switch to non-root user
USER singbox

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD pgrep sing-box || exit 1

# Use tini as init system for proper signal handling
ENTRYPOINT ["/sbin/tini", "--", "/entrypoint.sh"]