#!/usr/bin/env python3
"""
WireGuard Integration Test
Tests WireGuard configuration generation and management.
"""

import sys
import json
import uuid
import subprocess
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.wireguard_manager import WireGuardManager
from core.interfaces import User


# Colors for output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'


def log(message: str):
    print(f"{Colors.GREEN}[Test]{Colors.NC} {message}")


def warn(message: str):
    print(f"{Colors.YELLOW}[Test]{Colors.NC} {message}")


def error(message: str):
    print(f"{Colors.RED}[Test]{Colors.NC} {message}")


def success(message: str):
    print(f"{Colors.BLUE}[✓]{Colors.NC} {message}")


def create_test_user(username: str) -> User:
    """Create a test user with generated credentials."""
    log(f"Creating test user: {username}")
    
    # Generate WireGuard keys
    private_key = subprocess.run(
        ["wg", "genkey"],
        capture_output=True,
        text=True,
        check=True
    ).stdout.strip()
    
    public_key = subprocess.run(
        ["wg", "pubkey"],
        input=private_key,
        capture_output=True,
        text=True,
        check=True
    ).stdout.strip()
    
    user = User(
        username=username,
        id=str(uuid.uuid4()),
        xray_uuid=str(uuid.uuid4()),
        wireguard_private_key=private_key,
        wireguard_public_key=public_key,
        trojan_password=f"test-password-{username}",
        created_at=datetime.now().isoformat(),
        is_active=True
    )
    
    success(f"Test user created: {username}")
    return user


def test_server_config_generation():
    """Test server configuration generation."""
    log("Testing server configuration generation...")
    
    manager = WireGuardManager(Path("./data/stealth-vpn/configs"))
    
    # Create test users
    users = {
        'alice': create_test_user('alice'),
        'bob': create_test_user('bob')
    }
    
    # Generate server config
    config = manager.generate_server_config(users)
    
    # Validate config
    assert "[Interface]" in config, "Missing [Interface] section"
    assert "PrivateKey" in config, "Missing PrivateKey"
    assert "ListenPort" in config, "Missing ListenPort"
    assert config.count("[Peer]") == 2, f"Expected 2 peers, found {config.count('[Peer]')}"
    assert "# Peer: alice" in config, "Missing alice peer"
    assert "# Peer: bob" in config, "Missing bob peer"
    
    success("Server configuration generation passed")
    
    # Save config
    manager.save_server_config(config)
    success(f"Server configuration saved to {manager.server_config_path}")
    
    return manager, users


def test_client_config_generation(manager: WireGuardManager, users: dict):
    """Test client configuration generation."""
    log("Testing client configuration generation...")
    
    server_domain = "test.example.com"
    
    for username, user in users.items():
        log(f"Generating configs for {username}...")
        
        # Test WebSocket config
        ws_config = manager.generate_client_config(
            username=username,
            user=user,
            server_domain=server_domain,
            transport_method="websocket"
        )
        
        assert "[Interface]" in ws_config, "Missing [Interface] in WebSocket config"
        assert "[Peer]" in ws_config, "Missing [Peer] in WebSocket config"
        assert user.wireguard_private_key in ws_config, "Missing private key"
        assert "8006" in ws_config, "Missing WebSocket port"
        
        # Test udp2raw config
        udp2raw_config = manager.generate_client_config(
            username=username,
            user=user,
            server_domain=server_domain,
            transport_method="udp2raw"
        )
        
        assert "8007" in udp2raw_config, "Missing udp2raw port"
        
        # Test native config
        native_config = manager.generate_client_config(
            username=username,
            user=user,
            server_domain=server_domain,
            transport_method="native"
        )
        
        assert "51820" in native_config, "Missing native WireGuard port"
        
        success(f"Client configs generated for {username}")
    
    success("Client configuration generation passed")


