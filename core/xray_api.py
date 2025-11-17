"""
Xray API module for the Stealth VPN Server.
Provides high-level API for Xray user and configuration management.
"""

import json
import uuid
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from .interfaces import User
from .xray_manager import XrayConfigManager, create_xray_user_data
from .service_manager import DockerServiceManager, XrayServiceIntegration


class XrayAPI:
    """High-level API for Xray management."""
    
    def __init__(self, config_dir: str = "./data/stealth-vpn/configs", domain: str = "your-domain.com"):
        self.config_dir = Path(config_dir)
        self.domain = domain
        
        # Initialize managers
        self.xray_manager = XrayConfigManager(str(self.config_dir), domain)
        self.service_manager = DockerServiceManager()
        self.integration = XrayServiceIntegration(self.xray_manager, self.service_manager)
        
        # Users storage (in production this would be handled by UserStorageInterface)
        self.users_file = self.config_dir / "users.json"
        self._ensure_users_file()
    
    def _ensure_users_file(self):
        """Ensure users.json file exists."""
        if not self.users_file.exists():
            self.users_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.users_file, 'w') as f:
                json.dump({"users": {}, "server": {}}, f, indent=2)
    
    def _load_users(self) -> Dict[str, User]:
        """Load users from JSON file."""
        try:
            with open(self.users_file, 'r') as f:
                data = json.load(f)
            
            users = {}
            for username, user_data in data.get("users", {}).items():
                users[username] = User(**user_data)
            
            return users
        except Exception as e:
            print(f"Error loading users: {e}")
            return {}
    
    def _save_users(self, users: Dict[str, User]):
        """Save users to JSON file."""
        try:
            # Load existing data
            with open(self.users_file, 'r') as f:
                data = json.load(f)
            
            # Update users
            data["users"] = {}
            for username, user in users.items():
                data["users"][username] = {
                    "username": user.username,
                    "id": user.id,
                    "xray_uuid": user.xray_uuid,
                    "wireguard_private_key": user.wireguard_private_key,
                    "wireguard_public_key": user.wireguard_public_key,
                    "created_at": user.created_at,
                    "last_seen": user.last_seen,
                    "is_active": user.is_active
                }
            
            # Save back to file
            with open(self.users_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"Error saving users: {e}")
            raise
    
    def add_user(self, username: str) -> Tuple[bool, str, Optional[Dict[str, str]]]:
        """
        Add a new Xray user.
        
        Returns:
            (success, message, client_configs)
        """
        try:
            users = self._load_users()
            
            # Check if user already exists
            if username in users:
                return False, f"User {username} already exists", None
            
            # Create new user
            xray_data = create_xray_user_data(username)
            
            new_user = User(
                username=username,
                id=f"user-{username}-{uuid.uuid4().hex[:8]}",
                xray_uuid=xray_data["xray_uuid"],
                wireguard_private_key="",  # Will be set by WireGuard manager
                wireguard_public_key="",   # Will be set by WireGuard manager
                created_at="2025-01-01T00:00:00Z",  # In production, use datetime.now().isoformat()
                last_seen=None,
                is_active=True
            )
            
            # Add to users dict
            users[username] = new_user
            
            # Save users
            self._save_users(users)
            
            # Update server configuration and reload
            success = self.integration.update_users_and_reload(users)
            if not success:
                # Rollback user creation
                del users[username]
                self._save_users(users)
                return False, "Failed to update server configuration", None
            
            # Generate client configurations
            client_configs = self.xray_manager.generate_client_configs(username, new_user)
            
            return True, f"User {username} created successfully", client_configs
            
        except Exception as e:
            return False, f"Error creating user {username}: {e}", None
    
    def remove_user(self, username: str) -> Tuple[bool, str]:
        """
        Remove an Xray user.
        
        Returns:
            (success, message)
        """
        try:
            users = self._load_users()
            
            # Check if user exists
            if username not in users:
                return False, f"User {username} not found"
            
            # Remove user
            del users[username]
            
            # Save users
            self._save_users(users)
            
            # Update server configuration and reload
            success = self.integration.update_users_and_reload(users)
            if not success:
                return False, "Failed to update server configuration"
            
            return True, f"User {username} removed successfully"
            
        except Exception as e:
            return False, f"Error removing user {username}: {e}"
    
    def get_user(self, username: str) -> Optional[User]:
        """Get a specific user."""
        users = self._load_users()
        return users.get(username)
    
    def list_users(self) -> List[Dict[str, str]]:
        """List all users with basic information."""
        users = self._load_users()
        user_list = []
        
        for user in users.values():
            user_list.append({
                "username": user.username,
                "id": user.id,
                "created_at": user.created_at,
                "last_seen": user.last_seen or "Never",
                "is_active": "Active" if user.is_active else "Inactive"
            })
        
        return user_list
    
    def get_user_configs(self, username: str) -> Optional[Dict[str, str]]:
        """Get client configurations for a user."""
        user = self.get_user(username)
        if not user:
            return None
        
        return self.xray_manager.generate_client_configs(username, user)
    
    def toggle_user_status(self, username: str) -> Tuple[bool, str]:
        """Toggle user active/inactive status."""
        try:
            users = self._load_users()
            
            if username not in users:
                return False, f"User {username} not found"
            
            # Toggle status
            users[username].is_active = not users[username].is_active
            status = "activated" if users[username].is_active else "deactivated"
            
            # Save users
            self._save_users(users)
            
            # Update server configuration and reload
            success = self.integration.update_users_and_reload(users)
            if not success:
                return False, "Failed to update server configuration"
            
            return True, f"User {username} {status} successfully"
            
        except Exception as e:
            return False, f"Error toggling user {username}: {e}"
    
    def get_server_status(self) -> Dict[str, any]:
        """Get Xray server status and statistics."""
        try:
            users = self._load_users()
            service_status = self.service_manager.get_service_status()
            
            active_users = sum(1 for user in users.values() if user.is_active)
            total_users = len(users)
            
            return {
                "service_healthy": service_status.get("xray", False),
                "total_users": total_users,
                "active_users": active_users,
                "inactive_users": total_users - active_users,
                "domain": self.domain,
                "protocols": ["VLESS-XTLS-Vision", "VLESS-WebSocket"]
            }
            
        except Exception as e:
            return {
                "service_healthy": False,
                "error": str(e)
            }
    
    def regenerate_server_config(self) -> Tuple[bool, str]:
        """Regenerate and reload server configuration."""
        try:
            users = self._load_users()
            success = self.integration.update_users_and_reload(users)
            
            if success:
                return True, "Server configuration regenerated successfully"
            else:
                return False, "Failed to regenerate server configuration"
                
        except Exception as e:
            return False, f"Error regenerating config: {e}"