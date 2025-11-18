#!/usr/bin/env python3
"""
WireGuard Configuration Manager
Manages WireGuard server and client configurations with obfuscation support.
"""

import sys
import json
import argparse
from pathlib import Path

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
    NC = '\033[0m'  # No Color


def log(message: str):
    print(f"{Colors.GREEN}[WireGuard]{Colors.NC} {message}")


def warn(message: str):
    print(f"{Colors.YELLOW}[WireGuard]{Colors.NC} {message}")


def error(message: str):
    print(f"{Colors.RED}[WireGuard]{Colors.NC} {message}")


def load_users() -> dict:
    """Load users from JSON file."""
    users_file = Path("./data/proxy/configs/users.json")
    
    if not users_file.exists():
        return {}
    
    try:
        with open(users_file, 'r') as f:
            data = json.load(f)
            return data.get('users', {})
    except Exception as e:
        error(f"Failed to load users: {e}")
        return {}


def create_user_objects(users_data: dict) -> dict:
    """Convert user data to User objects."""
    users = {}
    for username, user_data in users_data.items():
        users[username] = User(
            username=username,
            id=user_data.get('id', ''),
            xray_uuid=user_data.get('xray_uuid', ''),
            wireguard_private_key=user_data.get('wireguard_private_key', ''),
            wireguard_public_key=user_data.get('wireguard_public_key', ''),
            trojan_password=user_data.get('trojan_password', ''),
            shadowtls_password=user_data.get('shadowtls_password'),
            shadowsocks_password=user_data.get('shadowsocks_password'),
            hysteria2_password=user_data.get('hysteria2_password'),
            tuic_uuid=user_data.get('tuic_uuid'),
            tuic_password=user_data.get('tuic_password'),
            created_at=user_data.get('created_at', ''),
            last_seen=user_data.get('last_seen'),
            is_active=user_data.get('is_active', True)
        )
    return users


def generate_server_config(args):
    """Generate WireGuard server configuration."""
    log("Generating WireGuard server configuration...")
    
    manager = WireGuardManager()
    users_data = load_users()
    users = create_user_objects(users_data)
    
    log(f"Found {len(users)} users")
    
    # Generate server config
    config = manager.generate_server_config(users)
    
    # Save config
    manager.save_server_config(config)
    
    log(f"Server configuration saved to {manager.server_config_path}")
    
    if args.show:
        print("\n" + "="*60)
        print(config)
        print("="*60 + "\n")


def generate_client_config(args):
    """Generate client configuration for a specific user."""
    if not args.username:
        error("Username is required for client config generation")
        sys.exit(1)
    
    log(f"Generating client configuration for user: {args.username}")
    
    manager = WireGuardManager()
    users_data = load_users()
    
    if args.username not in users_data:
        error(f"User '{args.username}' not found")
        sys.exit(1)
    
    users = create_user_objects(users_data)
    user = users[args.username]
    
    # Get server domain from environment or use default
    server_domain = args.domain or "your-domain.com"
    
    # Generate configs for all transport methods
    configs = manager.generate_all_client_configs(
        username=args.username,
        user=user,
        server_domain=server_domain
    )
    
    log(f"Generated {len(configs)} client configurations")
    
    for method, config in configs.items():
        config_path = manager.peer_configs_dir / args.username / f"wg-{method}.conf"
        log(f"  - {method}: {config_path}")
        
        if args.show:
            print(f"\n{'='*60}")
            print(f"WireGuard Client Config - {method.upper()}")
            print('='*60)
            print(config)
            print('='*60 + "\n")


