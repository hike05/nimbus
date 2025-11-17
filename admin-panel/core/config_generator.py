"""
Configuration generator for all VPN protocols.
Generates server and client configurations for Xray, Trojan, Sing-box, and WireGuard.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional

sys.path.insert(0, '/app/core')
sys.path.insert(0, '/app')
from interfaces import User, ConfigGeneratorInterface
from user_storage import UserStorage

# Try to import endpoint manager
try:
    from core.endpoint_manager import EndpointManager
except ImportError:
    EndpointManager = None


class ConfigGenerator(ConfigGeneratorInterface):
    """Generates VPN server and client configurations."""
    
    def __init__(self, config_dir: str = "/data/stealth-vpn/configs", domain: str = "your-domain.com"):
        self.config_dir = Path(config_dir)
        self.domain = domain
        self.user_storage = UserStorage(config_dir)
        
        # Initialize endpoint manager
        self.endpoint_manager = None
        if EndpointManager:
            try:
                endpoints_path = Path(config_dir).parent / 'endpoints.json'
                self.endpoint_manager = EndpointManager(str(endpoints_path))
            except Exception as e:
                print(f"Warning: Could not initialize endpoint manager: {e}")
    
    def get_endpoint(self, service_name: str, default: str) -> str:
        """Get obfuscated endpoint for a service."""
        if self.endpoint_manager:
            endpoint = self.endpoint_manager.get_endpoint_by_service(service_name)
            if endpoint:
                return endpoint
        return default
    
    def generate_xray_server_config(self, users: Dict[str, User]) -> Dict[str, Any]:
        """Generate Xray server configuration."""
        # Load template
        template_path = self.config_dir / "xray.template.json"
        if not template_path.exists():
            return {}
        
        with open(template_path, 'r') as f:
            template = f.read()
        
        # Generate client lists
        xtls_clients = []
        ws_clients = []
        
        for user in users.values():
            if user.is_active:
                xtls_clients.append({
                    "id": user.xray_uuid,
                    "flow": "xtls-rprx-vision",
                    "email": f"{user.username}@{self.domain}"
                })
                ws_clients.append({
                    "id": user.xray_uuid,
                    "email": f"{user.username}@{self.domain}"
                })
        
        # Get obfuscated WebSocket path
        ws_path = self.get_endpoint('xray_websocket', '/cdn/assets/js/analytics.min.js')
        
        # Replace template variables
        config_content = template.replace("{{DOMAIN}}", self.domain)
        config_content = config_content.replace("{{WEBSOCKET_PATH}}", ws_path)
        config_content = config_content.replace("{{VLESS_XTLS_CLIENTS}}", 
                                              json.dumps(xtls_clients, indent=10)[1:-1])
        config_content = config_content.replace("{{VLESS_WS_CLIENTS}}", 
                                              json.dumps(ws_clients, indent=10)[1:-1])
        
        return json.loads(config_content)
    
    def generate_trojan_server_config(self, users: Dict[str, User]) -> Dict[str, Any]:
        """Generate Trojan-Go server configuration."""
        template_path = self.config_dir / "trojan.template.json"
        if not template_path.exists():
            return {}
        
        with open(template_path, 'r') as f:
            template = f.read()
        
        # Generate password list
        passwords = [user.trojan_password for user in users.values() if user.is_active]
        
        # Get obfuscated WebSocket path
        ws_path = self.get_endpoint('trojan_websocket', '/api/v1/files/sync')
        
        config_content = template.replace("{{DOMAIN}}", self.domain)
        config_content = config_content.replace("{{PASSWORDS}}", json.dumps(passwords))
        config_content = config_content.replace("{{WEBSOCKET_PATH}}", ws_path)
        
        return json.loads(config_content)
    
    def generate_singbox_server_config(self, users: Dict[str, User]) -> Dict[str, Any]:
        """Generate Sing-box server configuration."""
        template_path = self.config_dir / "singbox.template.json"
        if not template_path.exists():
            return {}
        
        with open(template_path, 'r') as f:
            template = f.read()
        
        # Generate user lists for different protocols
        shadowtls_users = []
        hysteria2_users = []
        tuic_users = []
        
        for user in users.values():
            if user.is_active:
                if user.shadowtls_password:
                    shadowtls_users.append({
                        "name": user.username,
                        "password": user.shadowtls_password
                    })
                if user.hysteria2_password:
                    hysteria2_users.append({
                        "name": user.username,
                        "password": user.hysteria2_password
                    })
                if user.tuic_uuid and user.tuic_password:
                    tuic_users.append({
                        "name": user.username,
                        "uuid": user.tuic_uuid,
                        "password": user.tuic_password
                    })
        
        config_content = template.replace("{{DOMAIN}}", self.domain)
        config_content = config_content.replace("{{SHADOWTLS_USERS}}", json.dumps(shadowtls_users))
        config_content = config_content.replace("{{HYSTERIA2_USERS}}", json.dumps(hysteria2_users))
        config_content = config_content.replace("{{TUIC_USERS}}", json.dumps(tuic_users))
        
        return json.loads(config_content)
    
    def generate_wireguard_server_config(self, users: Dict[str, User]) -> str:
        """Generate WireGuard server configuration."""
        # Load server keys from users.json
        users_file = self.config_dir / "users.json"
        if not users_file.exists():
            return ""
        
        with open(users_file, 'r') as f:
            data = json.load(f)
        
        server_config = data.get("server", {})
        server_private_key = server_config.get("wireguard_server_private_key", "")
        
        config = f"""[Interface]
