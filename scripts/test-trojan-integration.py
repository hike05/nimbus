#!/usr/bin/env python3
"""
Test script for Trojan-Go integration.
Tests configuration generation, user management, and service integration.
"""

import sys
import os
import json
import tempfile
from pathlib import Path

# Add core modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.trojan_manager import TrojanManager
from core.service_manager import DockerServiceManager, TrojanServiceIntegration
from core.interfaces import User


def create_test_user(username: str = "test_user") -> User:
    """Create a test user with Trojan password."""
    trojan_manager = TrojanManager()
    
    return User(
        username=username,
        id=f"{username}-uuid",
        xray_uuid=f"{username}-xray-uuid",
        wireguard_private_key=f"{username}-wg-private",
        wireguard_public_key=f"{username}-wg-public",
        trojan_password=trojan_manager.create_user_password(),
        created_at="2025-01-01T00:00:00Z",
        last_seen=None,
        is_active=True
    )


def test_trojan_manager():
    """Test Trojan manager functionality."""
    print("Testing Trojan Manager...")
    
    # Create temporary config directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test template
        template_path = Path(temp_dir) / "trojan.template.json"
        template_config = {
            "run_type": "server",
            "local_addr": "0.0.0.0",
            "local_port": 8002,
            "remote_addr": "caddy",
            "remote_port": 8000,
            "password": [],
            "ssl": {
                "cert": "/etc/letsencrypt/live/your-domain.com/fullchain.pem",
                "key": "/etc/letsencrypt/live/your-domain.com/privkey.pem",
                "sni": "www.your-domain.com"
            }
        }
        
        with open(template_path, 'w') as f:
            json.dump(template_config, f, indent=2)
        
        # Initialize manager with temp directory
        trojan_manager = TrojanManager(temp_dir)
        
        # Test password generation
        password = trojan_manager.create_user_password()
        assert len(password) == 32, "Password should be 32 characters"
        print("✓ Password generation works")
        
        # Test user creation and config generation
        test_user = create_test_user()
        users = {"test_user": test_user}
        
        # Test server config generation
        server_config = trojan_manager.generate_server_config(users)
        assert test_user.trojan_password in server_config["password"], "User password should be in server config"
        print("✓ Server config generation works")
        
        # Test config validation
        assert trojan_manager.validate_config(server_config), "Generated config should be valid"
        print("✓ Config validation works")
        
        # Test client config generation
        client_configs = trojan_manager.get_client_configs(test_user)
        assert "trojan_json" in client_configs, "Should generate JSON config"
        assert "trojan_url" in client_configs, "Should generate URL config"
        
        # Validate JSON config
        json_config = json.loads(client_configs["trojan_json"])
        assert test_user.trojan_password in json_config["password"], "Client config should contain user password"
        print("✓ Client config generation works")
        
        # Test URL format
        url = client_configs["trojan_url"]
        assert url.startswith("trojan://"), "URL should start with trojan://"
        assert test_user.trojan_password in url, "URL should contain password"
        print("✓ URL generation works")
        
        print("✓ All Trojan Manager tests passed")
        return True


def test_service_integration():
    """Test service integration functionality."""
    print("Testing Service Integration...")
    
    try:
        # Create managers
        service_manager = DockerServiceManager()
        
        # Test service status check (may fail if Docker not running)
        try:
            status = service_manager.get_service_status()
            print(f"Service status: {status}")
            print("✓ Service status check works")
        except Exception as e:
            print(f"⚠ Service status check failed (Docker may not be running): {e}")
        
        print("✓ Service integration tests completed")
        return True
        
    except Exception as e:
        print(f"✗ Service integration test failed: {e}")
        return False


def test_config_file_operations():
    """Test configuration file operations."""
    print("Testing Config File Operations...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test template
        template_path = Path(temp_dir) / "trojan.template.json"
        template_config = {
            "run_type": "server",
            "local_addr": "0.0.0.0",
            "local_port": 8002,
            "password": [],
            "ssl": {
                "cert": "/etc/letsencrypt/live/your-domain.com/fullchain.pem",
                "key": "/etc/letsencrypt/live/your-domain.com/privkey.pem",
                "sni": "www.your-domain.com"
            }
        }
        
        with open(template_path, 'w') as f:
            json.dump(template_config, f, indent=2)
        
        # Test config save/load
        trojan_manager = TrojanManager(temp_dir)
        test_user = create_test_user()
        users = {"test_user": test_user}
        
        # Generate and save config
        success = trojan_manager.update_server_config(users)
        assert success, "Should successfully save config"
        
        # Verify config file exists
        config_path = Path(temp_dir) / "trojan.json"
        assert config_path.exists(), "Config file should exist"
        
        # Verify config content
        with open(config_path, 'r') as f:
            saved_config = json.load(f)
        
        assert test_user.trojan_password in saved_config["password"], "Saved config should contain user password"
        print("✓ Config file operations work")
        
        return True


def main():
    """Run all tests."""
    print("Starting Trojan-Go Integration Tests...")
    print("=" * 50)
    
    tests = [
        test_trojan_manager,
        test_service_integration,
        test_config_file_operations
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
                print()
            else:
                failed += 1
                print()
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            failed += 1
            print()
    
    print("=" * 50)
    print(f"Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("✓ All tests passed!")
        return True
    else:
        print("✗ Some tests failed!")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)