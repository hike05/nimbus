#!/usr/bin/env python3
"""
Unit tests for configuration generation functions.
Tests Xray, Trojan, Sing-box, and WireGuard config generation.
"""

import sys
import json
import tempfile
import shutil
from pathlib import Path

# Add core modules to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'core'))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'admin-panel' / 'core'))

from xray_manager import XrayManager
from trojan_manager import TrojanManager
from singbox_manager import SingboxManager
from wireguard_manager import WireGuardManager
from interfaces import User


def create_test_user():
    """Create a test user for config generation."""
    return User(
        username="testuser",
        id="12345678-1234-1234-1234-123456789abc",
        xray_uuid="87654321-4321-4321-4321-cba987654321",
        wireguard_private_key="YAnz5TF+lXXJte14tji3zlMNftqL1kmfVW66+xhPHkY=",
        wireguard_public_key="HIgo9xNzJMWLKASShiTqIybxZ0U3wGLiUeJ1PKf8ykw=",
        trojan_password="secure_password_123456",
        created_at="2025-01-01T00:00:00Z"
    )


def test_xray_config_generation():
    """Test Xray configuration generation."""
    print("\n=== Testing Xray Config Generation ===")
    
    temp_dir = tempfile.mkdtemp()
    try:
        manager = XrayManager(config_dir=temp_dir)
        user = create_test_user()
        
        # Generate server config
        server_config = manager.generate_server_config([user])
        
        # Verify structure
        if 'inbounds' not in server_config:
            print("✗ Missing inbounds in server config")
            return False
        
        if len(server_config['inbounds']) == 0:
            print("✗ No inbound configurations")
            return False
        
        print(f"✓ Generated server config with {len(server_config['inbounds'])} inbounds")
        
        # Generate client config
        client_config = manager.generate_client_config(user, "example.com")
        
        if 'outbounds' not in client_config:
            print("✗ Missing outbounds in client config")
            return False
        
        print("✓ Generated valid client config")
        
        # Generate connection link
        link = manager.generate_connection_link(user, "example.com", "/ws-path")
        
        if not link.startswith("vless://"):
            print("✗ Invalid connection link format")
            return False
        
        print(f"✓ Generated connection link: {link[:50]}...")
        
        return True
        
    finally:
        shutil.rmtree(temp_dir)


def test_trojan_config_generation():
    """Test Trojan-Go configuration generation."""
    print("\n=== Testing Trojan Config Generation ===")
    
    temp_dir = tempfile.mkdtemp()
    try:
        manager = TrojanManager(config_dir=temp_dir)
        user = create_test_user()
        
        # Generate server config
        server_config = manager.generate_server_config([user])
        
        # Verify structure
        if 'password' not in server_config:
            print("✗ Missing password in server config")
            return False
        
        if not isinstance(server_config['password'], list):
            print("✗ Password should be a list")
            return False
        
        print("✓ Generated valid Trojan server config")
        
        # Generate client config
        client_config = manager.generate_client_config(user, "example.com")
        
        if 'remote_addr' not in client_config:
            print("✗ Missing remote_addr in client config")
            return False
        
        print("✓ Generated valid Trojan client config")
        
        # Generate connection link
        link = manager.generate_connection_link(user, "example.com")
        
        if not link.startswith("trojan://"):
            print("✗ Invalid Trojan link format")
            return False
        
        print(f"✓ Generated Trojan link: {link[:50]}...")
        
        return True
        
    finally:
        shutil.rmtree(temp_dir)


def test_singbox_config_generation():
    """Test Sing-box configuration generation."""
    print("\n=== Testing Sing-box Config Generation ===")
    
    temp_dir = tempfile.mkdtemp()
    try:
        manager = SingboxManager(config_dir=temp_dir)
        user = create_test_user()
        
        # Generate server config
        server_config = manager.generate_server_config([user])
        
        # Verify structure
        if 'inbounds' not in server_config:
            print("✗ Missing inbounds in server config")
            return False
        
        # Should have multiple protocol inbounds
        inbound_types = [ib.get('type') for ib in server_config['inbounds']]
        expected_types = ['shadowtls', 'hysteria2', 'tuic']
        
        for expected in expected_types:
            if expected not in inbound_types:
                print(f"✗ Missing {expected} inbound")
                return False
        
        print(f"✓ Generated server config with {len(inbound_types)} protocols")
        
        # Generate client configs for each protocol
        protocols = ['shadowtls', 'hysteria2', 'tuic']
        for protocol in protocols:
            client_config = manager.generate_client_config(user, "example.com", protocol)
            
            if 'outbounds' not in client_config:
                print(f"✗ Missing outbounds in {protocol} client config")
                return False
            
            print(f"✓ Generated {protocol} client config")
        
        return True
        
    finally:
        shutil.rmtree(temp_dir)


