#!/usr/bin/env python3
"""
Traffic Analysis Protection Module

Implements timing randomization, packet size normalization, and anti-fingerprinting
measures to protect against traffic analysis attacks.

Requirements: 2.3, 3.3
"""

import random
import time
import hashlib
import secrets
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class TrafficPattern(Enum):
    """Common traffic patterns for mimicry"""
    WEB_BROWSING = "web_browsing"
    VIDEO_STREAMING = "video_streaming"
    FILE_DOWNLOAD = "file_download"
    API_REQUESTS = "api_requests"
    WEBSOCKET = "websocket"


@dataclass
class TimingProfile:
    """Timing characteristics for traffic obfuscation"""
    min_delay_ms: int
    max_delay_ms: int
    burst_probability: float
    burst_size_range: Tuple[int, int]
    inter_burst_delay_ms: Tuple[int, int]


@dataclass
class PacketSizeProfile:
    """Packet size characteristics for normalization"""
    min_size: int
    max_size: int
    common_sizes: List[int]
    padding_strategy: str  # "random", "mtu", "common"


class TrafficObfuscator:
    """
    Main class for traffic analysis protection
    
    Implements:
    - Timing randomization to prevent timing attacks
    - Packet size normalization to prevent size-based fingerprinting
    - Traffic pattern mimicry to blend with legitimate traffic
    """
    
    # Common HTTPS packet sizes (based on real-world analysis)
    HTTPS_COMMON_SIZES = [
        52, 64, 128, 256, 512, 1024, 1280, 1400, 1460, 1500
    ]
    
    # Common HTTP/3 QUIC packet sizes
    QUIC_COMMON_SIZES = [
        1200, 1252, 1280, 1350, 1400, 1452
    ]
    
    # Timing profiles for different traffic patterns
    TIMING_PROFILES = {
        TrafficPattern.WEB_BROWSING: TimingProfile(
            min_delay_ms=10,
            max_delay_ms=500,
            burst_probability=0.3,
            burst_size_range=(3, 10),
            inter_burst_delay_ms=(100, 2000)
        ),
        TrafficPattern.VIDEO_STREAMING: TimingProfile(
            min_delay_ms=5,
            max_delay_ms=50,
            burst_probability=0.7,
            burst_size_range=(10, 50),
            inter_burst_delay_ms=(30, 100)
        ),
        TrafficPattern.FILE_DOWNLOAD: TimingProfile(
            min_delay_ms=1,
            max_delay_ms=20,
            burst_probability=0.9,
            burst_size_range=(50, 200),
            inter_burst_delay_ms=(10, 50)
        ),
        TrafficPattern.API_REQUESTS: TimingProfile(
            min_delay_ms=50,
            max_delay_ms=1000,
            burst_probability=0.1,
            burst_size_range=(1, 3),
            inter_burst_delay_ms=(500, 5000)
        ),
        TrafficPattern.WEBSOCKET: TimingProfile(
            min_delay_ms=20,
            max_delay_ms=200,
            burst_probability=0.4,
            burst_size_range=(2, 8),
            inter_burst_delay_ms=(100, 1000)
        )
    }
    
    def __init__(self, pattern: TrafficPattern = TrafficPattern.WEB_BROWSING):
        """
        Initialize traffic obfuscator with a specific pattern
        
        Args:
            pattern: Traffic pattern to mimic
        """
        self.pattern = pattern
        self.timing_profile = self.TIMING_PROFILES[pattern]
        self.last_packet_time = time.time()
        self.burst_counter = 0
        self.in_burst = False
        
    def get_next_delay(self) -> float:
        """
        Calculate next packet delay with randomization
        
        Returns:
            Delay in seconds (float)
        """
        profile = self.timing_profile
        
        # Decide if we should start/continue a burst
        if not self.in_burst and random.random() < profile.burst_probability:
            self.in_burst = True
            self.burst_counter = random.randint(*profile.burst_size_range)
        
        if self.in_burst:
            # Short delay during burst
            delay_ms = random.uniform(profile.min_delay_ms, profile.min_delay_ms * 2)
            self.burst_counter -= 1
            
            if self.burst_counter <= 0:
                self.in_burst = False
                # Add inter-burst delay
                delay_ms += random.uniform(*profile.inter_burst_delay_ms)
        else:
            # Normal delay between packets
            delay_ms = random.uniform(profile.min_delay_ms, profile.max_delay_ms)
        
        # Add jitter (±10%)
        jitter = delay_ms * random.uniform(-0.1, 0.1)
        delay_ms += jitter
        
        return max(0, delay_ms / 1000.0)  # Convert to seconds
    
    def normalize_packet_size(self, data_size: int, protocol: str = "https") -> int:
        """
        Normalize packet size to common sizes
        
        Args:
            data_size: Original data size
            protocol: Protocol type ("https", "quic", "websocket")
            
        Returns:
            Normalized size with padding
        """
        if protocol == "quic":
            common_sizes = self.QUIC_COMMON_SIZES
        else:
            common_sizes = self.HTTPS_COMMON_SIZES
        
        # Find next common size that fits the data
        for size in sorted(common_sizes):
            if size >= data_size:
                return size
        
        # If data is larger than all common sizes, round up to MTU
        mtu = 1500
        return ((data_size + mtu - 1) // mtu) * mtu
    
    def calculate_padding(self, data_size: int, protocol: str = "https") -> int:
        """
        Calculate padding needed to reach normalized size
        
        Args:
            data_size: Original data size
            protocol: Protocol type
            
        Returns:
            Padding size in bytes
        """
        normalized = self.normalize_packet_size(data_size, protocol)
        return max(0, normalized - data_size)
    
    def generate_padding(self, size: int) -> bytes:
        """
        Generate random padding data
        
        Args:
            size: Padding size in bytes
            
        Returns:
            Random padding bytes
        """
        if size <= 0:
            return b''
        
        # Use cryptographically secure random for padding
        return secrets.token_bytes(size)
    
    def add_timing_jitter(self, base_delay: float, jitter_percent: float = 0.2) -> float:
        """
        Add random jitter to timing
        
        Args:
            base_delay: Base delay in seconds
            jitter_percent: Jitter as percentage of base delay (0.0-1.0)
            
        Returns:
            Delay with jitter applied
        """
        jitter = base_delay * random.uniform(-jitter_percent, jitter_percent)
        return max(0, base_delay + jitter)
    
    def should_send_dummy_packet(self) -> bool:
        """
        Decide if a dummy packet should be sent to obfuscate traffic patterns
        
        Returns:
            True if dummy packet should be sent
        """
        # Send dummy packets randomly to prevent traffic analysis
        # Higher probability during idle periods
        time_since_last = time.time() - self.last_packet_time
        
        if time_since_last > 5.0:
            # Long idle, high probability of dummy packet
            return random.random() < 0.3
        elif time_since_last > 2.0:
            # Medium idle
            return random.random() < 0.1
        else:
            # Active traffic
            return random.random() < 0.02
    
    def update_last_packet_time(self):
        """Update timestamp of last packet"""
        self.last_packet_time = time.time()


class FingerprintingProtection:
    """
    Anti-fingerprinting measures for VPN protocols
    
    Protects against:
    - TLS fingerprinting
    - HTTP/2 fingerprinting
    - QUIC fingerprinting
    - Behavioral fingerprinting
    """
    
    @staticmethod
    def randomize_tls_extensions_order() -> List[int]:
        """
        Randomize TLS extension order to prevent fingerprinting
        
        Returns:
            List of extension IDs in randomized order
        """
        # Common TLS extensions used by browsers
        extensions = [
            0,      # server_name
            5,      # status_request
            10,     # supported_groups
            11,     # ec_point_formats
            13,     # signature_algorithms
            16,     # application_layer_protocol_negotiation
            18,     # signed_certificate_timestamp
            23,     # extended_master_secret
            27,     # compress_certificate
            35,     # session_ticket
            43,     # supported_versions
            45,     # psk_key_exchange_modes
            51,     # key_share
        ]
        
        # Shuffle to prevent fingerprinting
        random.shuffle(extensions)
        return extensions
    
    @staticmethod
    def generate_realistic_user_agent() -> str:
        """
        Generate realistic User-Agent string
        
        Returns:
            User-Agent string mimicking popular browsers
        """
        browsers = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
        
        return random.choice(browsers)
    
    @staticmethod
    def generate_realistic_headers() -> Dict[str, str]:
        """
        Generate realistic HTTP headers
        
        Returns:
            Dictionary of HTTP headers
        """
        return {
            "User-Agent": FingerprintingProtection.generate_realistic_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": random.choice([
                "en-US,en;q=0.9",
                "en-GB,en;q=0.9",
                "en-US,en;q=0.5",
            ]),
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }
    
    @staticmethod
    def randomize_quic_parameters() -> Dict[str, int]:
        """
        Randomize QUIC parameters to prevent fingerprinting
        
        Returns:
            Dictionary of QUIC transport parameters
        """
        return {
            "initial_max_stream_data_bidi_local": random.randint(1048576, 10485760),
            "initial_max_stream_data_bidi_remote": random.randint(1048576, 10485760),
            "initial_max_stream_data_uni": random.randint(1048576, 10485760),
            "initial_max_data": random.randint(10485760, 104857600),
            "initial_max_streams_bidi": random.randint(100, 1000),
            "initial_max_streams_uni": random.randint(100, 1000),
            "max_idle_timeout": random.randint(30000, 60000),
            "max_udp_payload_size": random.choice([1200, 1252, 1350, 1452]),
        }


