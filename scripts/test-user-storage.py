#!/usr/bin/env python3
"""
Test script for user storage implementation.
Tests data models, validation, and storage operations.
"""

import sys
import tempfile
import shutil
from pathlib import Path

# Add core modules to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'core'))
sys.path.insert(0, str(Path(__file__).parent.parent / 'admin-panel' / 'core'))

from interfaces import User, ServerConfig


def test_user_validation():
    """Test User data model validation."""
    print("\n=== Testing User Validation ===")
    
    # Test valid user
    try:
        user = User(
            username="testuser",
            id="12345678-1234-1234-1234-123456789abc",
            xray_uuid="87654321-4321-4321-4321-cba987654321",
            wireguard_private_key="a" * 44,  # Base64 encoded 32 bytes
            wireguard_public_key="b" * 44,
            trojan_password="secure_password_123456",
            created_at="2025-01-01T00:00:00Z"
        )
        print("✓ Valid user created successfully")
        print(f"  - Username: {user.username}")
        print(f"  - ID: {user.id}")
    except ValueError as e:
        print(f"✗ Valid user failed: {e}")
        return False
    
    # Test invalid username (too short)
    try:
        user = User(
            username="ab",  # Too short
            id="12345678-1234-1234-1234-123456789abc",
            xray_uuid="87654321-4321-4321-4321-cba987654321",
            wireguard_private_key="a" * 44,
            wireguard_public_key="b" * 44,
            trojan_password="secure_password_123456"
        )
        print("✗ Invalid username should have failed")
        return False
    except ValueError as e:
        print(f"✓ Invalid username rejected correctly: {e}")
    
    # Test invalid UUID
    try:
        user = User(
            username="testuser",
            id="invalid-uuid",
            xray_uuid="87654321-4321-4321-4321-cba987654321",
            wireguard_private_key="a" * 44,
            wireguard_public_key="b" * 44,
            trojan_password="secure_password_123456"
        )
        print("✗ Invalid UUID should have failed")
        return False
    except ValueError as e:
        print(f"✓ Invalid UUID rejected correctly: {e}")
    
    # Test short password
    try:
        user = User(
            username="testuser",
            id="12345678-1234-1234-1234-123456789abc",
            xray_uuid="87654321-4321-4321-4321-cba987654321",
            wireguard_private_key="a" * 44,
            wireguard_public_key="b" * 44,
            trojan_password="short"  # Too short
        )
        print("✗ Short password should have failed")
        return False
    except ValueError as e:
        print(f"✓ Short password rejected correctly: {e}")
    
    return True


def test_user_serialization():
    """Test User to_dict and from_dict methods."""
    print("\n=== Testing User Serialization ===")
    
    try:
        # Create user
        user = User(
            username="testuser",
            id="12345678-1234-1234-1234-123456789abc",
            xray_uuid="87654321-4321-4321-4321-cba987654321",
            wireguard_private_key="a" * 44,
            wireguard_public_key="b" * 44,
            trojan_password="secure_password_123456",
            shadowtls_password="shadowtls_pass_123456",
            hysteria2_password="hysteria2_pass_123456",
            tuic_uuid="11111111-2222-3333-4444-555555555555",
            tuic_password="tuic_password_123456",
            created_at="2025-01-01T00:00:00Z",
            is_active=True
        )
        
        # Test to_dict
        user_dict = user.to_dict()
        print("✓ User serialized to dict")
        print(f"  - Keys: {', '.join(user_dict.keys())}")
        
        # Test from_dict
        user2 = User.from_dict(user_dict)
        print("✓ User deserialized from dict")
        
        # Verify data integrity
        if user.username == user2.username and user.id == user2.id:
            print("✓ Data integrity verified")
        else:
            print("✗ Data integrity check failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Serialization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_server_config_validation():
    """Test ServerConfig validation."""
    print("\n=== Testing ServerConfig Validation ===")
    
    try:
        # Test valid config
        config = ServerConfig(
            wireguard_server_private_key="a" * 44,
            wireguard_server_public_key="b" * 44,
            xray_private_key="c" * 44,
            admin_password_hash="$2b$12$abcdefghijklmnopqrstuvwxyz",
            session_secret="d" * 44,
            obfuscated_endpoints={
                "admin": "/api/v2/storage/upload",
                "xray_ws": "/cdn/assets/js/analytics.min.js"
            },
            created_at="2025-01-01T00:00:00Z"
        )
        print("✓ Valid ServerConfig created")
        
        # Test invalid session secret (too short)
        try:
            config = ServerConfig(
                wireguard_server_private_key="a" * 44,
                wireguard_server_public_key="b" * 44,
                xray_private_key="c" * 44,
                admin_password_hash="$2b$12$abcdefghijklmnopqrstuvwxyz",
                session_secret="short",  # Too short
                obfuscated_endpoints={}
            )
            print("✗ Short session secret should have failed")
            return False
        except ValueError as e:
            print(f"✓ Short session secret rejected: {e}")
        
        return True
        
    except Exception as e:
        print(f"✗ ServerConfig test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("User Storage Data Models and Validation Tests")
    print("=" * 60)
    
    tests = [
        ("User Validation", test_user_validation),
        ("User Serialization", test_user_serialization),
        ("ServerConfig Validation", test_server_config_validation),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