def test_wireguard_config_generation():
    """Test WireGuard configuration generation."""
    print("\n=== Testing WireGuard Config Generation ===")
    
    temp_dir = tempfile.mkdtemp()
    try:
        manager = WireGuardManager(config_dir=temp_dir)
        user = create_test_user()
        
        # Generate server config
        server_config = manager.generate_server_config([user])
        
        # Verify structure
        if '[Interface]' not in server_config:
            print("✗ Missing Interface section")
            return False
        
        if '[Peer]' not in server_config:
            print("✗ Missing Peer section")
            return False
        
        print("✓ Generated valid WireGuard server config")
        
        # Generate client config
        client_config = manager.generate_client_config(user, "example.com")
        
        if '[Interface]' not in client_config:
            print("✗ Missing Interface in client config")
            return False
        
        if 'PrivateKey' not in client_config:
            print("✗ Missing PrivateKey in client config")
            return False
        
        print("✓ Generated valid WireGuard client config")
        
        return True
        
    finally:
        shutil.rmtree(temp_dir)


def test_config_validation():
    """Test configuration validation."""
    print("\n=== Testing Config Validation ===")
    
    temp_dir = tempfile.mkdtemp()
    try:
        xray_manager = XrayManager(config_dir=temp_dir)
        user = create_test_user()
        
        # Generate config
        config = xray_manager.generate_server_config([user])
        
        # Save to file
        config_file = Path(temp_dir) / "xray.json"
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Validate JSON structure
        with open(config_file, 'r') as f:
            loaded_config = json.load(f)
        
        if loaded_config == config:
            print("✓ Config validation successful")
            return True
        else:
            print("✗ Config validation failed")
            return False
            
    finally:
        shutil.rmtree(temp_dir)


def test_multi_user_config():
    """Test configuration generation with multiple users."""
    print("\n=== Testing Multi-User Config Generation ===")
    
    temp_dir = tempfile.mkdtemp()
    try:
        manager = XrayManager(config_dir=temp_dir)
        
        # Create multiple users
        users = []
        for i in range(5):
            user = User(
                username=f"user{i}",
                id=f"12345678-1234-1234-1234-12345678{i:04d}",
                xray_uuid=f"87654321-4321-4321-4321-cba98765{i:04d}",
                wireguard_private_key="YAnz5TF+lXXJte14tji3zlMNftqL1kmfVW66+xhPHkY=",
                wireguard_public_key="HIgo9xNzJMWLKASShiTqIybxZ0U3wGLiUeJ1PKf8ykw=",
                trojan_password=f"password_{i}",
                created_at="2025-01-01T00:00:00Z"
            )
            users.append(user)
        
        # Generate server config
        config = manager.generate_server_config(users)
        
        # Verify all users are included
        if 'inbounds' not in config:
            print("✗ Missing inbounds")
            return False
        
        # Check that clients are configured
        clients_found = False
        for inbound in config['inbounds']:
            if 'settings' in inbound and 'clients' in inbound['settings']:
                if len(inbound['settings']['clients']) == len(users):
                    clients_found = True
                    break
        
        if clients_found:
            print(f"✓ Multi-user config generated for {len(users)} users")
            return True
        else:
            print("✗ Not all users included in config")
            return False
            
    finally:
        shutil.rmtree(temp_dir)


def main():
    """Run all configuration generation tests."""
    print("=" * 60)
    print("Configuration Generation Unit Tests")
    print("=" * 60)
    
    tests = [
        ("Xray Config Generation", test_xray_config_generation),
        ("Trojan Config Generation", test_trojan_config_generation),
        ("Sing-box Config Generation", test_singbox_config_generation),
        ("WireGuard Config Generation", test_wireguard_config_generation),
        ("Config Validation", test_config_validation),
        ("Multi-User Config", test_multi_user_config),
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
