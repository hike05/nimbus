"""
Service management for Docker-based VPN services.
Handles service reloading and health checks.
"""

import subprocess
import time
from typing import Dict

import sys
sys.path.insert(0, '/app/core')
from interfaces import ServiceManagerInterface


class DockerServiceManager(ServiceManagerInterface):
    """Manages Docker-based VPN services."""
    
    def __init__(self):
        self.services = {
            "xray": "stealth-xray",
            "trojan": "stealth-trojan",
            "singbox": "stealth-singbox",
            "wireguard": "stealth-wireguard",
            "caddy": "stealth-caddy"
        }
    
    def reload_service(self, service_name: str) -> bool:
        """Gracefully reload a VPN service."""
        try:
            container_name = self.services.get(service_name)
            if not container_name:
                return False
            
            # For Xray, send SIGUSR1 for graceful reload
            if service_name == "xray":
                result = subprocess.run(
                    ["docker", "exec", container_name, "pkill", "-USR1", "xray"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    return True
            
            # For other services, restart container
            result = subprocess.run(
                ["docker", "restart", container_name],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                time.sleep(3)
                return True
            
            return False
        except Exception as e:
            print(f"Error reloading {service_name}: {e}")
            return False
    
    def check_service_health(self, service_name: str) -> bool:
        """Check if a service is running and healthy."""
        try:
            container_name = self.services.get(service_name)
            if not container_name:
                return False
            
            result = subprocess.run(
                ["docker", "inspect", "--format={{.State.Running}}", container_name],
                capture_output=True,
                text=True
            )
            
            return result.returncode == 0 and result.stdout.strip() == "true"
        except Exception as e:
            print(f"Error checking {service_name} health: {e}")
            return False
    
    def get_service_status(self) -> Dict[str, bool]:
        """Get status of all VPN services."""
        status = {}
        for service_name in self.services.keys():
            status[service_name] = self.check_service_health(service_name)
        return status
    
    def stop_service(self, service_name: str) -> bool:
        """Stop a VPN service."""
        try:
            container_name = self.services.get(service_name)
            if not container_name:
                return False
            
            result = subprocess.run(
                ["docker", "stop", container_name],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print(f"Stopped service: {service_name}")
                return True
            else:
                print(f"Failed to stop {service_name}: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            print(f"Timeout stopping {service_name}")
            return False
        except Exception as e:
            print(f"Error stopping {service_name}: {e}")
            return False
    
    def start_service(self, service_name: str) -> bool:
        """Start a VPN service."""
        try:
            container_name = self.services.get(service_name)
            if not container_name:
                return False
            
            result = subprocess.run(
                ["docker", "start", container_name],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Wait a bit for service to initialize
                time.sleep(3)
                
                # Verify it's actually running
                if self.check_service_health(service_name):
                    print(f"Started service: {service_name}")
                    return True
                else:
                    print(f"Service {service_name} started but not healthy")
                    return False
            else:
                print(f"Failed to start {service_name}: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            print(f"Timeout starting {service_name}")
            return False
        except Exception as e:
            print(f"Error starting {service_name}: {e}")
            return False
