"""
Service management for the Stealth VPN Server.
Handles service reloading, health checks, and configuration updates.
"""

import subprocess
import json
import time
from typing import Dict, List, Optional
from pathlib import Path

from .interfaces import ServiceManagerInterface


class DockerServiceManager(ServiceManagerInterface):
    """Manages Docker-based VPN services."""
    
    def __init__(self, compose_file: str = "docker-compose.yml"):
        self.compose_file = compose_file
        self.services = {
            "xray": "stealth-xray",
            "trojan": "stealth-trojan", 
            "singbox": "stealth-singbox",
            "wireguard": "stealth-wireguard",
            "caddy": "stealth-caddy",
            "admin": "stealth-admin"
        }
    
    def reload_service(self, service_name: str) -> bool:
        """Gracefully reload a VPN service."""
        try:
            container_name = self.services.get(service_name)
            if not container_name:
                print(f"Unknown service: {service_name}")
                return False
            
            # For Xray, we can send SIGUSR1 for graceful reload
            if service_name == "xray":
                result = subprocess.run([
                    "docker", "exec", container_name, "pkill", "-USR1", "xray"
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"✓ Gracefully reloaded {service_name}")
                    return True
                else:
                    # Fallback to container restart
                    print(f"Graceful reload failed, restarting {service_name} container...")
                    return self._restart_container(container_name)
            
            # For other services, restart the container
            else:
                return self._restart_container(container_name)
                
        except Exception as e:
            print(f"Error reloading {service_name}: {e}")
            return False
    
    def _restart_container(self, container_name: str) -> bool:
        """Restart a Docker container."""
        try:
            # Restart the container
            result = subprocess.run([
                "docker", "restart", container_name
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✓ Restarted container {container_name}")
                
                # Wait for container to be ready
                time.sleep(5)
                return self._wait_for_container_health(container_name)
            else:
                print(f"Failed to restart {container_name}: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"Error restarting container {container_name}: {e}")
            return False
    
    def _wait_for_container_health(self, container_name: str, timeout: int = 30) -> bool:
        """Wait for container to become healthy."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                result = subprocess.run([
                    "docker", "inspect", "--format={{.State.Health.Status}}", container_name
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    health_status = result.stdout.strip()
                    if health_status == "healthy":
                        return True
                    elif health_status == "unhealthy":
                        print(f"Container {container_name} is unhealthy")
                        return False
                
                # If no health check defined, check if container is running
                result = subprocess.run([
                    "docker", "inspect", "--format={{.State.Running}}", container_name
                ], capture_output=True, text=True)
                
                if result.returncode == 0 and result.stdout.strip() == "true":
                    return True
                
            except Exception:
                pass
            
            time.sleep(2)
        
        print(f"Timeout waiting for {container_name} to become healthy")
        return False
    
    def check_service_health(self, service_name: str) -> bool:
        """Check if a service is running and healthy."""
        try:
            container_name = self.services.get(service_name)
            if not container_name:
                return False
            
            # Check if container is running
            result = subprocess.run([
                "docker", "inspect", "--format={{.State.Running}}", container_name
            ], capture_output=True, text=True)
            
            if result.returncode != 0 or result.stdout.strip() != "true":
                return False
            
            # Check health status if available
            result = subprocess.run([
                "docker", "inspect", "--format={{.State.Health.Status}}", container_name
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                health_status = result.stdout.strip()
                return health_status in ["healthy", "<no value>"]  # <no value> means no health check
            
            return True  # Container is running, assume healthy
            
        except Exception as e:
            print(f"Error checking health of {service_name}: {e}")
            return False
    
    def get_service_status(self) -> Dict[str, bool]:
        """Get status of all VPN services."""
        status = {}
        for service_name in self.services.keys():
            status[service_name] = self.check_service_health(service_name)
        return status
    
    def update_xray_config_and_reload(self, config: Dict) -> bool:
        """Update Xray configuration and reload the service."""
        try:
            # Save the new configuration
            config_path = Path("./data/stealth-vpn/configs/xray.json")
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            print("✓ Xray configuration updated")
            
            # Reload the Xray service
            return self.reload_service("xray")
            
        except Exception as e:
            print(f"Error updating Xray config: {e}")
            return False
    
    def update_trojan_config_and_reload(self, config: Dict) -> bool:
        """Update Trojan-Go configuration and reload the service."""
        try:
            # Save the new configuration
            config_path = Path("./data/stealth-vpn/configs/trojan.json")
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            print("✓ Trojan configuration updated")
            
            # Reload the Trojan service
            return self.reload_service("trojan")
            
        except Exception as e:
            print(f"Error updating Trojan config: {e}")
            return False
    
    def update_singbox_config_and_reload(self, config: Dict) -> bool:
        """Update Sing-box configuration and reload the service."""
        try:
            # Save the new configuration
            config_path = Path("./data/stealth-vpn/configs/singbox.json")
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            print("✓ Sing-box configuration updated")
            
            # Reload the Sing-box service
            return self.reload_service("singbox")
            
        except Exception as e:
            print(f"Error updating Sing-box config: {e}")
            return False
    
    def update_wireguard_config_and_reload(self, config: str) -> bool:
        """Update WireGuard configuration and reload the service."""
        try:
            # Save the new configuration
            config_path = Path("./data/stealth-vpn/configs/wireguard/wg0.conf")
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Backup existing config
            if config_path.exists():
                backup_path = config_path.with_suffix('.conf.backup')
                config_path.rename(backup_path)
            
            # Write new config
            with open(config_path, 'w') as f:
                f.write(config)
            config_path.chmod(0o600)
            
            print("✓ WireGuard configuration updated")
            
            # Reload WireGuard using syncconf for graceful reload
            container_name = self.services.get("wireguard")
            result = subprocess.run([
                "docker", "exec", container_name, "wg", "syncconf", "wg0", "/config/wg0.conf"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✓ WireGuard configuration reloaded gracefully")
                return True
            else:
                print(f"Graceful reload failed, restarting WireGuard container...")
                return self._restart_container(container_name)
            
        except Exception as e:
            print(f"Error updating WireGuard config: {e}")
            return False
    
    def get_container_logs(self, service_name: str, lines: int = 50) -> str:
        """Get recent logs from a service container."""
        try:
            container_name = self.services.get(service_name)
            if not container_name:
                return f"Unknown service: {service_name}"
            
            result = subprocess.run([
                "docker", "logs", "--tail", str(lines), container_name
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                return result.stdout
            else:
                return f"Error getting logs: {result.stderr}"
                
        except Exception as e:
            return f"Error getting logs for {service_name}: {e}"


class XrayServiceIntegration:
    """Integration between Xray configuration and service management."""
    
    def __init__(self, xray_manager, service_manager: DockerServiceManager):
        self.xray_manager = xray_manager
        self.service_manager = service_manager
    
    def update_users_and_reload(self, users: Dict) -> bool:
        """Update Xray configuration with new users and reload service."""
        try:
            # Generate new server configuration
            server_config = self.xray_manager.generate_xray_server_config(users)
            
            # Update and reload
            return self.service_manager.update_xray_config_and_reload(server_config)
            
        except Exception as e:
            print(f"Error updating Xray users: {e}")
            return False
    
    def add_user_and_reload(self, users: Dict, new_user) -> bool:
        """Add a new user and reload Xray service."""
        users[new_user.username] = new_user
        return self.update_users_and_reload(users)
    
    def remove_user_and_reload(self, users: Dict, username: str) -> bool:
        """Remove a user and reload Xray service."""
        if username in users:
            del users[username]
            return self.update_users_and_reload(users)
        return False


class TrojanServiceIntegration:
    """Integration between Trojan-Go configuration and service management."""
    
    def __init__(self, trojan_manager, service_manager: DockerServiceManager):
        self.trojan_manager = trojan_manager
        self.service_manager = service_manager
    
    def update_users_and_reload(self, users: Dict) -> bool:
        """Update Trojan configuration with new users and reload service."""
        try:
            # Generate new server configuration
            server_config = self.trojan_manager.generate_server_config(users)
            
            # Update and reload
            return self.service_manager.update_trojan_config_and_reload(server_config)
            
        except Exception as e:
            print(f"Error updating Trojan users: {e}")
            return False
    
    def add_user_and_reload(self, users: Dict, new_user) -> bool:
        """Add a new user and reload Trojan service."""
        users[new_user.username] = new_user
        return self.update_users_and_reload(users)
    
    def remove_user_and_reload(self, users: Dict, username: str) -> bool:
        """Remove a user and reload Trojan service."""
        if username in users:
            del users[username]
            return self.update_users_and_reload(users)
        return False


class SingboxServiceIntegration:
    """Integration between Sing-box configuration and service management."""
    
    def __init__(self, singbox_manager, service_manager: DockerServiceManager):
        self.singbox_manager = singbox_manager
        self.service_manager = service_manager
    
    def update_users_and_reload(self, users: Dict) -> bool:
        """Update Sing-box configuration with new users and reload service."""
        try:
            # Generate new server configuration
            server_config = self.singbox_manager.generate_server_config(users)
            
            # Update and reload
            return self.service_manager.update_singbox_config_and_reload(server_config)
            
        except Exception as e:
            print(f"Error updating Sing-box users: {e}")
            return False
    
    def add_user_and_reload(self, users: Dict, new_user) -> bool:
        """Add a new user and reload Sing-box service."""
        users[new_user.username] = new_user
        return self.update_users_and_reload(users)
    
    def remove_user_and_reload(self, users: Dict, username: str) -> bool:
        """Remove a user and reload Sing-box service."""
        if username in users:
            del users[username]
            return self.update_users_and_reload(users)
        return False



class WireGuardServiceIntegration:
    """Integration between WireGuard configuration and service management."""
    
    def __init__(self, wireguard_manager, service_manager: DockerServiceManager):
        self.wireguard_manager = wireguard_manager
        self.service_manager = service_manager
    
    def update_users_and_reload(self, users: Dict) -> bool:
        """Update WireGuard configuration with new users and reload service."""
        try:
            # Generate new server configuration
            server_config = self.wireguard_manager.generate_server_config(users)
            
            # Update and reload
            return self.service_manager.update_wireguard_config_and_reload(server_config)
            
        except Exception as e:
            print(f"Error updating WireGuard users: {e}")
            return False
    
    def add_user_and_reload(self, users: Dict, new_user) -> bool:
        """Add a new user and reload WireGuard service."""
        users[new_user.username] = new_user
        return self.update_users_and_reload(users)
    
    def remove_user_and_reload(self, users: Dict, username: str) -> bool:
        """Remove a user and reload WireGuard service."""
        if username in users:
            del users[username]
            return self.update_users_and_reload(users)
        return False
