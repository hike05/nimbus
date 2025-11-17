#!/usr/bin/env python3
"""
Test script for admin panel core modules.
Verifies that all modules can be imported and basic functionality works.
"""

import sys
import os
from pathlib import Path

# Add core to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing module imports...")
    
    try:
        from user_storage import UserStorage
        print("✓ UserStorage imported")
    except Exception as e:
        print(f"✗ UserStorage import failed: {e}")
        return False
    
    try:
        from config_generator import ConfigGenerator
        print("✓ ConfigGenerator imported")
    except Exception as e:
        print(f"✗ ConfigGenerator import failed: {e}")
        return False
    
    try:
        from service_manager import DockerServiceManager
        print("✓ DockerServiceManager imported")
    except Exception as e:
        print(f"✗ DockerServiceManager import failed: {e}")
        return False
    
    try:
        from client_config_manager import ClientConfigManager
        print("✓ ClientConfigManager imported")
    except Exception as e:
        print(f"✗ ClientConfigManager import failed: {e}")
        return False
    
    try:
        from backup_manager import BackupManager
        print("✓ BackupManager imported")
    except Exception as e:
        print(f"✗ BackupManager import failed: {e}")
        return False
    
    return True


def test_user_storage():
    """Test UserStorage basic functionality."""
    print("\nTesting UserStorage...")
    
    try:
        # Create temp directory
        test_dir = Path("/tmp/stealth-vpn-test")
        test_dir.mkdir(parents=True, exist_ok=True)
        
        from user_storage import UserStorage
        storage = UserStorage(str(test_dir))
        
        # Test load (should be empty initially)
        users = storage.load_users()
        print(f"✓ Loaded {len(users)} users")
        
        # Test add user
        user = storage.add_user("testuser")
        print(f"✓ Created user: {user.username}")
        print(f"  - ID: {user.id}")
        print(f"  - Xray UUID: {user.xray_uuid}")
        print(f"  - Trojan Password: {user.trojan_password[:20]}...")
        
        # Test load again
        users = storage.load_users()
        assert len(users) == 1
        assert "testuser" in users
        print(f"✓ User persisted correctly")
        
        # Test remove
        success = storage.remove_user("testuser")
        assert success
        print(f"✓ User removed successfully")
        
        # Cleanup
        import shutil
        shutil.rmtree(test_dir)
        
        return True
    except Exception as e:
        print(f"✗ UserStorage test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_generator():
    """Test ConfigGenerator basic functionality."""
    print("\nTesting ConfigGenerator...")
    
    try:
        from config_generator import ConfigGenerator
        from user_storage import UserStorage
        
        # Create temp directory
        test_dir = Path("/tmp/stealth-vpn-test-config")
        test_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a test user
        storage = UserStorage(str(test_dir))
        user = storage.add_user("testuser")
        
        # Test config generation
        generator = ConfigGenerator(str(test_dir), "test.example.com")
        configs = generator.generate_client_configs("testuser", user)
        
        print(f"✓ Generated {len(configs)} configuration types")
        print(f"  - Xray XTLS link: {configs['xray_xtls_link'][:50]}...")
        print(f"  - Xray WS link: {configs['xray_ws_link'][:50]}...")
        print(f"  - Trojan link: {configs['trojan_link'][:50]}...")
        
        # Cleanup
        import shutil
        shutil.rmtree(test_dir)
        
        return True
    except Exception as e:
        print(f"✗ ConfigGenerator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 60)
    print("Admin Panel Module Tests")
    print("=" * 60)
    print()
    
    # Test imports
    if not test_imports():
        print("\n✗ Import tests failed")
        sys.exit(1)
    
    # Test user storage
    if not test_user_storage():
        print("\n✗ UserStorage tests failed")
        sys.exit(1)
    
    # Test config generator
    if not test_config_generator():
        print("\n✗ ConfigGenerator tests failed")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✓ All tests passed!")
    print("=" * 60)


if __name__ == '__main__':
    main()
