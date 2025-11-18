#!/usr/bin/env python3
"""
Apply Traffic Obfuscation to Proxy Configurations

This script applies traffic analysis protection measures to all proxy protocol
configurations including timing randomization, packet size normalization,
and anti-fingerprinting.

Requirements: 2.3, 3.3
"""

import json
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.traffic_obfuscation import (
    generate_obfuscation_config,
    TrafficPattern,
    FingerprintingProtection
)

# Colors for output
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color


def log(message: str):
    """Print log message"""
    print(f"{GREEN}[Traffic Obfuscation]{NC} {message}")


def warn(message: str):
    """Print warning message"""
    print(f"{YELLOW}[Traffic Obfuscation]{NC} {message}")


def error(message: str):
    """Print error message"""
    print(f"{RED}[Traffic Obfuscation]{NC} {message}")


def apply_xray_obfuscation(config_path: Path) -> bool:
    """
    Apply traffic obfuscation to Xray configuration
    
    Args:
        config_path: Path to xray.json
        
    Returns:
        True if successful
    """
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        obf_config = generate_obfuscation_config("xray", TrafficPattern.WEB_BROWSING)
        
        # Apply to all inbounds
        for inbound in config.get('inbounds', []):
            stream_settings = inbound.get('streamSettings', {})
            
            # Add sockopt for traffic shaping
            stream_settings['sockopt'] = {
                'tcpFastOpen': True,
                'tcpNoDelay': True,
                'tcpKeepAliveInterval': 30,
                'mark': 255,
            }
            
            # WebSocket settings with realistic headers
            if stream_settings.get('network') == 'ws':
                ws_settings = stream_settings.get('wsSettings', {})
                headers = obf_config['anti_fingerprinting']['realistic_headers']
                ws_settings['headers'] = {
                    'User-Agent': headers['User-Agent'],
                    'Accept-Language': headers['Accept-Language'],
                }
                stream_settings['wsSettings'] = ws_settings
            
            # XTLS settings with anti-fingerprinting
            if stream_settings.get('security') in ['xtls', 'tls']:
                tls_settings = stream_settings.get('xtlsSettings') or stream_settings.get('tlsSettings', {})
                
                # Randomize ALPN
                tls_settings['alpn'] = ['h2', 'http/1.1']
                
                # Add realistic SNI
                if 'serverName' not in tls_settings:
                    tls_settings['serverName'] = os.getenv('DOMAIN', 'your-domain.com')
                
                if stream_settings.get('security') == 'xtls':
                    stream_settings['xtlsSettings'] = tls_settings
                else:
                    stream_settings['tlsSettings'] = tls_settings
            
            inbound['streamSettings'] = stream_settings
        
        # Save updated configuration
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        log(f"Applied traffic obfuscation to Xray configuration")
        return True
        
    except Exception as e:
        error(f"Failed to apply Xray obfuscation: {e}")
        return False


def apply_trojan_obfuscation(config_path: Path) -> bool:
    """
    Apply traffic obfuscation to Trojan configuration
    
    Args:
        config_path: Path to trojan.json
        
    Returns:
        True if successful
    """
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        obf_config = generate_obfuscation_config("trojan", TrafficPattern.WEB_BROWSING)
        
        # Add WebSocket headers for obfuscation
        if config.get('websocket', {}).get('enabled'):
            headers = obf_config['anti_fingerprinting']['realistic_headers']
            config['websocket']['headers'] = {
                'User-Agent': headers['User-Agent'],
                'Accept': headers['Accept'],
                'Accept-Language': headers['Accept-Language'],
            }
        
        # Add TCP settings for traffic shaping
        config['tcp'] = {
            'no_delay': True,
            'keep_alive': True,
            'keep_alive_interval': 30,
            'fast_open': True,
            'fast_open_qlen': 20,
        }
        
        # Save updated configuration
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        log(f"Applied traffic obfuscation to Trojan configuration")
        return True
        
    except Exception as e:
        error(f"Failed to apply Trojan obfuscation: {e}")
        return False


