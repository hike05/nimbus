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
sys.path.insert(0, '/app/core')
sys.path.insert(0, '/app')

from core.user_storage import UserStorage
from core.interfaces import User


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
    except ValueError as e:
        print(f"✗ Valid user failed: {e}")
        return False
    
    # Test invalid username
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
    except ValueError:
        print("✓ Invalid username rejected correctly")
    
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
    except ValueError:
        print("✓ Invalid UUID rejected correctly")
    
    return True


def test_storage_operations():
    """Test storage operations with atomic writes and backups."""
    print("\n=== Testing Storage Operations ===")
    
    # Create temporary directory for testing
    temp_dir = tempfile.mkdtemp()
    try:
        storage = UserStorage(config_dir=temp_dir)
        
        # Test adding user
        print("\nTesting add_user...")
        user = storage.add_user("alice")
        print(f"✓ Created user: {user.username}")
        print(f"  - ID: {user.id}")
        print(f"  - Xray UUID: {user.xray_uuid}")
        print(f"  - Trojan password: {user.trojan_password[:20]}...")
        
        # Test loading users
        print("\nTesting load_users...")
        users = storage.load_users()
        if "alice" in users:
            print(f"✓ Loaded {len(users)} user(s)")
        else:
            print("✗ Failed to load user")
            return False
        
        # Test adding another user
        print("\nTesting multiple users...")
        storage.add_user("bob")
        users = storage.load_users()
        if len(users) == 2:
            print(f"✓ Successfully managing {len(users)} users")
        else:
            print(f"✗ Expected 2 users, got {len(users)}")
            return False
        
        # Test backup creation
        print("\nTesting backups...")
        backups = storage.list_backups()
        if len(backups) > 0:
            print(f"✓ Created {len(backups)} backup(s)")
            for backup in backups:
                print(f"  - {backup['filename']} ({backup['type']}, {backup['size']} bytes)")
        else:
            print("✗ No backups created")
            return False
        
        # Test removing user
        print("\nTesting remove_user...")
        if storage.remove_user("bob"):
            users = storage.load_users()
            if len(users) == 1 and "alice" in users:
                print("✓ Successfully removed user")
            else:
                print("✗ User removal failed")
                return False
        else:
            print("✗ Failed to remove user")
            return False
        
        # Test duplicate user prevention
        print("\nTesting duplicate prevention...")
        try:
            storage.add_user("alice")
            print("✗ Should have prevented duplicate user")
            return False
        except ValueError:
            print("✓ Duplicate user correctly prevented")
        
        return True
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)


def test_atomic_operations():
    """Test atomic write operations."""
    print("\n=== Testing Atomic Operations ===")
    
    temp_dir = tempfile.mkdtemp()
    try:
        storage = UserStorage(config_dir=temp_dir)
        
        # Add multiple users
        for i in range(5):
            storage.add_user(f"user{i}")
        
        users = storage.load_users()
        print(f"✓ Created {len(users)} users with atomic writes")
        
        # Verify data integrity
        users_file = Path(temp_dir) / "users.json"
        if users_file.exists():
            import json
            with open(users_file, 'r') as f:
                data = json.load(f)
            
            if "schema_version" in data and "users" in data:
                print("✓ Data structure is valid")
            else:
                print("✗ Data structure is invalid")
                return False
        
        return True
        
    finally:
        shutil.rmtree(temp_dir)


def main():
    """Run all tests."""
    print("=" * 60)
    print("User Storage Implementation Tests")
    print("=" * 60)
    
    tests = [
        ("User Validation", test_user_validation),
        ("Storage Operations", test_storage_operations),
        ("Atomic Operations", test_atomic_operations),
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
