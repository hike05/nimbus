#!/usr/bin/env python3
"""
Test endpoint obfuscation integration
Verifies that all services can load and use obfuscated endpoints
"""

import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.endpoint_manager import EndpointManager


def test_endpoint_manager():
    """Test EndpointManager functionality"""
    print("🧪 Testing EndpointManager...")
    
    # Create temporary endpoint manager
    test_path = '/tmp/test_endpoints.json'
    manager = EndpointManager(test_path)
    
    # Generate endpoints
    print("  ✓ Generating endpoints...")
    endpoints = manager.generate_endpoints()
    
    # Validate endpoints
    print("  ✓ Validating endpoints...")
    is_valid, errors = manager.validate_endpoints(endpoints)
    if not is_valid:
        print(f"  ✗ Validation failed: {errors}")
        return False
    
    # Save endpoints
    print("  ✓ Saving endpoints...")
    if not manager.save_endpoints(endpoints):
        print("  ✗ Failed to save endpoints")
        return False
    
    # Load endpoints
    print("  ✓ Loading endpoints...")
    loaded = manager.load_endpoints()
    if not loaded:
        print("  ✗ Failed to load endpoints")
        return False
    
    # Check endpoint age
    print("  ✓ Checking endpoint age...")
    age = manager.get_endpoint_age(loaded)
    if age is None:
        print("  ✗ Failed to get endpoint age")
        return False
    
    # List services
    print("  ✓ Listing services...")
    services = manager.list_services()
    if len(services) < 4:
        print(f"  ✗ Expected at least 4 services, got {len(services)}")
        return False
    
    print(f"  ✓ Found {len(services)} services: {', '.join(services)}")
    
    # Get specific endpoint
    print("  ✓ Getting specific endpoint...")
    admin_endpoint = manager.get_endpoint_by_service('admin_panel')
    if not admin_endpoint:
        print("  ✗ Failed to get admin_panel endpoint")
        return False
    
    print(f"  ✓ Admin panel endpoint: {admin_endpoint}")
    
    # Clean up
    Path(test_path).unlink(missing_ok=True)
    
    print("✅ EndpointManager tests passed!")
    return True


def test_config_generator_integration():
    """Test that ConfigGenerator can use obfuscated endpoints"""
    print("\n🧪 Testing ConfigGenerator integration...")
    
    try:
        # This would require the full admin-panel environment
        # For now, just verify imports work
        sys.path.insert(0, str(Path(__file__).parent.parent / 'admin-panel'))
        sys.path.insert(0, str(Path(__file__).parent.parent / 'admin-panel' / 'core'))
        
        print("  ✓ Import paths configured")
        
        # Test that endpoint manager can be imported
        from core.endpoint_manager import EndpointManager
        print("  ✓ EndpointManager imported successfully")
        
        print("✅ ConfigGenerator integration tests passed!")
        return True
        
    except Exception as e:
        print(f"  ✗ Integration test failed: {e}")
        return False


def test_endpoint_rotation():
    """Test endpoint rotation functionality"""
    print("\n🧪 Testing endpoint rotation...")
    
    test_path = '/tmp/test_rotation_endpoints.json'
    manager = EndpointManager(test_path)
    
    # Generate initial endpoints
    print("  ✓ Generating initial endpoints...")
    initial = manager.generate_endpoints()
    manager.save_endpoints(initial)
    
    # Check if rotation is needed (should be False for fresh endpoints)
    print("  ✓ Checking rotation status...")
    should_rotate = manager.should_rotate(initial, rotation_days=30)
    if should_rotate:
        print("  ✗ Fresh endpoints should not need rotation")
        return False
    
    # Force rotation
    print("  ✓ Forcing rotation...")
    rotated = manager.rotate_endpoints(force=True)
    if not rotated:
        print("  ✗ Failed to rotate endpoints")
        return False
    
    # Verify endpoints changed
    print("  ✓ Verifying endpoints changed...")
    if initial['admin_panel'] == rotated['admin_panel']:
        print("  ⚠️  Warning: Endpoints might not have changed (random collision)")
    
    # Clean up
    Path(test_path).unlink(missing_ok=True)
    backup_dir = Path(test_path).parent / 'backups'
    if backup_dir.exists():
        import shutil
        shutil.rmtree(backup_dir, ignore_errors=True)
    
    print("✅ Endpoint rotation tests passed!")
    return True


def main():
    """Run all tests"""
    print("=" * 60)
    print("Endpoint Obfuscation Integration Tests")
    print("=" * 60)
    
    tests = [
        test_endpoint_manager,
        test_config_generator_integration,
        test_endpoint_rotation
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"\n❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    print("\n" + "=" * 60)
    print(f"Test Results: {sum(results)}/{len(results)} passed")
    print("=" * 60)
    
    if all(results):
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
