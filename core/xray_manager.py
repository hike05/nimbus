"""
Xray configuration management for the Stealth VPN Server.
Handles server configuration generation, client config templates, and user management.
"""

import json
import uuid
import secrets
import base64
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

from .interfaces import User, ConfigGeneratorInterface, XrayConfig


class XrayConfigManager(ConfigGeneratorInterface):
    """Manages Xray server and client configurations."""
    
    def __init__(self, config_dir: str = "/data/stealth-vpn/configs", domain: str = "your-domain.com"):
        self.config_dir = Path(config_dir)
        self.domain = domain
        self.template_path = self.config_dir / "xray.template.json"
        self.config_path = self.config_dir / "xray.json"
        
    def generate_xray_server_config(self, users: Dict[str, User]) -> Dict[str, Any]:
        """Generate Xray server configuration with all users."""
        
        # Load template
        with open(self.template_path, 'r') as f:
            template = f.read()
        
        # Generate client configurations for XTLS-Vision
        xtls_clients = []
        ws_clients = []
        
        for user in users.values():
            if user.is_active:
                # XTLS-Vision client
                xtls_client = {
                    "id": user.xray_uuid,
                    "flow": "xtls-rprx-vision",
                    "email": f"{user.username}@{self.domain}"
                }
                xtls_clients.append(xtls_client)
                
                # WebSocket client (same UUID, different flow)
                ws_client = {
                    "id": user.xray_uuid,
                    "email": f"{user.username}@{self.domain}"
                }
                ws_clients.append(ws_client)
        
        # Replace template variables
        config_content = template.replace("{{DOMAIN}}", self.domain)
        config_content = config_content.replace("{{WEBSOCKET_PATH}}", "/cdn/assets/js/analytics.min.js")
        config_content = config_content.replace("{{VLESS_XTLS_CLIENTS}}", 
                                              json.dumps(xtls_clients, indent=10)[1:-1])  # Remove outer brackets
        config_content = config_content.replace("{{VLESS_WS_CLIENTS}}", 
                                              json.dumps(ws_clients, indent=10)[1:-1])  # Remove outer brackets
        
        # Parse and return as dict
        return json.loads(config_content)
    
    def generate_wireguard_server_config(self, users: Dict[str, User]) -> str:
        """Generate WireGuard server configuration (placeholder for interface compliance)."""
        # This will be implemented in the WireGuard task
        return ""
    
    def generate_client_configs(self, username: str, user: User) -> Dict[str, str]:
        """Generate all Xray client configurations for a user."""
        configs = {}
        
        # VLESS-XTLS-Vision configuration
        xtls_config = self._generate_vless_xtls_config(user)
        configs["xray_xtls_json"] = json.dumps(xtls_config, indent=2)
        configs["xray_xtls_link"] = self._generate_vless_link(user, "xtls")
        
        # VLESS-WebSocket configuration
        ws_config = self._generate_vless_ws_config(user)
        configs["xray_ws_json"] = json.dumps(ws_config, indent=2)
        configs["xray_ws_link"] = self._generate_vless_link(user, "ws")
        
        return configs
    
    def _generate_vless_xtls_config(self, user: User) -> Dict[str, Any]:
        """Generate VLESS-XTLS-Vision client configuration."""
        return {
            "log": {
                "loglevel": "warning"
            },
            "inbounds": [
                {
                    "tag": "socks",
                    "port": 10808,
                    "listen": "127.0.0.1",
                    "protocol": "socks",
                    "sniffing": {
                        "enabled": True,
                        "destOverride": ["http", "tls"]
                    },
                    "settings": {
                        "auth": "noauth",
                        "udp": True
                    }
                },
                {
                    "tag": "http",
                    "port": 10809,
                    "listen": "127.0.0.1",
                    "protocol": "http",
                    "sniffing": {
                        "enabled": True,
                        "destOverride": ["http", "tls"]
                    }
                }
            ],
            "outbounds": [
                {
                    "tag": "proxy",
                    "protocol": "vless",
                    "settings": {
                        "vnext": [
                            {
                                "address": self.domain,
                                "port": 443,
                                "users": [
                                    {
                                        "id": user.xray_uuid,
                                        "flow": "xtls-rprx-vision",
                                        "encryption": "none"
                                    }
                                ]
                            }
                        ]
                    },
                    "streamSettings": {
                        "network": "tcp",
                        "security": "xtls",
                        "xtlsSettings": {
                            "flow": "xtls-rprx-vision",
                            "serverName": self.domain,
                            "allowInsecure": False
                        }
                    }
                },
                {
                    "tag": "direct",
                    "protocol": "freedom"
                },
                {
                    "tag": "block",
                    "protocol": "blackhole"
                }
            ],
            "routing": {
                "domainStrategy": "IPIfNonMatch",
                "rules": [
                    {
                        "type": "field",
                        "ip": ["geoip:private"],
                        "outboundTag": "direct"
                    },
                    {
                        "type": "field",
                        "ip": ["geoip:cn"],
                        "outboundTag": "direct"
                    },
                    {
                        "type": "field",
                        "domain": ["geosite:cn"],
                        "outboundTag": "direct"
                    }
                ]
            }
        }
    
    def _generate_vless_ws_config(self, user: User) -> Dict[str, Any]:
        """Generate VLESS-WebSocket client configuration."""
        return {
            "log": {
                "loglevel": "warning"
            },
            "inbounds": [
                {
                    "tag": "socks",
                    "port": 10808,
                    "listen": "127.0.0.1",
                    "protocol": "socks",
                    "sniffing": {
                        "enabled": True,
                        "destOverride": ["http", "tls"]
                    },
                    "settings": {
                        "auth": "noauth",
                        "udp": True
                    }
                },
                {
                    "tag": "http",
                    "port": 10809,
                    "listen": "127.0.0.1",
                    "protocol": "http",
                    "sniffing": {
                        "enabled": True,
                        "destOverride": ["http", "tls"]
                    }
                }
            ],
            "outbounds": [
                {
                    "tag": "proxy",
                    "protocol": "vless",
                    "settings": {
                        "vnext": [
                            {
                                "address": self.domain,
                                "port": 443,
                                "users": [
                                    {
                                        "id": user.xray_uuid,
                                        "encryption": "none"
                                    }
                                ]
                            }
                        ]
                    },
                    "streamSettings": {
                        "network": "ws",
                        "security": "tls",
                        "wsSettings": {
                            "path": "/cdn/assets/js/analytics.min.js",
                            "headers": {
                                "Host": self.domain
                            }
                        },
                        "tlsSettings": {
                            "serverName": self.domain,
                            "allowInsecure": False
                        }
                    }
                },
                {
                    "tag": "direct",
                    "protocol": "freedom"
                },
                {
                    "tag": "block",
                    "protocol": "blackhole"
                }
            ],
            "routing": {
                "domainStrategy": "IPIfNonMatch",
                "rules": [
                    {
                        "type": "field",
                        "ip": ["geoip:private"],
                        "outboundTag": "direct"
                    },
                    {
                        "type": "field",
                        "ip": ["geoip:cn"],
                        "outboundTag": "direct"
                    },
                    {
                        "type": "field",
                        "domain": ["geosite:cn"],
                        "outboundTag": "direct"
                    }
                ]
            }
        }
    
    def _generate_vless_link(self, user: User, protocol_type: str) -> str:
        """Generate VLESS share link for mobile clients."""
        if protocol_type == "xtls":
            # VLESS-XTLS-Vision link
            params = {
                "encryption": "none",
                "flow": "xtls-rprx-vision",
                "security": "xtls",
                "sni": self.domain,
                "type": "tcp",
                "headerType": "none"
            }
            param_str = "&".join([f"{k}={v}" for k, v in params.items()])
            link = f"vless://{user.xray_uuid}@{self.domain}:443?{param_str}#{user.username}-XTLS"
            
        elif protocol_type == "ws":
            # VLESS-WebSocket link
            params = {
                "encryption": "none",
                "security": "tls",
                "sni": self.domain,
                "type": "ws",
                "host": self.domain,
                "path": "/cdn/assets/js/analytics.min.js"
            }
            param_str = "&".join([f"{k}={v}" for k, v in params.items()])
            link = f"vless://{user.xray_uuid}@{self.domain}:443?{param_str}#{user.username}-WS"
        
        return link
    
    def update_server_configs(self) -> bool:
        """Update Xray server configuration and reload service."""
        try:
            # This will be called by the user management system
            # For now, just return True as the actual reload will be handled by the service manager
            return True
        except Exception as e:
            print(f"Error updating Xray server config: {e}")
            return False
    
    def save_server_config(self, config: Dict[str, Any]) -> bool:
        """Save the generated server configuration to file."""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving Xray config: {e}")
            return False


class XrayUserManager:
    """Manages Xray-specific user operations."""
    
    @staticmethod
    def generate_xray_uuid() -> str:
        """Generate a new UUID for Xray user."""
        return str(uuid.uuid4())
    
    @staticmethod
    def generate_xray_private_key() -> str:
        """Generate Xray private key (for future use with Reality protocol)."""
        # Generate 32 random bytes and encode as base64
        key_bytes = secrets.token_bytes(32)
        return base64.b64encode(key_bytes).decode('utf-8')
    
    @staticmethod
    def validate_xray_uuid(uuid_str: str) -> bool:
        """Validate Xray UUID format."""
        try:
            uuid.UUID(uuid_str)
            return True
        except ValueError:
            return False


def create_xray_user_data(username: str) -> Dict[str, str]:
    """Create Xray-specific user data for a new user."""
    return {
        "xray_uuid": XrayUserManager.generate_xray_uuid(),
        "xray_private_key": XrayUserManager.generate_xray_private_key()
    }