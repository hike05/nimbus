FROM alpine:3.19

# Install WireGuard, WebSocket proxy tools, and udp2raw dependencies
RUN apk add --no-cache \
    wireguard-tools \
    iptables \
    ip6tables \
    bash \
    curl \
    python3 \
    py3-pip \
    libpcap \
    libpcap-dev \
    gcc \
    g++ \
    make \
    linux-headers \
    git \
    tini \
    su-exec \
    && rm -rf /var/cache/apk/*

# Install websockify for WebSocket tunneling
RUN pip3 install --no-cache-dir --break-system-packages websockify

# Create non-root user for security (WireGuard needs NET_ADMIN capability)
RUN addgroup -g 1000 wireguard && \
    adduser -D -s /bin/bash -u 1000 -G wireguard wireguard

# Create necessary directories with proper permissions
RUN mkdir -p /config/wg0 \
    /config/peer_configs \
    /config/keys \
    /var/log/wireguard \
    /var/lib/wireguard && \
    chown -R wireguard:wireguard /config /var/log/wireguard /var/lib/wireguard && \
    chmod 700 /config/keys

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

WORKDIR /config

EXPOSE 51820/udp 8006 8007

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD wg show wg0 || exit 1

# Use tini as init system for proper signal handling
ENTRYPOINT ["/sbin/tini", "--", "/entrypoint.sh"]
