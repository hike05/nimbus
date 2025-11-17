FROM alpine:latest

# Install runtime dependencies and tini
RUN apk add --no-cache ca-certificates tzdata tini curl

# Download and install sing-box binary
RUN ARCH=$(uname -m) && \
    if [ "$ARCH" = "x86_64" ]; then ARCH="amd64"; fi && \
    if [ "$ARCH" = "aarch64" ]; then ARCH="arm64"; fi && \
    curl -Lo /tmp/sing-box.tar.gz "https://github.com/SagerNet/sing-box/releases/latest/download/sing-box-$(curl -s https://api.github.com/repos/SagerNet/sing-box/releases/latest | grep tag_name | cut -d '"' -f 4 | sed 's/v//')-linux-${ARCH}.tar.gz" && \
    tar -xzf /tmp/sing-box.tar.gz -C /tmp && \
    mv /tmp/sing-box-*/sing-box /usr/local/bin/sing-box && \
    chmod +x /usr/local/bin/sing-box && \
    rm -rf /tmp/sing-box*

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