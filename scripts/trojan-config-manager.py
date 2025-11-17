#!/usr/bin/env python3
"""
Trojan-Go Configuration Manager
Manages Trojan server configurations and user authentication.
"""

import json
import sys
import os
from pathlib import Path

# Add core modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.trojan_manager import TrojanManager
from core.interfaces import User


def load_users_from_json(users_file: str = "data/stealth-vpn/configs/users.json") -> dict:
    """Load users from JSON file."""
    try:
        with open(users_file, 'r') as f:
            data = json.load(f)
        return data.get('users', {})
    except FileNotFoundError:
        print(f"Users file not found: {users_file}")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error parsing users JSON: {e}")
        return {}


def save_users_to_json(users_data: dict, users_file: str = "data/stealth-vpn/configs/users.json"):
    """Save users to JSON file."""
    try:
        # Load existing data
        existing_data = {"users": {}, "server": {}}
        if os.path.exists(users_file):
            with open(users_file, 'r') as f:
                existing_data = json.load(f)
        
        # Update users section
        existing_data["users"] = users_data
        
        # Save back to file
        with open(users_file, 'w') as f:
            json.dump(existing_data, f, indent=2)
        
        print(f"Users saved to {users_file}")
    except Exception as e:
        print(f"Error saving users: {e}")


def convert_json_to_user_objects(users_data: dict) -> dict:
    """Convert JSON user data to User objects."""
    users = {}
    for username, user_data in users_data.items():
        # Add trojan_password if missing
        if 'trojan_password' not in user_data:
            trojan_manager = TrojanManager()
            user_data['trojan_password'] = trojan_manager.create_user_password()
        
        users[username] = User(
            username=user_data.get('username', username),
            id=user_data.get('id', ''),
            xray_uuid=user_data.get('xray_uuid', ''),
            wireguard_private_key=user_data.get('wireguard_private_key', ''),
            wireguard_public_key=user_data.get('wireguard_public_key', ''),
            trojan_password=user_data.get('trojan_password', ''),
            created_at=user_data.get('created_at', ''),
            last_seen=user_data.get('last_seen'),
            is_active=user_data.get('is_active', True)
        )
    return users


def convert_user_objects_to_json(users: dict) -> dict:
    """Convert User objects to JSON-serializable format."""
    users_data = {}
    for username, user in users.items():
        users_data[username] = {
            'username': user.username,
            'id': user.id,
            'xray_uuid': user.xray_uuid,
            'wireguard_private_key': user.wireguard_private_key,
            'wireguard_public_key': user.wireguard_public_key,
            'trojan_password': user.trojan_password,
            'created_at': user.created_at,
            'last_seen': user.last_seen,
            'is_active': user.is_active
        }
    return users_data


def generate_trojan_config():
    """Generate Trojan server configuration from current users."""
    print("Generating Trojan-Go server configuration...")
    
    # Load users
    users_data = load_users_from_json()
    users = convert_json_to_user_objects(users_data)
    
    # Initialize Trojan manager
    trojan_manager = TrojanManager()
    
    # Generate and save server config
    if trojan_manager.update_server_config(users):
        print("Trojan server configuration updated successfully")
        
        # Save updated users (with new trojan passwords if added)
        updated_users_data = convert_user_objects_to_json(users)
        save_users_to_json(updated_users_data)
        
        return True
    else:
        print("Failed to update Trojan server configuration")
        return False


def generate_client_config(username: str):
    """Generate Trojan client configuration for a specific user."""
    print(f"Generating Trojan client configuration for user: {username}")
    
    # Load users
    users_data = load_users_from_json()
    users = convert_json_to_user_objects(users_data)
    
    if username not in users:
        print(f"User '{username}' not found")
        return False
    
    user = users[username]
    trojan_manager = TrojanManager()
    
    # Generate client configs
    client_configs = trojan_manager.get_client_configs(user)
    
    # Save client configs to files
    client_dir = Path(f"data/stealth-vpn/configs/clients/{username}")
    client_dir.mkdir(parents=True, exist_ok=True)
    
    # Save JSON config
    json_file = client_dir / "trojan.json"
    with open(json_file, 'w') as f:
        f.write(client_configs["trojan_json"])
    
    # Save URL config
    url_file = client_dir / "trojan-url.txt"
    with open(url_file, 'w') as f:
        f.write(client_configs["trojan_url"])
    
    print(f"Trojan client configurations saved to {client_dir}")
    print(f"JSON config: {json_file}")
    print(f"URL config: {url_file}")
    
    return True


def add_user_trojan_password(username: str):
    """Add Trojan password to existing user."""
    print(f"Adding Trojan password for user: {username}")
    
    # Load users
    users_data = load_users_from_json()
    
    if username not in users_data:
        print(f"User '{username}' not found")
        return False
    
    # Generate Trojan password
    trojan_manager = TrojanManager()
    trojan_password = trojan_manager.create_user_password()
    
    # Update user data
    users_data[username]['trojan_password'] = trojan_password
    
    # Save updated users
    save_users_to_json(users_data)
    
    print(f"Trojan password added for user '{username}': {trojan_password}")
    return True


def test_trojan_config():
    """Test Trojan configuration generation."""
    print("Testing Trojan configuration generation...")
    
    trojan_manager = TrojanManager()
    if trojan_manager.test_config_generation():
        print("Trojan configuration test passed")
        return True
    else:
        print("Trojan configuration test failed")
        return False


def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python trojan-config-manager.py generate-server")
        print("  python trojan-config-manager.py generate-client <username>")
        print("  python trojan-config-manager.py add-password <username>")
        print("  python trojan-config-manager.py test")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "generate-server":
        success = generate_trojan_config()
        sys.exit(0 if success else 1)
    
    elif command == "generate-client":
        if len(sys.argv) < 3:
            print("Error: Username required for generate-client command")
            sys.exit(1)
        username = sys.argv[2]
        success = generate_client_config(username)
        sys.exit(0 if success else 1)
    
    elif command == "add-password":
        if len(sys.argv) < 3:
            print("Error: Username required for add-password command")
            sys.exit(1)
        username = sys.argv[2]
        success = add_user_trojan_password(username)
        sys.exit(0 if success else 1)
    
    elif command == "test":
        success = test_trojan_config()
        sys.exit(0 if success else 1)
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()