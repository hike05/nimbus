FROM trojangfw/trojan-go:latest

# Install additional tools for health checks and logging
RUN apk add --no-cache \
    curl \
    ca-certificates \
    tzdata \
    python3 \
    tini

# Create non-root user for security
RUN addgroup -g 1000 trojan && \
    adduser -D -s /bin/sh -u 1000 -G trojan trojan

# Create necessary directories with proper permissions
RUN mkdir -p /var/log/trojan-go /var/lib/trojan-go /etc/trojan-go && \
    chown -R trojan:trojan /var/log/trojan-go /var/lib/trojan-go /etc/trojan-go && \
    chmod 755 /var/log/trojan-go /var/lib/trojan-go

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Switch to non-root user
USER trojan

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD pgrep trojan-go || exit 1

# Expose port
EXPOSE 8002

# Use tini as init system for proper signal handling
ENTRYPOINT ["/sbin/tini", "--", "/entrypoint.sh"]