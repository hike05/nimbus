#!/usr/bin/env python3
"""
Xray Configuration Manager Script
Utility for testing and managing Xray configurations.
"""

import sys
import json
import os
from pathlib import Path

# Add the core module to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.interfaces import User
from core.xray_manager import XrayConfigManager, create_xray_user_data


def create_test_user(username: str) -> User:
    """Create a test user with Xray credentials."""
    xray_data = create_xray_user_data(username)
    
    return User(
        username=username,
        id=f"user-{username}",
        xray_uuid=xray_data["xray_uuid"],
        wireguard_private_key="test-wg-private-key",
        wireguard_public_key="test-wg-public-key",
        created_at="2025-01-01T00:00:00Z",
        last_seen=None,
        is_active=True
    )


def test_xray_config_generation():
    """Test Xray configuration generation."""
    print("Testing Xray Configuration Generation...")
    
    # Create test users
    users = {
        "alice": create_test_user("alice"),
        "bob": create_test_user("bob")
    }
    
    # Initialize Xray manager
    config_manager = XrayConfigManager(
        config_dir="./data/proxy/configs",
        domain="example.com"
    )
    
    # Generate server configuration
    print("\n1. Generating server configuration...")
    server_config = config_manager.generate_xray_server_config(users)
    
    # Save server config
    config_manager.save_server_config(server_config)
    print("✓ Server configuration saved to xray.json")
    
    # Generate client configurations
    print("\n2. Generating client configurations...")
    for username, user in users.items():
        client_configs = config_manager.generate_client_configs(username, user)
        
        print(f"\n--- Client configs for {username} ---")
        print(f"XTLS Link: {client_configs['xray_xtls_link']}")
        print(f"WebSocket Link: {client_configs['xray_ws_link']}")
        
        # Save client configs to files
        config_dir = Path(f"./data/proxy/configs/clients/{username}")
        config_dir.mkdir(parents=True, exist_ok=True)
        
        with open(config_dir / "xray-xtls.json", 'w') as f:
            f.write(client_configs['xray_xtls_json'])
        
        with open(config_dir / "xray-ws.json", 'w') as f:
            f.write(client_configs['xray_ws_json'])
        
        with open(config_dir / "xray-links.txt", 'w') as f:
            f.write(f"XTLS-Vision: {client_configs['xray_xtls_link']}\n")
            f.write(f"WebSocket: {client_configs['xray_ws_link']}\n")
        
        print(f"✓ Client configs saved to ./data/proxy/configs/clients/{username}/")
    
    print("\n✓ All configurations generated successfully!")


def validate_xray_config():
    """Validate the generated Xray configuration."""
    print("Validating Xray configuration...")
    
    config_path = Path("./data/proxy/configs/xray.json")
    if not config_path.exists():
        print("❌ xray.json not found. Run test generation first.")
        return False
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Basic validation
        required_keys = ["log", "inbounds", "outbounds", "routing"]
        for key in required_keys:
            if key not in config:
                print(f"❌ Missing required key: {key}")
                return False
        
        # Validate inbounds
        if len(config["inbounds"]) < 2:
            print("❌ Expected at least 2 inbounds (XTLS and WebSocket)")
            return False
        
        # Check for XTLS-Vision inbound
        xtls_found = False
        ws_found = False
        
        for inbound in config["inbounds"]:
            if inbound.get("tag") == "vless-xtls-vision":
                xtls_found = True
                if inbound.get("streamSettings", {}).get("security") != "xtls":
                    print("❌ XTLS inbound missing XTLS security")
                    return False
            elif inbound.get("tag") == "vless-ws":
                ws_found = True
                if inbound.get("streamSettings", {}).get("network") != "ws":
                    print("❌ WebSocket inbound missing WS network")
                    return False
        
        if not xtls_found:
            print("❌ XTLS-Vision inbound not found")
            return False
        
        if not ws_found:
            print("❌ WebSocket inbound not found")
            return False
        
        print("✓ Xray configuration is valid!")
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in xray.json: {e}")
        return False
    except Exception as e:
        print(f"❌ Error validating config: {e}")
        return False


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python3 xray-config-manager.py <command>")
        print("Commands:")
        print("  test     - Generate test configurations")
        print("  validate - Validate existing configuration")
        return
    
    command = sys.argv[1]
    
    if command == "test":
        test_xray_config_generation()
    elif command == "validate":
        validate_xray_config()
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()