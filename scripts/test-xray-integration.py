#!/usr/bin/env python3
"""
Xray Integration Test Script
Tests the complete Xray configuration generation and service management.
"""

import sys
import os
import json
from pathlib import Path

# Add the core module to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.interfaces import User
from core.xray_manager import XrayConfigManager, create_xray_user_data
from core.service_manager import DockerServiceManager, XrayServiceIntegration


def create_test_users() -> dict:
    """Create test users for integration testing."""
    users = {}
    
    for username in ["alice", "bob", "charlie"]:
        xray_data = create_xray_user_data(username)
        
        user = User(
            username=username,
            id=f"user-{username}",
            xray_uuid=xray_data["xray_uuid"],
            wireguard_private_key="test-wg-private-key",
            wireguard_public_key="test-wg-public-key",
            created_at="2025-01-01T00:00:00Z",
            last_seen=None,
            is_active=True
        )
        users[username] = user
    
    return users


def test_configuration_generation():
    """Test Xray configuration generation."""
    print("=== Testing Xray Configuration Generation ===")
    
    users = create_test_users()
    xray_manager = XrayConfigManager(
        config_dir="./data/stealth-vpn/configs",
        domain="test-domain.com"
    )
    
    # Test server config generation
    print("\n1. Testing server configuration generation...")
    server_config = xray_manager.generate_xray_server_config(users)
    
    # Validate server config structure
    assert "inbounds" in server_config, "Server config missing inbounds"
    assert len(server_config["inbounds"]) >= 2, "Server config should have at least 2 inbounds"
    
    # Check XTLS inbound
    xtls_inbound = next((ib for ib in server_config["inbounds"] if ib.get("tag") == "vless-xtls-vision"), None)
    assert xtls_inbound is not None, "XTLS-Vision inbound not found"
    assert len(xtls_inbound["settings"]["clients"]) == 3, "XTLS inbound should have 3 clients"
    
    # Check WebSocket inbound
    ws_inbound = next((ib for ib in server_config["inbounds"] if ib.get("tag") == "vless-ws"), None)
    assert ws_inbound is not None, "WebSocket inbound not found"
    assert len(ws_inbound["settings"]["clients"]) == 3, "WebSocket inbound should have 3 clients"
    
    print("✓ Server configuration generation passed")
    
    # Test client config generation
    print("\n2. Testing client configuration generation...")
    for username, user in users.items():
        client_configs = xray_manager.generate_client_configs(username, user)
        
        # Validate client configs
        assert "xray_xtls_json" in client_configs, f"Missing XTLS config for {username}"
        assert "xray_ws_json" in client_configs, f"Missing WebSocket config for {username}"
        assert "xray_xtls_link" in client_configs, f"Missing XTLS link for {username}"
        assert "xray_ws_link" in client_configs, f"Missing WebSocket link for {username}"
        
        # Validate XTLS link format
        xtls_link = client_configs["xray_xtls_link"]
        assert xtls_link.startswith("vless://"), f"Invalid XTLS link format for {username}"
        assert "xtls-rprx-vision" in xtls_link, f"XTLS link missing flow for {username}"
        
        # Validate WebSocket link format
        ws_link = client_configs["xray_ws_link"]
        assert ws_link.startswith("vless://"), f"Invalid WebSocket link format for {username}"
        assert "type=ws" in ws_link, f"WebSocket link missing type for {username}"
        
        print(f"✓ Client configs for {username} validated")
    
    print("✓ Client configuration generation passed")
    
    # Save configurations for further testing
    xray_manager.save_server_config(server_config)
    print("✓ Server configuration saved")
    
    return users, xray_manager


def test_service_management():
    """Test service management functionality."""
    print("\n=== Testing Service Management ===")
    
    service_manager = DockerServiceManager()
    
    # Test service status checking
    print("\n1. Testing service status checking...")
    status = service_manager.get_service_status()
    
    for service, is_healthy in status.items():
        print(f"  {service}: {'✓ Healthy' if is_healthy else '❌ Unhealthy'}")
    
    print("✓ Service status checking completed")
    
    return service_manager


