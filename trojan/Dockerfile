FROM alpine:latest

# Install runtime dependencies
RUN apk add --no-cache \
    curl \
    ca-certificates \
    tzdata \
    python3 \
    tini

# Download and install trojan-go binary
RUN ARCH=$(uname -m) && \
    if [ "$ARCH" = "x86_64" ]; then ARCH="amd64"; fi && \
    if [ "$ARCH" = "aarch64" ]; then ARCH="arm64"; fi && \
    curl -Lo /tmp/trojan-go.zip "https://github.com/p4gefau1t/trojan-go/releases/latest/download/trojan-go-linux-${ARCH}.zip" && \
    unzip /tmp/trojan-go.zip -d /tmp && \
    mv /tmp/trojan-go /usr/local/bin/trojan-go && \
    chmod +x /usr/local/bin/trojan-go && \
    rm -rf /tmp/trojan-go*

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