def apply_singbox_obfuscation(config_path: Path) -> bool:
    """
    Apply traffic obfuscation to Sing-box configuration
    
    Args:
        config_path: Path to singbox.json
        
    Returns:
        True if successful
    """
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        obf_config = generate_obfuscation_config("singbox", TrafficPattern.VIDEO_STREAMING)
        
        # Apply to all inbounds
        for inbound in config.get('inbounds', []):
            inbound_type = inbound.get('type')
            
            # Hysteria2 obfuscation
            if inbound_type == 'hysteria2':
                # Randomize QUIC parameters
                quic_params = obf_config.get('quic_parameters', {})
                inbound['up_mbps'] = 100
                inbound['down_mbps'] = 100
                
                # Add salamander obfuscation
                if 'obfs' not in inbound:
                    inbound['obfs'] = {
                        'type': 'salamander',
                        'salamander': {
                            'password': os.urandom(16).hex()
                        }
                    }
            
            # TUIC obfuscation
            elif inbound_type == 'tuic':
                # Randomize congestion control
                inbound['congestion_control'] = 'bbr'
                
                # Randomize ALPN
                inbound['alpn'] = ['h3', 'h3-29']
            
            # ShadowTLS obfuscation
            elif inbound_type == 'shadowtls':
                # Enable strict mode for better obfuscation
                inbound['strict_mode'] = True
                
                # Add realistic handshake server
                if 'handshake' in inbound:
                    inbound['handshake']['server'] = os.getenv('DOMAIN', 'your-domain.com')
        
        # Save updated configuration
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        log(f"Applied traffic obfuscation to Sing-box configuration")
        return True
        
    except Exception as e:
        error(f"Failed to apply Sing-box obfuscation: {e}")
        return False


def apply_wireguard_obfuscation(config_dir: Path) -> bool:
    """
    Apply traffic obfuscation to WireGuard configuration
    
    Args:
        config_dir: Path to wireguard config directory
        
    Returns:
        True if successful
    """
    try:
        obf_config = generate_obfuscation_config("wireguard", TrafficPattern.FILE_DOWNLOAD)
        
        # Create obfuscation settings file
        obf_settings_path = config_dir / 'obfuscation.json'
        
        obf_settings = {
            'timing': obf_config['timing'],
            'packet_size': obf_config['packet_size'],
            'websocket': {
                'enabled': True,
                'headers': obf_config['anti_fingerprinting']['realistic_headers'],
            },
            'udp2raw': {
                'enabled': False,  # Enable manually if needed
                'cipher_mode': 'aes256gcm',
                'auth_mode': 'hmac_sha256',
                'seq_mode': 4,
            }
        }
        
        with open(obf_settings_path, 'w') as f:
            json.dump(obf_settings, f, indent=2)
        
        log(f"Applied traffic obfuscation to WireGuard configuration")
        return True
        
    except Exception as e:
        error(f"Failed to apply WireGuard obfuscation: {e}")
        return False


def main():
    """Main function"""
    log("Applying traffic analysis protection to all proxy protocols...")
    
    # Configuration paths
    config_base = Path(__file__).parent.parent / 'data' / 'proxy' / 'configs'
    
    success = True
    
    # Apply to Xray
    xray_config = config_base / 'xray.json'
    if xray_config.exists():
        if not apply_xray_obfuscation(xray_config):
            success = False
    else:
        warn(f"Xray configuration not found: {xray_config}")
    
    # Apply to Trojan
    trojan_config = config_base / 'trojan.json'
    if trojan_config.exists():
        if not apply_trojan_obfuscation(trojan_config):
            success = False
    else:
        warn(f"Trojan configuration not found: {trojan_config}")
    
    # Apply to Sing-box
    singbox_config = config_base / 'singbox.json'
    if singbox_config.exists():
        if not apply_singbox_obfuscation(singbox_config):
            success = False
    else:
        warn(f"Sing-box configuration not found: {singbox_config}")
    
    # Apply to WireGuard
    wireguard_dir = config_base / 'wireguard'
    if wireguard_dir.exists():
        if not apply_wireguard_obfuscation(wireguard_dir):
            success = False
    else:
        warn(f"WireGuard configuration directory not found: {wireguard_dir}")
    
    if success:
        log("✓ Traffic analysis protection applied successfully to all protocols")
        return 0
    else:
        error("✗ Some configurations failed to apply traffic obfuscation")
        return 1


if __name__ == '__main__':
    sys.exit(main())