class TrafficShaper:
    """
    Traffic shaping to mimic legitimate applications
    """
    
    def __init__(self, target_pattern: TrafficPattern):
        """
        Initialize traffic shaper
        
        Args:
            target_pattern: Pattern to mimic
        """
        self.pattern = target_pattern
        self.obfuscator = TrafficObfuscator(target_pattern)
    
    def shape_outbound_traffic(self, data: bytes, protocol: str = "https") -> Tuple[bytes, float]:
        """
        Shape outbound traffic with padding and timing
        
        Args:
            data: Original data
            protocol: Protocol type
            
        Returns:
            Tuple of (padded_data, delay_seconds)
        """
        # Calculate padding
        padding_size = self.obfuscator.calculate_padding(len(data), protocol)
        padding = self.obfuscator.generate_padding(padding_size)
        
        # Add padding to data
        padded_data = data + padding
        
        # Calculate delay
        delay = self.obfuscator.get_next_delay()
        
        return padded_data, delay
    
    def get_dummy_packet_config(self) -> Optional[Tuple[int, float]]:
        """
        Get configuration for dummy packet if needed
        
        Returns:
            Tuple of (packet_size, delay) or None
        """
        if self.obfuscator.should_send_dummy_packet():
            # Generate realistic dummy packet size
            size = random.choice(self.obfuscator.HTTPS_COMMON_SIZES)
            delay = self.obfuscator.get_next_delay()
            return (size, delay)
        
        return None


