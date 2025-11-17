#!/usr/bin/env python3
"""
Xray API Demo Script
Demonstrates how the admin panel would interact with the Xray API.
"""

import sys
import os
import json

# Add the core module to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.xray_api import XrayAPI


def demo_user_management():
    """Demonstrate user management operations."""
    print("=== Xray API Demo: User Management ===")
    
    # Initialize API
    api = XrayAPI(
        config_dir="./data/stealth-vpn/configs",
        domain="demo.example.com"
    )
    
    print("\n1. Initial server status:")
    status = api.get_server_status()
    print(f"   Service healthy: {status['service_healthy']}")
    print(f"   Total users: {status['total_users']}")
    print(f"   Active users: {status['active_users']}")
    print(f"   Domain: {status['domain']}")
    print(f"   Protocols: {', '.join(status['protocols'])}")
    
    print("\n2. Adding users...")
    
    # Add some test users
    test_users = ["alice", "bob", "charlie"]
    
    for username in test_users:
        success, message, configs = api.add_user(username)
        if success:
            print(f"   ✓ {message}")
            if configs:
                print(f"     XTLS Link: {configs['xray_xtls_link'][:50]}...")
                print(f"     WebSocket Link: {configs['xray_ws_link'][:50]}...")
        else:
            print(f"   ❌ {message}")
    
    print("\n3. Listing users:")
    users = api.list_users()
    for user in users:
        print(f"   - {user['username']} ({user['is_active']}) - Created: {user['created_at']}")
    
    print("\n4. Getting user configurations:")
    alice_configs = api.get_user_configs("alice")
    if alice_configs:
        print("   Alice's configurations generated successfully")
        print(f"   - XTLS config: {len(alice_configs['xray_xtls_json'])} characters")
        print(f"   - WebSocket config: {len(alice_configs['xray_ws_json'])} characters")
    
    print("\n5. Toggling user status:")
    success, message = api.toggle_user_status("bob")
    print(f"   {message}")
    
    # Show updated user list
    users = api.list_users()
    bob_status = next((u['is_active'] for u in users if u['username'] == 'bob'), 'Not found')
    print(f"   Bob's status: {bob_status}")
    
    print("\n6. Final server status:")
    status = api.get_server_status()
    print(f"   Total users: {status['total_users']}")
    print(f"   Active users: {status['active_users']}")
    print(f"   Inactive users: {status['inactive_users']}")
    
    print("\n7. Removing a user:")
    success, message = api.remove_user("charlie")
    print(f"   {message}")
    
    # Final user list
    print("\n8. Final user list:")
    users = api.list_users()
    for user in users:
        print(f"   - {user['username']} ({user['is_active']})")
    
    print("\n✓ User management demo completed!")


def demo_configuration_export():
    """Demonstrate configuration export for different clients."""
    print("\n=== Xray API Demo: Configuration Export ===")
    
    api = XrayAPI(
        config_dir="./data/stealth-vpn/configs",
        domain="demo.example.com"
    )
    
    # Get alice's configurations (should exist from previous demo)
    alice_configs = api.get_user_configs("alice")
    
    if alice_configs:
        print("\n1. Exporting Alice's configurations:")
        
        # Save configurations to files for demonstration
        export_dir = "./data/stealth-vpn/configs/export/alice"
        os.makedirs(export_dir, exist_ok=True)
        
        # Save XTLS configuration
        with open(f"{export_dir}/xray-xtls.json", 'w') as f:
            f.write(alice_configs['xray_xtls_json'])
        print(f"   ✓ XTLS config saved to {export_dir}/xray-xtls.json")
        
        # Save WebSocket configuration
        with open(f"{export_dir}/xray-ws.json", 'w') as f:
            f.write(alice_configs['xray_ws_json'])
        print(f"   ✓ WebSocket config saved to {export_dir}/xray-ws.json")
        
        # Save share links
        with open(f"{export_dir}/share-links.txt", 'w') as f:
            f.write(f"XTLS-Vision Link:\n{alice_configs['xray_xtls_link']}\n\n")
            f.write(f"WebSocket Link:\n{alice_configs['xray_ws_link']}\n")
        print(f"   ✓ Share links saved to {export_dir}/share-links.txt")
        
        print("\n2. Configuration summary:")
        print(f"   - XTLS config size: {len(alice_configs['xray_xtls_json'])} bytes")
        print(f"   - WebSocket config size: {len(alice_configs['xray_ws_json'])} bytes")
        print(f"   - XTLS link length: {len(alice_configs['xray_xtls_link'])} characters")
        print(f"   - WebSocket link length: {len(alice_configs['xray_ws_link'])} characters")
        
    else:
        print("   ❌ No configurations found for Alice")
    
    print("\n✓ Configuration export demo completed!")


def demo_server_management():
    """Demonstrate server management operations."""
    print("\n=== Xray API Demo: Server Management ===")
    
    api = XrayAPI(
        config_dir="./data/stealth-vpn/configs",
        domain="demo.example.com"
    )
    
    print("\n1. Current server status:")
    status = api.get_server_status()
    for key, value in status.items():
        print(f"   {key}: {value}")
    
    print("\n2. Regenerating server configuration:")
    success, message = api.regenerate_server_config()
    print(f"   {message}")
    
    print("\n3. Server configuration file check:")
    config_file = "./data/stealth-vpn/configs/xray.json"
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        print(f"   ✓ Configuration file exists")
        print(f"   - Inbounds: {len(config.get('inbounds', []))}")
        print(f"   - Outbounds: {len(config.get('outbounds', []))}")
        
        # Count total clients across all inbounds
        total_clients = 0
        for inbound in config.get('inbounds', []):
            clients = inbound.get('settings', {}).get('clients', [])
            total_clients += len(clients)
        
        print(f"   - Total configured clients: {total_clients}")
    else:
        print("   ❌ Configuration file not found")
    
    print("\n✓ Server management demo completed!")


def main():
    """Main demo function."""
    print("Xray API Demonstration")
    print("=" * 50)
    
    try:
        # Run all demos
        demo_user_management()
        demo_configuration_export()
        demo_server_management()
        
        print("\n" + "=" * 50)
        print("🎉 Xray API demonstration completed successfully!")
        print("\nKey features demonstrated:")
        print("✓ User creation and management")
        print("✓ Configuration generation (XTLS and WebSocket)")
        print("✓ Share link generation")
        print("✓ User status toggling")
        print("✓ Configuration export")
        print("✓ Server status monitoring")
        print("✓ Server configuration regeneration")
        
        print("\nThe Xray API is ready for integration with the admin panel!")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()