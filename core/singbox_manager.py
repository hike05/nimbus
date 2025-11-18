"""
Sing-box configuration management for the Multi-Protocol Proxy Server.
Handles ShadowTLS v3, Hysteria 2, and TUIC v5 protocols with proper masking.
"""

import json
import secrets
import string
import uuid
import base64
from typing import Dict, List, Any, Optional
from pathlib import Path

from .interfaces import User


class SingboxManager:
    """Manages Sing-box server and client configurations for multiple protocols."""
    
    def __init__(self, config_dir: str = "data/proxy/configs", domain: str = "your-domain.com"):
        self.config_dir = Path(config_dir)
        self.domain = domain
        self.server_config_path = self.config_dir / "singbox.json"
        self.template_path = self.config_dir / "singbox.template.json"
        
    def generate_password(self, length: int = 32) -> str:
        """Generate a secure random password."""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*-_=+"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def generate_uuid(self) -> str:
        """Generate a new UUID for TUIC protocol."""
        return str(uuid.uuid4())
    
    def generate_shadowsocks_key(self) -> str:
        """Generate Shadowsocks 2022 server key."""
        # Generate 32 random bytes for AES-256
        key_bytes = secrets.token_bytes(32)
        return base64.b64encode(key_bytes).decode('utf-8')
    
    def load_template_config(self) -> Dict[str, Any]:
        """Load the Sing-box server configuration template."""
        try:
            with open(self.template_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Sing-box template config not found: {self.template_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in Sing-box template: {e}")
    
    def generate_server_config(self, users: Dict[str, User]) -> Dict[str, Any]:
        """Generate Sing-box server configuration with all protocols."""
        template = self.load_template_config()
        
        # Generate user configurations for each protocol
        shadowtls_users = []
        shadowsocks_users = []
        hysteria2_users = []
        tuic_users = []
        
        for user in users.values():
            if user.is_active:
                # ShadowTLS v3 users
                if hasattr(user, 'shadowtls_password'):
                    shadowtls_users.append({
                        "name": user.username,
                        "password": user.shadowtls_password
                    })
                
                # Shadowsocks users (underlying protocol for ShadowTLS)
                if hasattr(user, 'shadowsocks_password'):
                    shadowsocks_users.append({
                        "name": user.username,
                        "password": user.shadowsocks_password
                    })
                
                # Hysteria 2 users
                if hasattr(user, 'hysteria2_password'):
                    hysteria2_users.append({
                        "name": user.username,
                        "password": user.hysteria2_password
                    })
                
                # TUIC v5 users
                if hasattr(user, 'tuic_uuid') and hasattr(user, 'tuic_password'):
                    tuic_users.append({
                        "name": user.username,
                        "uuid": user.tuic_uuid,
                        "password": user.tuic_password
                    })
        
        # Replace template variables
        config_str = json.dumps(template)
        config_str = config_str.replace("DOMAIN_PLACEHOLDER", self.domain)
        config_str = config_str.replace('"SHADOWTLS_USERS_PLACEHOLDER"', json.dumps(shadowtls_users))
        config_str = config_str.replace('"SHADOWSOCKS_USERS_PLACEHOLDER"', json.dumps(shadowsocks_users))
        config_str = config_str.replace('"HYSTERIA2_USERS_PLACEHOLDER"', json.dumps(hysteria2_users))
        config_str = config_str.replace('"TUIC_USERS_PLACEHOLDER"', json.dumps(tuic_users))
        
        # Generate server passwords/keys
        config_str = config_str.replace("SHADOWSOCKS_SERVER_PASSWORD_PLACEHOLDER", self.generate_shadowsocks_key())
        config_str = config_str.replace("HYSTERIA2_OBFS_PASSWORD_PLACEHOLDER", self.generate_password(16))
        config_str = config_str.replace('"BANDWIDTH_UP_PLACEHOLDER"', "100")
        config_str = config_str.replace('"BANDWIDTH_DOWN_PLACEHOLDER"', "100")
        
        return json.loads(config_str)
    
    def save_server_config(self, config: Dict[str, Any]) -> bool:
        """Save Sing-box server configuration to file."""
        try:
            # Create backup of existing config
            if self.server_config_path.exists():
                backup_path = self.server_config_path.with_suffix('.json.backup')
                self.server_config_path.rename(backup_path)
            
            # Write new configuration
            with open(self.server_config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving Sing-box server config: {e}")
            return False
    
    def generate_shadowtls_client_config(self, user: User) -> Dict[str, Any]:
        """Generate ShadowTLS v3 client configuration."""
        return {
            "type": "shadowtls",
            "server": self.domain,
            "server_port": 443,
            "version": 3,
            "password": user.shadowtls_password,
            "tls": {
                "enabled": True,
                "server_name": f"api.{self.domain}",
                "insecure": False
            },
            "detour": "shadowsocks-out"
        }
    
    def generate_hysteria2_client_config(self, user: User) -> Dict[str, Any]:
        """Generate Hysteria 2 client configuration."""
        return {
            "type": "hysteria2",
            "server": self.domain,
            "server_port": 443,
            "password": user.hysteria2_password,
            "tls": {
                "enabled": True,
                "server_name": f"cdn.{self.domain}",
                "insecure": False,
                "alpn": ["h3"]
            },
            "obfs": {
                "type": "salamander",
                "salamander": {
                    "password": "obfs-password-from-server"
                }
            },
            "up_mbps": 100,
            "down_mbps": 100
        }
    
    def generate_tuic_client_config(self, user: User) -> Dict[str, Any]:
        """Generate TUIC v5 client configuration."""
        return {
            "type": "tuic",
            "server": self.domain,
            "server_port": 443,
            "uuid": user.tuic_uuid,
            "password": user.tuic_password,
            "congestion_control": "bbr",
            "udp_relay_mode": "native",
            "zero_rtt_handshake": False,
            "heartbeat": "10s",
            "tls": {
                "enabled": True,
                "server_name": f"files.{self.domain}",
                "insecure": False,
                "alpn": ["h3", "h3-29", "h3-Q050"]
            }
        }
    
    def generate_client_config_json(self, user: User, protocol: str) -> str:
        """Generate complete client configuration JSON for specified protocol."""
        if protocol == "shadowtls":
            outbound = self.generate_shadowtls_client_config(user)
            # Add shadowsocks outbound for ShadowTLS
            shadowsocks_out = {
                "type": "shadowsocks",
                "tag": "shadowsocks-out",
                "server": "127.0.0.1",
                "server_port": 8004,
                "method": "2022-blake3-aes-256-gcm",
                "password": user.shadowsocks_password
            }
        elif protocol == "hysteria2":
            outbound = self.generate_hysteria2_client_config(user)
            shadowsocks_out = None
        elif protocol == "tuic":
            outbound = self.generate_tuic_client_config(user)
            shadowsocks_out = None
        else:
            raise ValueError(f"Unsupported protocol: {protocol}")
        
        # Complete client configuration
        client_config = {
            "log": {
                "level": "warn",
                "timestamp": True
            },
            "inbounds": [
                {
                    "type": "mixed",
                    "listen": "127.0.0.1",
                    "listen_port": 1080,
                    "sniff": True,
                    "sniff_override_destination": True
                }
            ],
            "outbounds": [
                outbound,
                {
                    "type": "direct",
                    "tag": "direct"
                },
                {
                    "type": "block",
                    "tag": "block"
                }
            ],
            "route": {
                "rules": [
                    {
                        "geoip": "private",
                        "outbound": "direct"
                    }
                ],
                "final": "proxy",
                "auto_detect_interface": True
            }
        }
        
        # Add shadowsocks outbound if needed
        if shadowsocks_out:
            client_config["outbounds"].insert(1, shadowsocks_out)
        
        return json.dumps(client_config, indent=2)
    
    def generate_client_url(self, user: User, protocol: str) -> str:
        """Generate client URL for easy import."""
        if protocol == "shadowtls":
            # ShadowTLS doesn't have a standard URL format, return JSON config info
            return f"shadowtls://{user.shadowtls_password}@{self.domain}:443?sni=api.{self.domain}&version=3#{user.username}-shadowtls"
        
        elif protocol == "hysteria2":
            # Hysteria 2 URL format
            return f"hysteria2://{user.hysteria2_password}@{self.domain}:443?sni=cdn.{self.domain}&obfs=salamander&obfs-password=obfs-password#{user.username}-hysteria2"
        
        elif protocol == "tuic":
            # TUIC URL format
            return f"tuic://{user.tuic_uuid}:{user.tuic_password}@{self.domain}:443?sni=files.{self.domain}&congestion_control=bbr&alpn=h3#{user.username}-tuic"
        
        else:
            raise ValueError(f"Unsupported protocol: {protocol}")
    
    def get_client_configs(self, user: User) -> Dict[str, str]:
        """Get all Sing-box client configuration formats for a user."""
        configs = {}
        
        # Generate configs for each protocol
        protocols = ["shadowtls", "hysteria2", "tuic"]
        
        for protocol in protocols:
            try:
                configs[f"{protocol}_json"] = self.generate_client_config_json(user, protocol)
                configs[f"{protocol}_url"] = self.generate_client_url(user, protocol)
            except Exception as e:
                print(f"Error generating {protocol} config for {user.username}: {e}")
        
        return configs
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate Sing-box server configuration."""
        required_fields = ["inbounds", "outbounds"]
        
        for field in required_fields:
            if field not in config:
                print(f"Missing required field in Sing-box config: {field}")
                return False
        
        # Validate inbounds
        inbounds = config.get("inbounds", [])
        if not isinstance(inbounds, list) or not inbounds:
            print("Sing-box config must have at least one inbound")
            return False
        
        # Check for required inbound types
        inbound_types = [inbound.get("type") for inbound in inbounds]
        required_types = ["shadowtls", "hysteria2", "tuic"]
        
        for req_type in required_types:
            if req_type not in inbound_types:
                print(f"Missing required inbound type: {req_type}")
                return False
        
        return True
    
    def update_server_config(self, users: Dict[str, User]) -> bool:
        """Update Sing-box server configuration with current users."""
        try:
            config = self.generate_server_config(users)
            
            if not self.validate_config(config):
                print("Generated Sing-box config failed validation")
                return False
            
            return self.save_server_config(config)
        except Exception as e:
            print(f"Error updating Sing-box server config: {e}")
            return False
    
    def create_user_credentials(self) -> Dict[str, str]:
        """Create new credentials for all Sing-box protocols for a user."""
        return {
            "shadowtls_password": self.generate_password(32),
            "shadowsocks_password": self.generate_password(32),
            "hysteria2_password": self.generate_password(32),
            "tuic_uuid": self.generate_uuid(),
            "tuic_password": self.generate_password(32)
        }
    
    def test_config_generation(self) -> bool:
        """Test configuration generation with dummy data."""
        try:
            # Create test user with Sing-box credentials
            test_user = User(
                username="test_user",
                id="test-uuid",
                xray_uuid="test-xray-uuid",
                wireguard_private_key="test-wg-private",
                wireguard_public_key="test-wg-public",
                trojan_password=self.generate_password(),
                created_at="2025-01-01T00:00:00Z",
                last_seen=None,
                is_active=True
            )
            
            # Add Sing-box credentials
            credentials = self.create_user_credentials()
            for key, value in credentials.items():
                setattr(test_user, key, value)
            
            # Test server config generation
            users = {"test_user": test_user}
            server_config = self.generate_server_config(users)
            
            if not self.validate_config(server_config):
                return False
            
            # Test client config generation
            client_configs = self.get_client_configs(test_user)
            
            expected_configs = ["shadowtls_json", "shadowtls_url", "hysteria2_json", "hysteria2_url", "tuic_json", "tuic_url"]
            for config_type in expected_configs:
                if not client_configs.get(config_type):
                    print(f"Missing client config: {config_type}")
                    return False
            
            print("Sing-box configuration generation test passed")
            return True
            
        except Exception as e:
            print(f"Sing-box configuration test failed: {e}")
            return False


def create_singbox_user_data(username: str) -> Dict[str, str]:
    """Create Sing-box-specific user data for a new user."""
    manager = SingboxManager()
    return manager.create_user_credentials()