#!/usr/bin/env python3
"""
First User Creation Script for Multi-Protocol Proxy Server.
Generates initial admin user with all protocol credentials.
"""

import sys
import json
import uuid
import secrets
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any


def generate_wireguard_keypair() -> tuple[str, str]:
    """
    Generate WireGuard private and public key pair.
    
    Returns:
        Tuple of (private_key, public_key)
    """
    try:
        # Generate private key
        result = subprocess.run(
            ["wg", "genkey"],
            capture_output=True,
            text=True,
            check=True
        )
        private_key = result.stdout.strip()
        
        # Generate public key from private key
        result = subprocess.run(
            ["wg", "pubkey"],
            input=private_key,
            capture_output=True,
            text=True,
            check=True
        )
        public_key = result.stdout.strip()
        
        return private_key, public_key
    except subprocess.CalledProcessError as e:
        print(f"Error generating WireGuard keys: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("Error: 'wg' command not found. Please install wireguard-tools.", file=sys.stderr)
        sys.exit(1)


def create_first_user(username: str, config_dir: str) -> Dict[str, Any]:
    """
    Create the first user with all protocol credentials.
    
    Args:
        username: Username for the first user
        config_dir: Path to configuration directory
    
    Returns:
        Dictionary containing user credentials
    """
    # Generate all credentials
    user_id = str(uuid.uuid4())
    xray_uuid = str(uuid.uuid4())
    wg_private_key, wg_public_key = generate_wireguard_keypair()
    trojan_password = secrets.token_urlsafe(32)
    shadowtls_password = secrets.token_urlsafe(32)
    shadowsocks_password = secrets.token_urlsafe(32)
    hysteria2_password = secrets.token_urlsafe(32)
    tuic_uuid = str(uuid.uuid4())
    tuic_password = secrets.token_urlsafe(32)
    created_at = datetime.utcnow().isoformat() + "Z"
    
    # Create user object
    user_data = {
        "id": user_id,
        "xray_uuid": xray_uuid,
        "wireguard_private_key": wg_private_key,
        "wireguard_public_key": wg_public_key,
        "trojan_password": trojan_password,
        "shadowtls_password": shadowtls_password,
        "shadowsocks_password": shadowsocks_password,
        "hysteria2_password": hysteria2_password,
        "tuic_uuid": tuic_uuid,
        "tuic_password": tuic_password,
        "created_at": created_at,
        "last_seen": None,
        "is_active": True
    }
    
    # Prepare users.json structure
    users_data = {
        "schema_version": 1,
        "users": {
            username: user_data
        },
        "server": {
            "created_at": created_at
        },
        "last_modified": created_at
    }
    
    # Ensure config directory exists
    config_path = Path(config_dir)
    config_path.mkdir(parents=True, exist_ok=True)
    
    # Save to users.json
    users_file = config_path / "users.json"
    with open(users_file, 'w') as f:
        json.dump(users_data, f, indent=2, sort_keys=True)
    
    # Set secure file permissions (owner read/write only)
    users_file.chmod(0o600)
    
    # Return credentials for display
    return {
        "username": username,
        "user_id": user_id,
        "xray_uuid": xray_uuid,
        "wireguard_private_key": wg_private_key,
        "wireguard_public_key": wg_public_key,
        "trojan_password": trojan_password,
        "shadowtls_password": shadowtls_password,
        "shadowsocks_password": shadowsocks_password,
        "hysteria2_password": hysteria2_password,
        "tuic_uuid": tuic_uuid,
        "tuic_password": tuic_password,
        "created_at": created_at
    }


def main():
    """Main entry point for first user creation."""
    if len(sys.argv) < 2:
        print("Usage: create-first-user.py <username> [config_dir]", file=sys.stderr)
        print("Example: create-first-user.py admin /data/proxy/configs", file=sys.stderr)
        sys.exit(1)
    
    username = sys.argv[1]
    config_dir = sys.argv[2] if len(sys.argv) > 2 else "/data/proxy/configs"
    
    # Validate username
    if not username or len(username) < 3 or len(username) > 32:
        print("Error: Username must be 3-32 characters", file=sys.stderr)
        sys.exit(1)
    
    # Check if users.json already exists
    users_file = Path(config_dir) / "users.json"
    if users_file.exists():
        print(f"Warning: {users_file} already exists. First user may already be created.", file=sys.stderr)
        # Load existing file to check
        try:
            with open(users_file, 'r') as f:
                data = json.load(f)
                if data.get("users"):
                    print(f"Error: Users already exist in {users_file}. Aborting.", file=sys.stderr)
                    sys.exit(1)
        except Exception as e:
            print(f"Warning: Could not read existing users file: {e}", file=sys.stderr)
    
    try:
        # Create first user
        credentials = create_first_user(username, config_dir)
        
        # Output credentials as JSON for easy parsing
        print(json.dumps(credentials, indent=2))
        
    except Exception as e:
        print(f"Error creating first user: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