def test_integration():
    """Test full integration between configuration and service management."""
    print("\n=== Testing Full Integration ===")
    
    users, xray_manager = test_configuration_generation()
    service_manager = test_service_management()
    
    # Create integration instance
    integration = XrayServiceIntegration(xray_manager, service_manager)
    
    print("\n1. Testing user addition simulation...")
    
    # Simulate adding a new user
    new_user_data = create_xray_user_data("david")
    new_user = User(
        username="david",
        id="user-david",
        xray_uuid=new_user_data["xray_uuid"],
        wireguard_private_key="test-wg-private-key",
        wireguard_public_key="test-wg-public-key",
        created_at="2025-01-01T00:00:00Z",
        last_seen=None,
        is_active=True
    )
    
    # Test configuration update (without actual service reload in test)
    updated_config = xray_manager.generate_xray_server_config({**users, "david": new_user})
    
    # Validate the updated configuration
    xtls_inbound = next((ib for ib in updated_config["inbounds"] if ib.get("tag") == "vless-xtls-vision"), None)
    assert len(xtls_inbound["settings"]["clients"]) == 4, "Updated config should have 4 clients"
    
    print("✓ User addition simulation passed")
    
    print("\n2. Testing user removal simulation...")
    
    # Simulate removing a user
    remaining_users = {k: v for k, v in users.items() if k != "alice"}
    updated_config = xray_manager.generate_xray_server_config(remaining_users)
    
    # Validate the updated configuration
    xtls_inbound = next((ib for ib in updated_config["inbounds"] if ib.get("tag") == "vless-xtls-vision"), None)
    assert len(xtls_inbound["settings"]["clients"]) == 2, "Updated config should have 2 clients"
    
    # Ensure alice's UUID is not in the config
    client_ids = [client["id"] for client in xtls_inbound["settings"]["clients"]]
    assert users["alice"].xray_uuid not in client_ids, "Removed user should not be in config"
    
    print("✓ User removal simulation passed")
    
    print("✓ Full integration testing completed")


def test_configuration_validation():
    """Test configuration validation and error handling."""
    print("\n=== Testing Configuration Validation ===")
    
    # Test with empty users
    print("\n1. Testing empty user list...")
    xray_manager = XrayConfigManager(
        config_dir="./data/stealth-vpn/configs",
        domain="test-domain.com"
    )
    
    empty_config = xray_manager.generate_xray_server_config({})
    
    # Should still have valid structure but no clients
    xtls_inbound = next((ib for ib in empty_config["inbounds"] if ib.get("tag") == "vless-xtls-vision"), None)
    assert xtls_inbound is not None, "XTLS inbound should exist even with no users"
    assert len(xtls_inbound["settings"]["clients"]) == 0, "Should have no clients"
    
    print("✓ Empty user list handling passed")
    
    # Test with inactive users
    print("\n2. Testing inactive user filtering...")
    users = create_test_users()
    users["alice"].is_active = False  # Deactivate alice
    
    filtered_config = xray_manager.generate_xray_server_config(users)
    xtls_inbound = next((ib for ib in filtered_config["inbounds"] if ib.get("tag") == "vless-xtls-vision"), None)
    
    # Should only have 2 active users (bob and charlie)
    assert len(xtls_inbound["settings"]["clients"]) == 2, "Should filter out inactive users"
    
    # Ensure alice's UUID is not in the config
    client_ids = [client["id"] for client in xtls_inbound["settings"]["clients"]]
    assert users["alice"].xray_uuid not in client_ids, "Inactive user should not be in config"
    
    print("✓ Inactive user filtering passed")
    
    print("✓ Configuration validation testing completed")


def main():
    """Main test function."""
    print("Starting Xray Integration Tests...")
    print("=" * 50)
    
    try:
        # Run all tests
        test_configuration_generation()
        test_service_management()
        test_integration()
        test_configuration_validation()
        
        print("\n" + "=" * 50)
        print("🎉 All Xray integration tests passed!")
        print("✓ Configuration generation working")
        print("✓ Service management ready")
        print("✓ User management integration working")
        print("✓ Configuration validation working")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()