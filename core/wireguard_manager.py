"""
WireGuard configuration management module.
Handles server and client configuration generation with obfuscation support.
"""

import json
import subprocess
import secrets
import base64
from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import asdict

from core.interfaces import User, WireGuardConfig


class WireGuardManager:
    """Manages WireGuard server and client configurations with obfuscation."""
    
    def __init__(self, config_dir: Path = Path("/data/proxy/configs")):
        self.config_dir = config_dir
        self.wg_config_dir = config_dir / "wireguard"
        self.wg_config_dir.mkdir(parents=True, exist_ok=True)
        
        self.server_config_path = self.wg_config_dir / "wg0.conf"
        self.keys_dir = self.wg_config_dir / "keys"
        self.keys_dir.mkdir(parents=True, exist_ok=True)
        
        self.peer_configs_dir = self.wg_config_dir / "peer_configs"
        self.peer_configs_dir.mkdir(parents=True, exist_ok=True)
        
        # Default configuration
        self.server_address = "10.13.13.1/24"
        self.server_port = 51820
        self.dns_servers = ["1.1.1.1", "8.8.8.8"]
        self.allowed_ips = ["0.0.0.0/0", "::/0"]
    
    def generate_keypair(self) -> tuple[str, str]:
        """
        Generate WireGuard private and public key pair.
        
        Returns:
            Tuple of (private_key, public_key)
        """
        # Generate private key
        private_key = subprocess.run(
            ["wg", "genkey"],
            capture_output=True,
            text=True,
            check=True
        ).stdout.strip()
        
        # Generate public key from private key
        public_key = subprocess.run(
            ["wg", "pubkey"],
            input=private_key,
            capture_output=True,
            text=True,
            check=True
        ).stdout.strip()
        
        return private_key, public_key
    
    def get_server_keys(self) -> tuple[str, str]:
        """
        Get or generate server keys.
        
        Returns:
            Tuple of (private_key, public_key)
        """
        private_key_path = self.keys_dir / "server_private.key"
        public_key_path = self.keys_dir / "server_public.key"
        
        if private_key_path.exists() and public_key_path.exists():
            private_key = private_key_path.read_text().strip()
            public_key = public_key_path.read_text().strip()
        else:
            private_key, public_key = self.generate_keypair()
            private_key_path.write_text(private_key)
            public_key_path.write_text(public_key)
            private_key_path.chmod(0o600)
            public_key_path.chmod(0o600)
        
        return private_key, public_key
    
    def get_next_peer_ip(self, users: Dict[str, User]) -> str:
        """
        Get next available peer IP address.
        
        Args:
            users: Dictionary of existing users
            
        Returns:
            Next available IP address in the subnet
        """
        # Start from 10.13.13.2 (server is .1)
        used_ips = set()
        
        # Parse existing peer IPs from server config if it exists
        if self.server_config_path.exists():
            config_content = self.server_config_path.read_text()
            for line in config_content.split('\n'):
                if line.strip().startswith('AllowedIPs'):
                    ip = line.split('=')[1].strip().split('/')[0]
                    if ip.startswith('10.13.13.'):
                        used_ips.add(ip)
        
        # Find next available IP
        for i in range(2, 255):
            ip = f"10.13.13.{i}"
            if ip not in used_ips:
                return ip
        
        raise ValueError("No available IP addresses in subnet")
    
    def generate_server_config(self, users: Dict[str, User]) -> str:
        """
        Generate WireGuard server configuration.
        
        Args:
            users: Dictionary of users to include as peers
            
        Returns:
            WireGuard server configuration as string
        """
        server_private_key, server_public_key = self.get_server_keys()
        
        config_lines = [
            "[Interface]",
            f"Address = {self.server_address}",
            f"ListenPort = {self.server_port}",
            f"PrivateKey = {server_private_key}",
            "PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE",
            "PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE",
            ""
        ]
        
        # Add peers
        peer_ip_counter = 2
        for username, user in users.items():
            if not user.is_active:
                continue
            
            peer_ip = f"10.13.13.{peer_ip_counter}/32"
            peer_ip_counter += 1
            
            config_lines.extend([
                f"# Peer: {username}",
                "[Peer]",
                f"PublicKey = {user.wireguard_public_key}",
                f"AllowedIPs = {peer_ip}",
                ""
            ])
        
        return "\n".join(config_lines)
    
    def save_server_config(self, config: str) -> None:
        """
        Save WireGuard server configuration to file.
        
        Args:
            config: Configuration content as string
        """
        # Backup existing config
        if self.server_config_path.exists():
            backup_path = self.server_config_path.with_suffix('.conf.backup')
            self.server_config_path.rename(backup_path)
        
        # Write new config
        self.server_config_path.write_text(config)
        self.server_config_path.chmod(0o600)
    
    def generate_client_config(
        self,
        username: str,
        user: User,
        server_domain: str,
        transport_method: str = "websocket",
        websocket_port: int = 8006,
        udp2raw_port: int = 8007
    ) -> str:
        """
        Generate WireGuard client configuration file.
        
        Args:
            username: Username for the configuration
            user: User object with credentials
            server_domain: Server domain name
            transport_method: Transport method (websocket, udp2raw, native)
            websocket_port: WebSocket proxy port
            udp2raw_port: udp2raw proxy port
            
        Returns:
            WireGuard client configuration as string
        """
        server_private_key, server_public_key = self.get_server_keys()
        
        # Determine endpoint based on transport method
        if transport_method == "websocket":
            endpoint = f"{server_domain}:{websocket_port}"
            endpoint_comment = "# WebSocket over HTTPS transport"
        elif transport_method == "udp2raw":
            endpoint = f"{server_domain}:{udp2raw_port}"
            endpoint_comment = "# udp2raw TCP masking transport"
        else:  # native
            endpoint = f"{server_domain}:{self.server_port}"
            endpoint_comment = "# Native WireGuard (UDP)"
        
        # Get peer IP (find user's IP from server config or assign new)
        peer_ip = self.get_peer_ip_for_user(username)
        
        config_lines = [
            "[Interface]",
            f"PrivateKey = {user.wireguard_private_key}",
            f"Address = {peer_ip}/32",
            f"DNS = {', '.join(self.dns_servers)}",
            "",
            "[Peer]",
            f"PublicKey = {server_public_key}",
            f"Endpoint = {endpoint}",
            endpoint_comment,
            f"AllowedIPs = {', '.join(self.allowed_ips)}",
            "PersistentKeepalive = 25",
            ""
        ]
        
        return "\n".join(config_lines)
    
    def get_peer_ip_for_user(self, username: str) -> str:
        """
        Get peer IP address for a specific user.
        
        Args:
            username: Username to find IP for
            
        Returns:
            IP address for the user
        """
        if self.server_config_path.exists():
            config_content = self.server_config_path.read_text()
            lines = config_content.split('\n')
            
            for i, line in enumerate(lines):
                if line.strip() == f"# Peer: {username}":
                    # Find AllowedIPs in next few lines
                    for j in range(i, min(i + 5, len(lines))):
                        if lines[j].strip().startswith('AllowedIPs'):
                            ip = lines[j].split('=')[1].strip().split('/')[0]
                            return ip
        
        # If not found, return a default (should not happen in normal operation)
        return "10.13.13.2"
    
    def save_client_config(self, username: str, config: str, transport_method: str) -> Path:
        """
        Save client configuration to file.
        
        Args:
            username: Username for the configuration
            config: Configuration content
            transport_method: Transport method used
            
        Returns:
            Path to saved configuration file
        """
        user_config_dir = self.peer_configs_dir / username
        user_config_dir.mkdir(parents=True, exist_ok=True)
        
        config_filename = f"wg-{transport_method}.conf"
        config_path = user_config_dir / config_filename
        
        config_path.write_text(config)
        config_path.chmod(0o600)
        
        return config_path
    
    def generate_all_client_configs(
        self,
        username: str,
        user: User,
        server_domain: str
    ) -> Dict[str, str]:
        """
        Generate all client configurations for a user (all transport methods).
        
        Args:
            username: Username for configurations
            user: User object with credentials
            server_domain: Server domain name
            
        Returns:
            Dictionary mapping transport method to config content
        """
        configs = {}
        
        # Generate config for each transport method
        for method in ["websocket", "udp2raw", "native"]:
            config = self.generate_client_config(
                username=username,
                user=user,
                server_domain=server_domain,
                transport_method=method
            )
            configs[method] = config
            
            # Save to file
            self.save_client_config(username, config, method)
        
        return configs
    
    def get_obfuscation_params(self) -> Dict[str, str]:
        """
        Get obfuscation parameters for client configuration.
        
        Returns:
            Dictionary with obfuscation parameters
        """
        params = {}
        
        # Get udp2raw key if it exists
        udp2raw_key_path = self.keys_dir / "udp2raw.key"
        if udp2raw_key_path.exists():
            params['udp2raw_key'] = udp2raw_key_path.read_text().strip()
        else:
            # Generate new key
            key = base64.b64encode(secrets.token_bytes(32)).decode('utf-8')
            udp2raw_key_path.write_text(key)
            udp2raw_key_path.chmod(0o600)
            params['udp2raw_key'] = key
        
        # WebSocket path (should match Caddy configuration)
        params['websocket_path'] = '/static/fonts/woff2/roboto-regular.woff2'
        
        # TLS server name
        params['tls_server_name'] = 'your-domain.com'
        
        return params
    
    def generate_client_config_object(
        self,
        username: str,
        user: User,
        server_domain: str,
        transport_method: str = "websocket"
    ) -> WireGuardConfig:
        """
        Generate WireGuard client configuration object.
        
        Args:
            username: Username for configuration
            user: User object with credentials
            server_domain: Server domain name
            transport_method: Transport method to use
            
        Returns:
            WireGuardConfig object
        """
        obfs_params = self.get_obfuscation_params()
        
        if transport_method == "websocket":
            server_port = 8006
            websocket_path = obfs_params['websocket_path']
            tls_server_name = server_domain
        elif transport_method == "udp2raw":
            server_port = 8007
            websocket_path = None
            tls_server_name = None
        else:  # native
            server_port = self.server_port
            websocket_path = None
            tls_server_name = None
        
        server_private_key, server_public_key = self.get_server_keys()
        
        return WireGuardConfig(
            protocol="wireguard",
            server_address=server_domain,
            server_port=server_port,
            private_key=user.wireguard_private_key,
            server_public_key=server_public_key,
            allowed_ips=self.allowed_ips,
            dns_servers=self.dns_servers,
            transport_method=transport_method,
            websocket_path=websocket_path,
            tls_server_name=tls_server_name
        )
    
    def remove_peer(self, username: str) -> bool:
        """
        Remove a peer from WireGuard configuration.
        
        Args:
            username: Username to remove
            
        Returns:
            True if successful, False otherwise
        """
        if not self.server_config_path.exists():
            return False
        
        config_content = self.server_config_path.read_text()
        lines = config_content.split('\n')
        
        # Find and remove peer section
        new_lines = []
        skip_until_next_section = False
        
        for i, line in enumerate(lines):
            if line.strip() == f"# Peer: {username}":
                skip_until_next_section = True
                continue
            
            if skip_until_next_section:
                # Skip until we hit another section or end
                if line.strip().startswith('[') or line.strip().startswith('# Peer:'):
                    skip_until_next_section = False
                    new_lines.append(line)
                continue
            
            new_lines.append(line)
        
        # Save updated config
        self.server_config_path.write_text('\n'.join(new_lines))
        
        # Remove client configs
        user_config_dir = self.peer_configs_dir / username
        if user_config_dir.exists():
            import shutil
            shutil.rmtree(user_config_dir)
        
        return True
    
    def reload_wireguard(self) -> bool:
        """
        Reload WireGuard configuration without dropping connections.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Use wg syncconf for graceful reload
            subprocess.run(
                ["wg", "syncconf", "wg0", str(self.server_config_path)],
                check=True,
                capture_output=True
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"Failed to reload WireGuard: {e.stderr.decode()}")
            return False
