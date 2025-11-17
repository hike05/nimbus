#!/usr/bin/env python3
"""
Test script for Sing-box integration with the Stealth VPN Server.
Tests configuration generation, service management, and client config creation.
"""

import json
import sys
import os
from pathlib import Path

# Add the parent directory to the path to import core modules
sys.path.append(str(Path(__file__).parent.parent))

from core.singbox_manager import SingboxManager, create_singbox_user_data
from core.service_manager import DockerServiceManager, SingboxServiceIntegration
from core.interfaces import User


def create_test_user() -> User:
    """Create a test user with all necessary credentials."""
    # Create base user
    user = User(
        username="test_singbox_user",
        id="test-uuid-singbox",
        xray_uuid="test-xray-uuid",
        wireguard_private_key="test-wg-private",
        wireguard_public_key="test-wg-public",
        trojan_password="test-trojan-password",
        created_at="2025-01-01T00:00:00Z",
        last_seen=None,
        is_active=True
    )
    
    # Add Sing-box credentials
    singbox_creds = create_singbox_user_data("test_singbox_user")
    for key, value in singbox_creds.items():
        setattr(user, key, value)
    
    return user


def test_singbox_manager():
    """Test Sing-box manager functionality."""
    print("Testing Sing-box Manager...")
    
    try:
        # Initialize manager
        manager = SingboxManager(domain="test-domain.com")
        
        # Create test user
        test_user = create_test_user()
        users = {"test_singbox_user": test_user}
        
        # Test server config generation
        print("  ✓ Testing server config generation...")
        server_config = manager.generate_server_config(users)
        
        if not server_config:
            print("  ✗ Server config generation failed")
            return False
        
        # Validate server config
        if not manager.validate_config(server_config):
            print("  ✗ Server config validation failed")
            return False
        
        print("  ✓ Server config generation and validation passed")
        
        # Test client config generation
        print("  ✓ Testing client config generation...")
        client_configs = manager.get_client_configs(test_user)
        
        expected_configs = [
            "shadowtls_json", "shadowtls_url",
            "hysteria2_json", "hysteria2_url", 
            "tuic_json", "tuic_url"
        ]
        
        for config_type in expected_configs:
            if config_type not in client_configs:
                print(f"  ✗ Missing client config: {config_type}")
                return False
            
            if not client_configs[config_type]:
                print(f"  ✗ Empty client config: {config_type}")
                return False
        
        print("  ✓ Client config generation passed")
        
        # Test individual protocol configs
        print("  ✓ Testing individual protocol configs...")
        
        # Test ShadowTLS config
        shadowtls_config = manager.generate_shadowtls_client_config(test_user)
        if shadowtls_config["type"] != "shadowtls":
            print("  ✗ ShadowTLS config type incorrect")
            return False
        
        # Test Hysteria2 config
        hysteria2_config = manager.generate_hysteria2_client_config(test_user)
        if hysteria2_config["type"] != "hysteria2":
            print("  ✗ Hysteria2 config type incorrect")
            return False
        
        # Test TUIC config
        tuic_config = manager.generate_tuic_client_config(test_user)
        if tuic_config["type"] != "tuic":
            print("  ✗ TUIC config type incorrect")
            return False
        
        print("  ✓ Individual protocol configs passed")
        
        print("✓ Sing-box Manager tests passed")
        return True
        
    except Exception as e:
        print(f"✗ Sing-box Manager test failed: {e}")
        return False


