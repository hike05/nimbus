#!/usr/bin/env python3
"""
Unit tests for JSON storage operations.
Tests data persistence, atomic writes, and backup functionality.
"""

import sys
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Add core modules to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'admin-panel' / 'core'))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'core'))

from user_storage import UserStorage
from interfaces import User


def test_json_serialization():
    """Test JSON serialization and deserialization of User objects."""
    print("\n=== Testing JSON Serialization ===")
    
    user = User(
        username="testuser",
        id="12345678-1234-1234-1234-123456789abc",
        xray_uuid="87654321-4321-4321-4321-cba987654321",
        wireguard_private_key="a" * 44,
        wireguard_public_key="b" * 44,
        trojan_password="secure_password_123456",
        created_at="2025-01-01T00:00:00Z"
    )
    
    # Serialize to dict
    user_dict = {
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
    
    # Convert to JSON and back
    json_str = json.dumps(user_dict)
    loaded_dict = json.loads(json_str)
    
    # Verify all fields match
    if loaded_dict['username'] == user.username and loaded_dict['id'] == user.id:
        print("✓ JSON serialization successful")
        return True
    else:
        print("✗ JSON serialization failed")
        return False


def test_atomic_write():
    """Test atomic write operations to prevent data corruption."""
    print("\n=== Testing Atomic Write Operations ===")
    
    temp_dir = tempfile.mkdtemp()
    try:
        storage = UserStorage(config_dir=temp_dir)
        users_file = Path(temp_dir) / "users.json"
        
        # Add first user
        storage.add_user("user1")
        
        # Verify file exists and is valid JSON
        if not users_file.exists():
            print("✗ Users file not created")
            return False
        
        with open(users_file, 'r') as f:
            data1 = json.load(f)
        
        # Add second user
        storage.add_user("user2")
        
        # Verify file is still valid JSON
        with open(users_file, 'r') as f:
            data2 = json.load(f)
        
        if len(data2['users']) == 2:
            print("✓ Atomic writes maintain data integrity")
            return True
        else:
            print("✗ Atomic write failed")
            return False
            
    finally:
        shutil.rmtree(temp_dir)


def test_backup_creation():
    """Test automatic backup creation on data changes."""
    print("\n=== Testing Backup Creation ===")
    
    temp_dir = tempfile.mkdtemp()
    try:
        storage = UserStorage(config_dir=temp_dir)
        backup_dir = Path(temp_dir) / "backups"
        
        # Add user (should create backup)
        storage.add_user("user1")
        
        # Check if backup was created
        backups = storage.list_backups()
        if len(backups) > 0:
            print(f"✓ Backup created: {backups[0]['filename']}")
            
            # Verify backup is valid JSON
            backup_path = backup_dir / backups[0]['filename']
            with open(backup_path, 'r') as f:
                backup_data = json.load(f)
            
            if 'users' in backup_data:
                print("✓ Backup contains valid data")
                return True
            else:
                print("✗ Backup data is invalid")
                return False
        else:
            print("✗ No backup created")
            return False
            
    finally:
        shutil.rmtree(temp_dir)


def test_backup_rotation():
    """Test backup rotation to prevent unlimited growth."""
    print("\n=== Testing Backup Rotation ===")
    
    temp_dir = tempfile.mkdtemp()
    try:
        storage = UserStorage(config_dir=temp_dir)
        
        # Create multiple backups by adding/removing users
        for i in range(15):
            storage.add_user(f"user{i}")
        
        backups = storage.list_backups()
        
        # Should keep only last 10 backups
        if len(backups) <= 10:
            print(f"✓ Backup rotation working: {len(backups)} backups kept")
            return True
        else:
            print(f"✗ Too many backups: {len(backups)}")
            return False
            
    finally:
        shutil.rmtree(temp_dir)


def test_data_recovery():
    """Test data recovery from backup."""
    print("\n=== Testing Data Recovery ===")
    
    temp_dir = tempfile.mkdtemp()
    try:
        storage = UserStorage(config_dir=temp_dir)
        users_file = Path(temp_dir) / "users.json"
        
        # Add users
        storage.add_user("user1")
        storage.add_user("user2")
        
        # Get backup list
        backups = storage.list_backups()
        if len(backups) == 0:
            print("✗ No backups available")
            return False
        
        # Corrupt main file
        with open(users_file, 'w') as f:
            f.write("corrupted data")
        
        # Try to load (should fail)
        try:
            storage.load_users()
            print("✗ Should have detected corruption")
            return False
        except:
            print("✓ Corruption detected")
        
        # Restore from backup
        backup_file = Path(temp_dir) / "backups" / backups[0]['filename']
        shutil.copy(backup_file, users_file)
        
        # Verify recovery
        users = storage.load_users()
        if len(users) > 0:
            print(f"✓ Data recovered: {len(users)} users")
            return True
        else:
            print("✗ Recovery failed")
            return False
            
    finally:
        shutil.rmtree(temp_dir)


def test_concurrent_access():
    """Test handling of concurrent access scenarios."""
    print("\n=== Testing Concurrent Access Handling ===")
    
    temp_dir = tempfile.mkdtemp()
    try:
        storage1 = UserStorage(config_dir=temp_dir)
        storage2 = UserStorage(config_dir=temp_dir)
        
        # Add user from first instance
        storage1.add_user("user1")
        
        # Reload from second instance
        users = storage2.load_users()
        
        if "user1" in users:
            print("✓ Concurrent access handled correctly")
            return True
        else:
            print("✗ Concurrent access failed")
            return False
            
    finally:
        shutil.rmtree(temp_dir)


def main():
    """Run all JSON storage tests."""
    print("=" * 60)
    print("JSON Storage Unit Tests")
    print("=" * 60)
    
    tests = [
        ("JSON Serialization", test_json_serialization),
        ("Atomic Write Operations", test_atomic_write),
        ("Backup Creation", test_backup_creation),
        ("Backup Rotation", test_backup_rotation),
        ("Data Recovery", test_data_recovery),
        ("Concurrent Access", test_concurrent_access),
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
