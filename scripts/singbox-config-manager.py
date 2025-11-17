#!/usr/bin/env python3
"""
Sing-box Configuration Manager
Manages ShadowTLS v3, Hysteria 2, and TUIC v5 configurations for the Stealth VPN Server.
"""

import json
import sys
import os
from pathlib import Path

# Add the parent directory to the path to import core modules
sys.path.append(str(Path(__file__).parent.parent))

from core.singbox_manager import SingboxManager, create_singbox_user_data
from core.interfaces import User


def load_users(config_dir: str = "data/stealth-vpn/configs") -> dict:
    """Load users from the JSON file."""
    users_file = Path(config_dir) / "users.json"
    
    if not users_file.exists():
        print(f"Users file not found: {users_file}")
        return {}
    
    try:
        with open(users_file, 'r') as f:
            data = json.load(f)
            return data.get("users", {})
    except Exception as e:
        print(f"Error loading users: {e}")
        return {}


def save_users(users_data: dict, config_dir: str = "data/stealth-vpn/configs") -> bool:
    """Save users to the JSON file."""
    users_file = Path(config_dir) / "users.json"
    
    try:
        # Load existing data
        existing_data = {}
        if users_file.exists():
            with open(users_file, 'r') as f:
                existing_data = json.load(f)
        
        # Update users section
        existing_data["users"] = users_data
        
        # Create backup
        if users_file.exists():
            backup_file = users_file.with_suffix('.json.backup')
            users_file.rename(backup_file)
        
        # Save updated data
        with open(users_file, 'w') as f:
            json.dump(existing_data, f, indent=2)
        
        return True
    except Exception as e:
        print(f"Error saving users: {e}")
        return False


def create_user_objects(users_data: dict) -> dict:
    """Convert user data dict to User objects."""
    users = {}
    
    for username, user_data in users_data.items():
        user = User(
            username=username,
            id=user_data.get("id", ""),
            xray_uuid=user_data.get("xray_uuid", ""),
            wireguard_private_key=user_data.get("wireguard_private_key", ""),
            wireguard_public_key=user_data.get("wireguard_public_key", ""),
            trojan_password=user_data.get("trojan_password", ""),
            shadowtls_password=user_data.get("shadowtls_password"),
            shadowsocks_password=user_data.get("shadowsocks_password"),
            hysteria2_password=user_data.get("hysteria2_password"),
            tuic_uuid=user_data.get("tuic_uuid"),
            tuic_password=user_data.get("tuic_password"),
            created_at=user_data.get("created_at", ""),
            last_seen=user_data.get("last_seen"),
            is_active=user_data.get("is_active", True)
        )
        users[username] = user
    
    return users


def add_singbox_credentials_to_user(username: str, config_dir: str = "data/stealth-vpn/configs") -> bool:
    """Add Sing-box credentials to an existing user."""
    users_data = load_users(config_dir)
    
    if username not in users_data:
        print(f"User {username} not found")
        return False
    
    # Generate Sing-box credentials
    singbox_creds = create_singbox_user_data(username)
    
    # Add credentials to user data
    users_data[username].update(singbox_creds)
    
    # Save updated users
    if save_users(users_data, config_dir):
        print(f"Added Sing-box credentials to user {username}")
        return True
    else:
        print(f"Failed to save Sing-box credentials for user {username}")
        return False


def generate_server_config(domain: str = "your-domain.com", config_dir: str = "data/stealth-vpn/configs") -> bool:
    """Generate Sing-box server configuration."""
    try:
        # Load users
        users_data = load_users(config_dir)
        users = create_user_objects(users_data)
        
        # Initialize Sing-box manager
        manager = SingboxManager(config_dir, domain)
        
        # Generate server configuration
        server_config = manager.generate_server_config(users)
        
        # Save configuration
        if manager.save_server_config(server_config):
            print("Sing-box server configuration generated successfully")
            return True
        else:
            print("Failed to save Sing-box server configuration")
            return False
            
    except Exception as e:
        print(f"Error generating Sing-box server config: {e}")
        return False


def generate_client_configs(username: str, domain: str = "your-domain.com", config_dir: str = "data/stealth-vpn/configs") -> bool:
    """Generate client configurations for a specific user."""
    try:
        # Load users
        users_data = load_users(config_dir)
        
        if username not in users_data:
            print(f"User {username} not found")
            return False
        
        # Create user object
        users = create_user_objects(users_data)
        user = users[username]
        
        # Initialize Sing-box manager
        manager = SingboxManager(config_dir, domain)
        
        # Generate client configurations
        client_configs = manager.get_client_configs(user)
        
        # Create client configs directory
        client_dir = Path(config_dir) / "clients" / username
        client_dir.mkdir(parents=True, exist_ok=True)
        
        # Save client configurations
        for config_type, config_content in client_configs.items():
            if config_type.endswith("_json"):
                filename = f"singbox-{config_type.replace('_json', '')}.json"
                with open(client_dir / filename, 'w') as f:
                    f.write(config_content)
            elif config_type.endswith("_url"):
                filename = f"singbox-{config_type.replace('_url', '')}-link.txt"
                with open(client_dir / filename, 'w') as f:
                    f.write(config_content)
        
        print(f"Client configurations generated for {username}")
        return True
        
    except Exception as e:
        print(f"Error generating client configs for {username}: {e}")
        return False


def test_configuration() -> bool:
    """Test Sing-box configuration generation."""
    try:
        manager = SingboxManager()
        return manager.test_config_generation()
    except Exception as e:
        print(f"Configuration test failed: {e}")
        return False


def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python singbox-config-manager.py generate-server [domain] [config_dir]")
        print("  python singbox-config-manager.py generate-client <username> [domain] [config_dir]")
        print("  python singbox-config-manager.py add-credentials <username> [config_dir]")
        print("  python singbox-config-manager.py test")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "generate-server":
        domain = sys.argv[2] if len(sys.argv) > 2 else "your-domain.com"
        config_dir = sys.argv[3] if len(sys.argv) > 3 else "data/stealth-vpn/configs"
        
        if generate_server_config(domain, config_dir):
            print("Server configuration generated successfully")
        else:
            print("Failed to generate server configuration")
            sys.exit(1)
    
    elif command == "generate-client":
        if len(sys.argv) < 3:
            print("Username required for generate-client command")
            sys.exit(1)
        
        username = sys.argv[2]
        domain = sys.argv[3] if len(sys.argv) > 3 else "your-domain.com"
        config_dir = sys.argv[4] if len(sys.argv) > 4 else "data/stealth-vpn/configs"
        
        if generate_client_configs(username, domain, config_dir):
            print(f"Client configurations generated for {username}")
        else:
            print(f"Failed to generate client configurations for {username}")
            sys.exit(1)
    
    elif command == "add-credentials":
        if len(sys.argv) < 3:
            print("Username required for add-credentials command")
            sys.exit(1)
        
        username = sys.argv[2]
        config_dir = sys.argv[3] if len(sys.argv) > 3 else "data/stealth-vpn/configs"
        
        if add_singbox_credentials_to_user(username, config_dir):
            print(f"Sing-box credentials added to {username}")
        else:
            print(f"Failed to add Sing-box credentials to {username}")
            sys.exit(1)
    
    elif command == "test":
        if test_configuration():
            print("Configuration test passed")
        else:
            print("Configuration test failed")
            sys.exit(1)
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()