def generate_obfuscation_config(protocol: str, pattern: TrafficPattern) -> Dict:
    """
    Generate obfuscation configuration for VPN protocols
    
    Args:
        protocol: Protocol name ("xray", "trojan", "singbox", "wireguard")
        pattern: Traffic pattern to mimic
        
    Returns:
        Configuration dictionary
    """
    obfuscator = TrafficObfuscator(pattern)
    fingerprint = FingerprintingProtection()
    
    config = {
        "protocol": protocol,
        "pattern": pattern.value,
        "timing": {
            "min_delay_ms": obfuscator.timing_profile.min_delay_ms,
            "max_delay_ms": obfuscator.timing_profile.max_delay_ms,
            "jitter_percent": 0.2,
            "enable_dummy_packets": True,
        },
        "packet_size": {
            "normalization": "common_sizes",
            "common_sizes": obfuscator.HTTPS_COMMON_SIZES if protocol != "singbox" else obfuscator.QUIC_COMMON_SIZES,
            "padding_strategy": "random",
        },
        "anti_fingerprinting": {
            "randomize_tls_extensions": True,
            "realistic_headers": fingerprint.generate_realistic_headers(),
            "user_agent_rotation": True,
        }
    }
    
    if protocol == "singbox":
        # Add QUIC-specific parameters
        config["quic_parameters"] = fingerprint.randomize_quic_parameters()
    
    return config


if __name__ == "__main__":
    # Example usage
    print("Traffic Obfuscation Configuration Generator")
    print("=" * 50)
    
    for protocol in ["xray", "trojan", "singbox", "wireguard"]:
        pattern = TrafficPattern.WEB_BROWSING
        config = generate_obfuscation_config(protocol, pattern)
        
        print(f"\n{protocol.upper()} Configuration:")
        print(f"  Pattern: {config['pattern']}")
        print(f"  Timing: {config['timing']['min_delay_ms']}-{config['timing']['max_delay_ms']}ms")
        print(f"  Packet sizes: {len(config['packet_size']['common_sizes'])} common sizes")
        print(f"  Anti-fingerprinting: Enabled")
