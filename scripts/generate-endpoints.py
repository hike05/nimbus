#!/usr/bin/env python3
"""
Generate obfuscated endpoints for multi-protocol proxy server
This script creates realistic-looking paths for proxy services with rotation support
"""

import sys
import json
import secrets
import string
import random
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.endpoint_manager import EndpointManager

# Endpoint generation functions are now in core/endpoint_manager.py
# This script provides a CLI interface to the EndpointManager

def update_caddyfile(endpoints: Dict, caddyfile_path: str = 'config/Caddyfile') -> bool:
    """
    Update Caddyfile with new endpoints
    
    Args:
        endpoints: Dictionary of service names to endpoint paths
        caddyfile_path: Path to Caddyfile
    
    Returns:
        True if update was successful
    """
    try:
        # Backup current Caddyfile
        backup_path = f"{caddyfile_path}.backup"
        with open(caddyfile_path, 'r') as f:
            original_content = f.read()
        
        with open(backup_path, 'w') as f:
            f.write(original_content)
        
        content = original_content
        
        # Define endpoint mappings (old path -> new path)
        replacements = {
            'handle /api/v2/storage/upload {': f'handle {endpoints["admin_panel"]} {{',
            'handle /cdn/assets/js/analytics.min.js {': f'handle {endpoints["xray_websocket"]} {{',
            'handle /static/fonts/woff2/roboto-regular.woff2 {': f'handle {endpoints["wireguard_websocket"]} {{',
            'handle /api/v1/files/sync {': f'handle {endpoints["trojan_websocket"]} {{',
            'handle /api/v1/microservices/health {': f'handle {endpoints.get("health_check", "/api/v1/microservices/health")} {{',
            'handle /media/webrtc/conference/signal {': f'handle {endpoints.get("webrtc_signal", "/media/webrtc/conference/signal")} {{'
        }
        
        # Apply replacements
        replaced_count = 0
        for old_pattern, new_pattern in replacements.items():
            if old_pattern in content:
                content = content.replace(old_pattern, new_pattern)
                replaced_count += 1
        
        # Write updated content
        with open(caddyfile_path, 'w') as f:
            f.write(content)
        
        print(f"✓ Updated Caddyfile with {replaced_count} new endpoints")
        print(f"✓ Backup saved to {backup_path}")
        return True
        
    except Exception as e:
        print(f"✗ Error updating Caddyfile: {e}")
        # Restore from backup if it exists
        try:
            if Path(backup_path).exists():
                with open(backup_path, 'r') as f:
                    content = f.read()
                with open(caddyfile_path, 'w') as f:
                    f.write(content)
                print(f"✓ Restored Caddyfile from backup")
        except:
            pass
        return False

# Helper functions using EndpointManager

def get_endpoint_stats(manager: EndpointManager) -> Dict:
    """Get statistics about current endpoints"""
    endpoints = manager.load_endpoints()
    if not endpoints:
        return {}
    
    age = manager.get_endpoint_age(endpoints)
    if not age:
        return {}
    
    return {
        'age_days': age.days,
        'age_hours': age.seconds // 3600,
        'generated_at': endpoints.get('generated_at', 'unknown'),
        'version': endpoints.get('version', 'unknown'),
        'service_count': len(manager.list_services())
    }

def main():
    """Main function with command-line argument support"""
    # Parse command-line arguments
    args = sys.argv[1:]
    force_rotation = '--force' in args or '-f' in args
    show_stats = '--stats' in args or '-s' in args
    validate_only = '--validate' in args or '-v' in args
    
    print("🔧 Multi-Protocol Proxy Server - Endpoint Management")
    print("=" * 60)
    
    # Initialize endpoint manager
    manager = EndpointManager()
    
    # Load current endpoints
    current_endpoints = manager.load_endpoints()
    
    # Show stats if requested
    if show_stats:
        if current_endpoints:
            stats = get_endpoint_stats(manager)
            print("\n📊 Current Endpoint Statistics:")
            print(f"   Age: {stats.get('age_days', 0)} days, {stats.get('age_hours', 0)} hours")
            print(f"   Generated ID: {stats.get('generated_at', 'unknown')}")
            print(f"   Version: {stats.get('version', 'unknown')}")
            print(f"   Services: {stats.get('service_count', 0)}")
            
            print("\n📋 Current endpoints:")
            for service, path in current_endpoints.items():
                if service not in ['generated_at', 'timestamp', 'version']:
                    print(f"   {service:25} -> {path}")
        else:
            print("\n⚠️  No endpoints found")
        return
    
    # Validate only if requested
    if validate_only:
        if current_endpoints:
            print("\n🔍 Validating current endpoints...")
            is_valid, errors = manager.validate_endpoints(current_endpoints)
            if is_valid:
                print("✓ All endpoints are valid")
            else:
                print("✗ Endpoint validation failed:")
                for error in errors:
                    print(f"   - {error}")
                sys.exit(1)
        else:
            print("\n⚠️  No endpoints to validate")
            sys.exit(1)
        return
    
    # Check if rotation is needed
    print("\n🔍 Checking if rotation is needed...")
    if current_endpoints and not force_rotation:
        if not manager.should_rotate(current_endpoints):
            stats = get_endpoint_stats(manager)
            print(f"ℹ️  Endpoints are still fresh ({stats.get('age_days', 0)} days old)")
            print("   Use --force to rotate anyway")
            return
    
    # Rotate or generate new endpoints
    if current_endpoints:
        print("🔄 Rotating endpoints...")
        endpoints = manager.rotate_endpoints(force=force_rotation)
        if endpoints is None:
            print("ℹ️  No rotation needed")
            return
    else:
        print("🆕 Generating initial endpoints...")
        endpoints = manager.generate_endpoints()
        manager.save_endpoints(endpoints)
    
    # Validate new endpoints
    is_valid, errors = manager.validate_endpoints(endpoints)
    if not is_valid:
        print("✗ Generated endpoints failed validation:")
        for error in errors:
            print(f"   - {error}")
        sys.exit(1)
    
    print("\n📋 New endpoints:")
    for service, path in endpoints.items():
        if service not in ['generated_at', 'timestamp', 'version']:
            print(f"   {service:25} -> {path}")
    
    # Update Caddyfile
    if not update_caddyfile(endpoints):
        print("✗ Failed to update Caddyfile")
        sys.exit(1)
    
    print(f"\n🎯 Endpoint management complete!")
    print(f"   Generated ID: {endpoints['generated_at']}")
    print(f"   Timestamp: {endpoints['timestamp']}")
    print(f"   Version: {endpoints['version']}")
    
    print("\n⚠️  Next steps:")
    print("   1. Update client configurations with new endpoints")
    print("   2. Restart Caddy container: docker compose restart caddy")
    print("   3. Test all endpoints after deployment")
    print("   4. Update admin panel configuration if needed")
    
    print("\n💡 Usage:")
    print("   --stats, -s     Show current endpoint statistics")
    print("   --validate, -v  Validate current endpoints")
    print("   --force, -f     Force rotation regardless of age")

if __name__ == "__main__":
    main()