Address = 10.0.0.1/24
ListenPort = 51820
PrivateKey = {server_private_key}
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

"""
        
        # Add peers
        ip_counter = 2
        for user in users.values():
            if user.is_active:
                config += f"""# {user.username}
[Peer]
PublicKey = {user.wireguard_public_key}
AllowedIPs = 10.0.0.{ip_counter}/32

"""
                ip_counter += 1
        
        return config
    
    def generate_client_configs(self, username: str, user: User) -> Dict[str, str]:
        """Generate all client configurations for a user."""
        configs = {}
        
        # Xray XTLS-Vision
        configs['xray_xtls_link'] = self._generate_xray_xtls_link(user)
        configs['xray_xtls_json'] = self._generate_xray_xtls_json(user)
        
        # Xray WebSocket
        configs['xray_ws_link'] = self._generate_xray_ws_link(user)
        configs['xray_ws_json'] = self._generate_xray_ws_json(user)
        
        # Trojan
        configs['trojan_link'] = self._generate_trojan_link(user)
        configs['trojan_json'] = self._generate_trojan_json(user)
        
        # Sing-box protocols
        if user.shadowtls_password:
            configs['shadowtls_json'] = self._generate_shadowtls_json(user)
        if user.hysteria2_password:
            configs['hysteria2_link'] = self._generate_hysteria2_link(user)
            configs['hysteria2_json'] = self._generate_hysteria2_json(user)
        if user.tuic_uuid and user.tuic_password:
            configs['tuic_json'] = self._generate_tuic_json(user)
        
        # WireGuard
        configs['wireguard_conf'] = self._generate_wireguard_conf(user)
        configs['wireguard_obfs_conf'] = self._generate_wireguard_obfs_conf(user)
        
        return configs
    
    def _generate_xray_xtls_link(self, user: User) -> str:
        """Generate Xray XTLS-Vision connection link."""
        import urllib.parse
        params = {
            'type': 'tcp',
            'security': 'xtls',
            'flow': 'xtls-rprx-vision',
            'sni': self.domain,
            'fp': 'chrome'
        }
        param_str = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"vless://{user.xray_uuid}@{self.domain}:443?{param_str}#{user.username}-xtls"
    
    def _generate_xray_xtls_json(self, user: User) -> str:
        """Generate Xray XTLS-Vision JSON config."""
        config = {
            "outbounds": [{
                "protocol": "vless",
                "settings": {
                    "vnext": [{
                        "address": self.domain,
                        "port": 443,
                        "users": [{
                            "id": user.xray_uuid,
                            "flow": "xtls-rprx-vision",
                            "encryption": "none"
                        }]
                    }]
                },
                "streamSettings": {
                    "network": "tcp",
                    "security": "xtls",
                    "xtlsSettings": {
                        "serverName": self.domain,
                        "fingerprint": "chrome"
                    }
                }
            }]
        }
        return json.dumps(config, indent=2)
    
    def _generate_xray_ws_link(self, user: User) -> str:
        """Generate Xray WebSocket connection link."""
        import urllib.parse
        ws_path = self.get_endpoint('xray_websocket', '/cdn/assets/js/analytics.min.js')
        params = {
            'type': 'ws',
            'path': ws_path,
            'host': self.domain,
            'security': 'tls',
            'sni': self.domain
        }
        param_str = '&'.join([f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items()])
        return f"vless://{user.xray_uuid}@{self.domain}:443?{param_str}#{user.username}-ws"
    
    def _generate_xray_ws_json(self, user: User) -> str:
        """Generate Xray WebSocket JSON config."""
        ws_path = self.get_endpoint('xray_websocket', '/cdn/assets/js/analytics.min.js')
        config = {
            "outbounds": [{
                "protocol": "vless",
                "settings": {
                    "vnext": [{
                        "address": self.domain,
                        "port": 443,
                        "users": [{
                            "id": user.xray_uuid,
                            "encryption": "none"
                        }]
                    }]
                },
                "streamSettings": {
                    "network": "ws",
                    "security": "tls",
                    "wsSettings": {
                        "path": ws_path,
                        "headers": {"Host": self.domain}
                    },
                    "tlsSettings": {
                        "serverName": self.domain
                    }
                }
            }]
        }
        return json.dumps(config, indent=2)
    
    def _generate_trojan_link(self, user: User) -> str:
        """Generate Trojan connection link."""
        import urllib.parse
        ws_path = self.get_endpoint('trojan_websocket', '/api/v1/files/sync')
        params = {
            'type': 'ws',
            'path': ws_path,
            'host': self.domain,
            'sni': self.domain
        }
        param_str = '&'.join([f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items()])
        return f"trojan://{user.trojan_password}@{self.domain}:443?{param_str}#{user.username}-trojan"
    
    def _generate_trojan_json(self, user: User) -> str:
        """Generate Trojan JSON config."""
        ws_path = self.get_endpoint('trojan_websocket', '/api/v1/files/sync')
        config = {
            "run_type": "client",
            "local_addr": "127.0.0.1",
            "local_port": 1080,
            "remote_addr": self.domain,
            "remote_port": 443,
            "password": [user.trojan_password],
            "ssl": {
                "sni": self.domain,
                "verify": True
            },
            "websocket": {
                "enabled": True,
                "path": ws_path,
                "host": self.domain
            }
        }
        return json.dumps(config, indent=2)
    
    def _generate_wireguard_conf(self, user: User) -> str:
        """Generate WireGuard client configuration."""
        # Load server public key
        users_file = self.config_dir / "users.json"
        if not users_file.exists():
            return ""
        
        with open(users_file, 'r') as f:
            data = json.load(f)
        
        server_config = data.get("server", {})
        server_public_key = server_config.get("wireguard_server_public_key", "")
        
        # Find user's IP
        users = self.user_storage.load_users()
        user_list = list(users.keys())
        ip_index = user_list.index(user.username) + 2 if user.username in user_list else 2
        
        return f"""[Interface]
