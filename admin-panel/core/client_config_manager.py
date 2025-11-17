"""
Client configuration file management.
Saves individual client configuration files for each user.
"""

import json
from pathlib import Path
from typing import Dict

import sys
sys.path.insert(0, '/app/core')
from interfaces import User
from config_generator import ConfigGenerator
from qr_generator import QRCodeGenerator


class ClientConfigManager:
    """Manages client configuration files."""
    
    def __init__(self, config_dir: str = "/data/stealth-vpn/configs", domain: str = "your-domain.com"):
        self.config_dir = Path(config_dir)
        self.clients_dir = self.config_dir / "clients"
        self.domain = domain
        self.config_generator = ConfigGenerator(str(self.config_dir), domain)
        self.qr_generator = QRCodeGenerator(str(self.config_dir), domain)
        
        # Ensure clients directory exists
        self.clients_dir.mkdir(parents=True, exist_ok=True)
    
    def save_client_configs(self, username: str, user: User) -> bool:
        """Save all client configuration files for a user."""
        try:
            # Create user directory
            user_dir = self.clients_dir / username
            user_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate all configs
            configs = self.config_generator.generate_client_configs(username, user)
            
            # Save Xray XTLS config
            if 'xray_xtls_json' in configs:
                with open(user_dir / "xray-xtls.json", 'w') as f:
                    f.write(configs['xray_xtls_json'])
            
            # Save Xray WebSocket config
            if 'xray_ws_json' in configs:
                with open(user_dir / "xray-ws.json", 'w') as f:
                    f.write(configs['xray_ws_json'])
            
            # Save Trojan config
            if 'trojan_json' in configs:
                with open(user_dir / "trojan.json", 'w') as f:
                    f.write(configs['trojan_json'])
            
            # Save Sing-box configs
            if 'shadowtls_json' in configs:
                with open(user_dir / "singbox-shadowtls.json", 'w') as f:
                    f.write(configs['shadowtls_json'])
            
            if 'hysteria2_json' in configs:
                with open(user_dir / "singbox-hysteria2.json", 'w') as f:
                    f.write(configs['hysteria2_json'])
            
            if 'tuic_json' in configs:
                with open(user_dir / "singbox-tuic.json", 'w') as f:
                    f.write(configs['tuic_json'])
            
            # Save WireGuard configs
            if 'wireguard_conf' in configs:
                with open(user_dir / "wireguard.conf", 'w') as f:
                    f.write(configs['wireguard_conf'])
            
            if 'wireguard_obfs_conf' in configs:
                with open(user_dir / "wireguard-websocket.conf", 'w') as f:
                    f.write(configs['wireguard_obfs_conf'])
            
            # Save connection links
            links_content = f"""# VPN Connection Links for {username}

## Xray XTLS-Vision (Recommended for Desktop)
{configs.get('xray_xtls_link', 'N/A')}

## Xray WebSocket (Fallback)
{configs.get('xray_ws_link', 'N/A')}

## Trojan-Go (Alternative Protocol)
{configs.get('trojan_link', 'N/A')}

## Hysteria2 (High Speed, UDP-based)
{configs.get('hysteria2_link', 'N/A')}

## ShadowTLS v3
See singbox-shadowtls.json file

## TUIC v5
See singbox-tuic.json file

## WireGuard (Native)
See wireguard.conf file

## WireGuard over WebSocket (Obfuscated)
See wireguard-websocket.conf file

## Usage Instructions

### For Mobile (iOS/Android):
1. Install appropriate VPN client app:
   - Xray/Trojan: v2rayNG (Android) or Shadowrocket (iOS)
   - Sing-box protocols: Sing-box app (Android/iOS)
   - Hysteria2: Clash Meta or Sing-box
   - WireGuard: WireGuard app (Android/iOS)

2. Scan QR code or import configuration link/file

### For Desktop:
1. Use JSON configuration files with appropriate client:
   - Xray: Xray-core, v2rayN (Windows), or Qv2ray
   - Trojan: Trojan-Go client or Clash
   - Sing-box: Sing-box client
   - WireGuard: WireGuard client

2. Import the .json or .conf file

### Protocol Recommendations:
- **Best Performance**: Hysteria2 (UDP-based, requires good network)
- **Best Compatibility**: Xray XTLS-Vision (works everywhere)
- **Best Obfuscation**: ShadowTLS v3 or WireGuard over WebSocket
- **Simplest Setup**: WireGuard native

### Server Information
Domain: {self.domain}
Port: 443 (HTTPS)
All protocols use standard HTTPS port for maximum compatibility
"""
            
            with open(user_dir / "xray-links.txt", 'w') as f:
                f.write(links_content)
            
            # Generate and save QR codes
            try:
                self.qr_generator.save_qr_codes(username, user, str(user_dir))
            except Exception as e:
                print(f"Warning: Could not generate QR codes for {username}: {e}")
            
            return True
        except Exception as e:
            print(f"Error saving client configs for {username}: {e}")
            return False
    
    def delete_client_configs(self, username: str) -> bool:
        """Delete all client configuration files for a user."""
        try:
            user_dir = self.clients_dir / username
            if user_dir.exists():
                import shutil
                shutil.rmtree(user_dir)
            return True
        except Exception as e:
            print(f"Error deleting client configs for {username}: {e}")
            return False
    
    def get_client_config_path(self, username: str) -> Path:
        """Get the path to a user's client configuration directory."""
        return self.clients_dir / username
    
    def get_qr_codes(self, username: str, user: User) -> Dict[str, str]:
        """Get QR codes as base64 encoded strings for web display."""
        try:
            return self.qr_generator.generate_all_qr_codes(username, user)
        except Exception as e:
            print(f"Error generating QR codes for {username}: {e}")
            return {}