def test_service_integration():
    """Test Sing-box service integration."""
    print("Testing Sing-box Service Integration...")
    
    try:
        # Initialize managers
        singbox_manager = SingboxManager(domain="test-domain.com")
        service_manager = DockerServiceManager()
        integration = SingboxServiceIntegration(singbox_manager, service_manager)
        
        # Create test user
        test_user = create_test_user()
        users = {"test_singbox_user": test_user}
        
        # Test service status check (this will fail if Docker isn't running, but that's OK)
        print("  ✓ Testing service status check...")
        status = service_manager.check_service_health("singbox")
        print(f"  - Sing-box service status: {'healthy' if status else 'not running'}")
        
        # Test configuration update (without actual reload)
        print("  ✓ Testing configuration update...")
        server_config = singbox_manager.generate_server_config(users)
        
        # Save config to test file instead of actual config
        test_config_path = Path("./test_singbox_config.json")
        try:
            with open(test_config_path, 'w') as f:
                json.dump(server_config, f, indent=2)
            print("  ✓ Configuration save test passed")
            
            # Clean up test file
            test_config_path.unlink()
            
        except Exception as e:
            print(f"  ✗ Configuration save test failed: {e}")
            return False
        
        print("✓ Sing-box Service Integration tests passed")
        return True
        
    except Exception as e:
        print(f"✗ Sing-box Service Integration test failed: {e}")
        return False


def test_client_config_formats():
    """Test client configuration formats for all protocols."""
    print("Testing Client Configuration Formats...")
    
    try:
        manager = SingboxManager(domain="test-domain.com")
        test_user = create_test_user()
        
        protocols = ["shadowtls", "hysteria2", "tuic"]
        
        for protocol in protocols:
            print(f"  ✓ Testing {protocol} client config...")
            
            # Test JSON config
            try:
                json_config = manager.generate_client_config_json(test_user, protocol)
                config_data = json.loads(json_config)
                
                # Validate basic structure
                if "inbounds" not in config_data or "outbounds" not in config_data:
                    print(f"  ✗ {protocol} JSON config missing required sections")
                    return False
                
                print(f"  ✓ {protocol} JSON config valid")
                
            except Exception as e:
                print(f"  ✗ {protocol} JSON config failed: {e}")
                return False
            
            # Test URL format
            try:
                url_config = manager.generate_client_url(test_user, protocol)
                
                if not url_config.startswith(f"{protocol}://"):
                    print(f"  ✗ {protocol} URL format incorrect")
                    return False
                
                print(f"  ✓ {protocol} URL config valid")
                
            except Exception as e:
                print(f"  ✗ {protocol} URL config failed: {e}")
                return False
        
        print("✓ Client Configuration Format tests passed")
        return True
        
    except Exception as e:
        print(f"✗ Client Configuration Format test failed: {e}")
        return False


def test_credential_generation():
    """Test credential generation for Sing-box protocols."""
    print("Testing Credential Generation...")
    
    try:
        manager = SingboxManager()
        
        # Test password generation
        password = manager.generate_password(32)
        if len(password) != 32:
            print("  ✗ Password generation length incorrect")
            return False
        
        # Test UUID generation
        uuid_val = manager.generate_uuid()
        if len(uuid_val) != 36 or uuid_val.count('-') != 4:
            print("  ✗ UUID generation format incorrect")
            return False
        
        # Test Shadowsocks key generation
        ss_key = manager.generate_shadowsocks_key()
        if not ss_key or len(ss_key) < 40:  # Base64 encoded 32 bytes should be longer
            print("  ✗ Shadowsocks key generation failed")
            return False
        
        # Test complete credential set
        credentials = manager.create_user_credentials()
        expected_keys = ["shadowtls_password", "shadowsocks_password", "hysteria2_password", "tuic_uuid", "tuic_password"]
        
        for key in expected_keys:
            if key not in credentials or not credentials[key]:
                print(f"  ✗ Missing credential: {key}")
                return False
        
        print("✓ Credential Generation tests passed")
        return True
        
    except Exception as e:
        print(f"✗ Credential Generation test failed: {e}")
        return False


def main():
    """Run all Sing-box integration tests."""
    print("Starting Sing-box Integration Tests...\n")
    
    tests = [
        test_credential_generation,
        test_singbox_manager,
        test_client_config_formats,
        test_service_integration
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")
            failed += 1
        print()  # Add spacing between tests
    
    print(f"Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All Sing-box integration tests passed!")
        return True
    else:
        print("❌ Some tests failed. Check the output above for details.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)