PrivateKey = {user.wireguard_private_key}
Address = 10.0.0.{ip_index}/32
DNS = 1.1.1.1, 8.8.8.8

[Peer]
PublicKey = {server_public_key}
Endpoint = {self.domain}:51820
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
"""
    
    def _generate_wireguard_obfs_conf(self, user: User) -> str:
        """Generate WireGuard configuration with WebSocket obfuscation."""
        # Load server public key
        users_file = self.config_dir / "users.json"
        if not users_file.exists():
            return ""
        
        with open(users_file, 'r') as f:
            data = json.load(f)
        
        server_config = data.get("server", {})
        server_public_key = server_config.get("wireguard_server_public_key", "")
        
        # Find user's IP
        users = self.user_storage.load_users()
        user_list = list(users.keys())
        ip_index = user_list.index(user.username) + 2 if user.username in user_list else 2
        
        # Get obfuscated WebSocket path
        ws_path = self.get_endpoint('wireguard_websocket', '/static/fonts/woff2/roboto-regular.woff2')
        
        return f"""# WireGuard over WebSocket (HTTPS obfuscation)
# Requires wstunnel or similar WebSocket tunnel client
# Example: wstunnel client -L 127.0.0.1:51820:127.0.0.1:51820 wss://{self.domain}{ws_path}