def test_config(args):
    """Test WireGuard configuration."""
    log("Testing WireGuard configuration...")
    
    manager = WireGuardManager()
    
    # Check if server config exists
    if not manager.server_config_path.exists():
        error("Server configuration not found")
        sys.exit(1)
    
    log(f"Server config: {manager.server_config_path}")
    
    # Check if keys exist
    server_private_key, server_public_key = manager.get_server_keys()
    log(f"Server public key: {server_public_key}")
    
    # Load and validate config
    try:
        config_content = manager.server_config_path.read_text()
        
        # Basic validation
        if "[Interface]" not in config_content:
            error("Invalid config: missing [Interface] section")
            sys.exit(1)
        
        if "PrivateKey" not in config_content:
            error("Invalid config: missing PrivateKey")
            sys.exit(1)
        
        # Count peers
        peer_count = config_content.count("[Peer]")
        log(f"Configuration has {peer_count} peers")
        
        log("Configuration validation passed")
        
        if args.show:
            print("\n" + "="*60)
            print(config_content)
            print("="*60 + "\n")
        
    except Exception as e:
        error(f"Configuration validation failed: {e}")
        sys.exit(1)


def list_peers(args):
    """List all WireGuard peers."""
    log("Listing WireGuard peers...")
    
    manager = WireGuardManager()
    
    if not manager.server_config_path.exists():
        warn("Server configuration not found")
        return
    
    config_content = manager.server_config_path.read_text()
    lines = config_content.split('\n')
    
    peers = []
    current_peer = None
    
    for line in lines:
        line = line.strip()
        
        if line.startswith('# Peer:'):
            current_peer = {'username': line.split(':', 1)[1].strip()}
        elif line.startswith('PublicKey') and current_peer:
            current_peer['public_key'] = line.split('=', 1)[1].strip()
        elif line.startswith('AllowedIPs') and current_peer:
            current_peer['allowed_ips'] = line.split('=', 1)[1].strip()
            peers.append(current_peer)
            current_peer = None
    
    if not peers:
        log("No peers configured")
        return
    
    log(f"Found {len(peers)} peers:")
    print()
    for peer in peers:
        print(f"  Username: {peer['username']}")
        print(f"  Public Key: {peer['public_key']}")
        print(f"  Allowed IPs: {peer['allowed_ips']}")
        print()


def show_obfuscation_params(args):
    """Show obfuscation parameters."""
    log("WireGuard Obfuscation Parameters:")
    
    manager = WireGuardManager()
    params = manager.get_obfuscation_params()
    
    print()
    print(f"  WebSocket Path: {params.get('websocket_path', 'N/A')}")
    print(f"  TLS Server Name: {params.get('tls_server_name', 'N/A')}")
    print(f"  udp2raw Key: {params.get('udp2raw_key', 'N/A')}")
    print()
    print("Transport Methods:")
    print("  - websocket: WireGuard over WebSocket (HTTPS)")
    print("  - udp2raw: WireGuard over TCP with masking")
    print("  - native: Direct WireGuard (UDP, no obfuscation)")
    print()


def main():
    parser = argparse.ArgumentParser(
        description='WireGuard Configuration Manager',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Generate server config
    server_parser = subparsers.add_parser('server', help='Generate server configuration')
    server_parser.add_argument('--show', action='store_true', help='Show generated config')
    
    # Generate client config
    client_parser = subparsers.add_parser('client', help='Generate client configuration')
    client_parser.add_argument('--username', '-u', required=True, help='Username')
    client_parser.add_argument('--domain', '-d', help='Server domain name')
    client_parser.add_argument('--show', action='store_true', help='Show generated configs')
    
    # Test config
    test_parser = subparsers.add_parser('test', help='Test configuration')
    test_parser.add_argument('--show', action='store_true', help='Show configuration')
    
    # List peers
    list_parser = subparsers.add_parser('list', help='List all peers')
    
    # Show obfuscation params
    obfs_parser = subparsers.add_parser('obfuscation', help='Show obfuscation parameters')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.command == 'server':
            generate_server_config(args)
        elif args.command == 'client':
            generate_client_config(args)
        elif args.command == 'test':
            test_config(args)
        elif args.command == 'list':
            list_peers(args)
        elif args.command == 'obfuscation':
            show_obfuscation_params(args)
    except KeyboardInterrupt:
        print("\nOperation cancelled")
        sys.exit(1)
    except Exception as e:
        error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
