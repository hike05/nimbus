"""
Trojan-Go configuration management for the Multi-Protocol Proxy Server.
Handles server configuration generation, client config creation, and user management.
"""

import json
import secrets
import string
from typing import Dict, List, Any, Optional
from pathlib import Path

from .interfaces import User, TrojanConfig


class TrojanManager:
    """Manages Trojan-Go server and client configurations."""
    
    def __init__(self, config_dir: str = "data/proxy/configs"):
        self.config_dir = Path(config_dir)
        self.server_config_path = self.config_dir / "trojan.json"
        self.template_path = self.config_dir / "trojan.template.json"
        
    def generate_password(self, length: int = 32) -> str:
        """Generate a secure random password for Trojan authentication."""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def load_template_config(self) -> Dict[str, Any]:
        """Load the Trojan server configuration template."""
        try:
            with open(self.template_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Trojan template config not found: {self.template_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in Trojan template: {e}")
    
    def generate_server_config(self, users: Dict[str, User]) -> Dict[str, Any]:
        """Generate Trojan-Go server configuration with user passwords."""
        template = self.load_template_config()
        
        # Extract passwords from active users
        passwords = []
        for user in users.values():
            if user.is_active and hasattr(user, 'trojan_password'):
                passwords.append(user.trojan_password)
        
        # Update template with user passwords
        template["password"] = passwords if passwords else ["default-password-change-me"]
        
        return template
    
    def save_server_config(self, config: Dict[str, Any]) -> bool:
        """Save Trojan server configuration to file."""
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
            print(f"Error saving Trojan server config: {e}")
            return False
    
    def generate_client_config(self, user: User, server_address: str = "your-domain.com") -> TrojanConfig:
        """Generate Trojan client configuration for a user."""
        return TrojanConfig(
            protocol="trojan",
            server_address=server_address,
            server_port=443,  # Using standard HTTPS port through Caddy
            password=user.trojan_password,
            sni="www.your-domain.com",
            websocket_enabled=True,
            websocket_path="/api/v1/files/sync",
            websocket_host="www.your-domain.com",
            fingerprint="firefox",
            alpn=["http/1.1", "h2"]
        )
    
    def generate_client_config_json(self, user: User, server_address: str = "your-domain.com") -> str:
        """Generate Trojan client configuration in JSON format."""
        config = {
            "run_type": "client",
            "local_addr": "127.0.0.1",
            "local_port": 1080,
            "remote_addr": server_address,
            "remote_port": 443,
            "password": [user.trojan_password],
            "log_level": 1,
            "ssl": {
                "verify": True,
                "verify_hostname": True,
                "cert": "",
                "cipher": "ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384",
                "cipher_tls13": "TLS_AES_128_GCM_SHA256:TLS_CHACHA20_POLY1305_SHA256:TLS_AES_256_GCM_SHA384",
                "sni": "www.your-domain.com",
                "alpn": ["http/1.1", "h2"],
                "reuse_session": True,
                "session_ticket": False,
                "curves": "",
                "fingerprint": "firefox"
            },
            "tcp": {
                "no_delay": True,
                "keep_alive": True,
                "reuse_port": False,
                "fast_open": False,
                "fast_open_qlen": 20
            },
            "websocket": {
                "enabled": True,
                "path": "/api/v1/files/sync",
                "host": "www.your-domain.com",
                "add_headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
            },
            "mux": {
                "enabled": True,
                "concurrency": 8,
                "idle_timeout": 60
            }
        }
        
        return json.dumps(config, indent=2)
    
    def generate_client_url(self, user: User, server_address: str = "your-domain.com") -> str:
        """Generate Trojan URL for easy client import."""
        # Format: trojan://password@server:port?sni=domain&type=ws&host=domain&path=/path#name
        password = user.trojan_password
        sni = "www.your-domain.com"
        ws_path = "/api/v1/files/sync"
        ws_host = "www.your-domain.com"
        
        url = f"trojan://{password}@{server_address}:443"
        url += f"?sni={sni}&type=ws&host={ws_host}&path={ws_path}"
        url += f"&security=tls&alpn=http/1.1,h2&fp=firefox"
        url += f"#{user.username}-trojan"
        
        return url
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate Trojan server configuration."""
        required_fields = ["run_type", "local_addr", "local_port", "password", "ssl"]
        
        for field in required_fields:
            if field not in config:
                print(f"Missing required field in Trojan config: {field}")
                return False
        
        if not isinstance(config["password"], list) or not config["password"]:
            print("Trojan config must have at least one password")
            return False
        
        ssl_config = config.get("ssl", {})
        required_ssl_fields = ["cert", "key", "sni"]
        for field in required_ssl_fields:
            if field not in ssl_config:
                print(f"Missing required SSL field in Trojan config: {field}")
                return False
        
        return True
    
    def update_server_config(self, users: Dict[str, User]) -> bool:
        """Update Trojan server configuration with current users."""
        try:
            config = self.generate_server_config(users)
            
            if not self.validate_config(config):
                print("Generated Trojan config failed validation")
                return False
            
            return self.save_server_config(config)
        except Exception as e:
            print(f"Error updating Trojan server config: {e}")
            return False
    
    def get_client_configs(self, user: User, server_address: str = "your-domain.com") -> Dict[str, str]:
        """Get all Trojan client configuration formats for a user."""
        return {
            "trojan_json": self.generate_client_config_json(user, server_address),
            "trojan_url": self.generate_client_url(user, server_address)
        }
    
    def create_user_password(self) -> str:
        """Create a new Trojan password for a user."""
        return self.generate_password()
    
    def test_config_generation(self) -> bool:
        """Test configuration generation with dummy data."""
        try:
            # Create test user
            test_user = User(
                username="test_user",
                id="test-uuid",
                xray_uuid="test-xray-uuid",
                wireguard_private_key="test-wg-private",
                wireguard_public_key="test-wg-public",
                trojan_password=self.create_user_password(),
                created_at="2025-01-01T00:00:00Z",
                last_seen=None,
                is_active=True
            )
            
            # Test server config generation
            users = {"test_user": test_user}
            server_config = self.generate_server_config(users)
            
            if not self.validate_config(server_config):
                return False
            
            # Test client config generation
            client_configs = self.get_client_configs(test_user)
            
            if not client_configs.get("trojan_json") or not client_configs.get("trojan_url"):
                return False
            
            print("Trojan configuration generation test passed")
            return True
            
        except Exception as e:
            print(f"Trojan configuration test failed: {e}")
            return False