[Interface]
PrivateKey = {user.wireguard_private_key}
Address = 10.0.0.{ip_index}/32
DNS = 1.1.1.1, 8.8.8.8

[Peer]
PublicKey = {server_public_key}
Endpoint = 127.0.0.1:51820
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25

# Setup Instructions:
# 1. Install wstunnel: cargo install wstunnel
# 2. Run: wstunnel client -L 127.0.0.1:51820:127.0.0.1:51820 wss://{self.domain}{ws_path}
# 3. Connect WireGuard to 127.0.0.1:51820
"""
    
    def _generate_shadowtls_json(self, user: User) -> str:
        """Generate ShadowTLS v3 client configuration for Sing-box."""
        config = {
            "type": "shadowtls",
            "server": self.domain,
            "server_port": 443,
            "version": 3,
            "password": user.shadowtls_password,
            "tls": {
                "enabled": True,
                "server_name": f"api.{self.domain}",
                "insecure": False
            }
        }
        return json.dumps(config, indent=2)
    
    def _generate_hysteria2_link(self, user: User) -> str:
        """Generate Hysteria2 connection link."""
        import urllib.parse
        # Hysteria2 link format: hysteria2://password@server:port?sni=domain&obfs=salamander&obfs-password=pass
        params = {
            'sni': f"cdn.{self.domain}",
            'obfs': 'salamander',
            'obfs-password': user.hysteria2_password[:16]  # Use part of password for obfs
        }
        param_str = '&'.join([f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items()])
        return f"hysteria2://{user.hysteria2_password}@{self.domain}:443?{param_str}#{user.username}-hy2"
    
    def _generate_hysteria2_json(self, user: User) -> str:
        """Generate Hysteria2 client configuration for Sing-box."""
        config = {
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
                "password": user.hysteria2_password[:16]
            },
            "up_mbps": 100,
            "down_mbps": 100
        }
        return json.dumps(config, indent=2)
    
    def _generate_tuic_json(self, user: User) -> str:
        """Generate TUIC v5 client configuration for Sing-box."""
        config = {
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
                "alpn": ["h3", "h3-29"]
            }
        }
        return json.dumps(config, indent=2)
    
    def update_server_configs(self) -> bool:
        """Update all server configurations and reload services."""
        try:
            users = self.user_storage.load_users()
            
            # Generate and save Xray config
            xray_config = self.generate_xray_server_config(users)
            if xray_config:
                with open(self.config_dir / "xray.json", 'w') as f:
                    json.dump(xray_config, f, indent=2)
            
            # Generate and save Trojan config
            trojan_config = self.generate_trojan_server_config(users)
            if trojan_config:
                with open(self.config_dir / "trojan.json", 'w') as f:
                    json.dump(trojan_config, f, indent=2)
            
            # Generate and save Sing-box config
            singbox_config = self.generate_singbox_server_config(users)
            if singbox_config:
                with open(self.config_dir / "singbox.json", 'w') as f:
                    json.dump(singbox_config, f, indent=2)
            
            # Generate and save WireGuard config
            wg_config = self.generate_wireguard_server_config(users)
            if wg_config:
                wg_dir = self.config_dir / "wireguard"
                wg_dir.mkdir(exist_ok=True)
                with open(wg_dir / "wg0.conf", 'w') as f:
                    f.write(wg_config)
            
            return True
        except Exception as e:
            print(f"Error updating server configs: {e}")
            return False