def test_all_client_configs(manager: WireGuardManager, users: dict):
    """Test generating all client configs at once."""
    log("Testing all client configs generation...")
    
    server_domain = "test.example.com"
    
    for username, user in users.items():
        configs = manager.generate_all_client_configs(
            username=username,
            user=user,
            server_domain=server_domain
        )
        
        assert len(configs) == 3, f"Expected 3 configs, got {len(configs)}"
        assert "websocket" in configs, "Missing websocket config"
        assert "udp2raw" in configs, "Missing udp2raw config"
        assert "native" in configs, "Missing native config"
        
        # Verify files were created
        user_config_dir = manager.peer_configs_dir / username
        assert user_config_dir.exists(), f"Config directory not created for {username}"
        
        for method in ["websocket", "udp2raw", "native"]:
            config_file = user_config_dir / f"wg-{method}.conf"
            assert config_file.exists(), f"Config file not created: {config_file}"
        
        success(f"All configs generated and saved for {username}")
    
    success("All client configs generation passed")


def test_obfuscation_params(manager: WireGuardManager):
    """Test obfuscation parameters."""
    log("Testing obfuscation parameters...")
    
    params = manager.get_obfuscation_params()
    
    assert "udp2raw_key" in params, "Missing udp2raw_key"
    assert "websocket_path" in params, "Missing websocket_path"
    assert "tls_server_name" in params, "Missing tls_server_name"
    
    # Verify udp2raw key is valid base64
    import base64
    try:
        base64.b64decode(params["udp2raw_key"])
    except Exception:
        raise AssertionError("udp2raw_key is not valid base64")
    
    success("Obfuscation parameters passed")


def test_peer_removal(manager: WireGuardManager):
    """Test peer removal."""
    log("Testing peer removal...")
    
    # Remove bob
    result = manager.remove_peer("bob")
    assert result, "Failed to remove peer"
    
    # Verify bob is removed from config
    config_content = manager.server_config_path.read_text()
    assert "# Peer: bob" not in config_content, "Bob still in config"
    assert "# Peer: alice" in config_content, "Alice should still be in config"
    
    # Verify bob's config directory is removed
    bob_config_dir = manager.peer_configs_dir / "bob"
    assert not bob_config_dir.exists(), "Bob's config directory still exists"
    
    success("Peer removal passed")


def test_config_object_generation(manager: WireGuardManager, users: dict):
    """Test WireGuardConfig object generation."""
    log("Testing WireGuardConfig object generation...")
    
    user = users['alice']
    server_domain = "test.example.com"
    
    # Test WebSocket config object
    ws_config = manager.generate_client_config_object(
        username='alice',
        user=user,
        server_domain=server_domain,
        transport_method="websocket"
    )
    
    assert ws_config.protocol == "wireguard", "Wrong protocol"
    assert ws_config.server_address == server_domain, "Wrong server address"
    assert ws_config.server_port == 8006, "Wrong WebSocket port"
    assert ws_config.transport_method == "websocket", "Wrong transport method"
    assert ws_config.websocket_path is not None, "Missing websocket_path"
    assert ws_config.private_key == user.wireguard_private_key, "Wrong private key"
    
    success("WireGuardConfig object generation passed")


def run_all_tests():
    """Run all integration tests."""
    log("Starting WireGuard integration tests...")
    print()
    
    try:
        # Test 1: Server config generation
        manager, users = test_server_config_generation()
        print()
        
        # Test 2: Client config generation
        test_client_config_generation(manager, users)
        print()
        
        # Test 3: All client configs
        test_all_client_configs(manager, users)
        print()
        
        # Test 4: Obfuscation parameters
        test_obfuscation_params(manager)
        print()
        
        # Test 5: Config object generation
        test_config_object_generation(manager, users)
        print()
        
        # Test 6: Peer removal
        test_peer_removal(manager)
        print()
        
        success("="*60)
        success("All WireGuard integration tests passed!")
        success("="*60)
        
        return 0
        
    except AssertionError as e:
        error(f"Test failed: {e}")
        return 1
    except Exception as e:
        error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
