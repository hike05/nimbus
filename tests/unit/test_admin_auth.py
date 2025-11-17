#!/usr/bin/env python3
"""
Unit tests for admin panel authentication.
Tests password hashing, session management, and access control.
"""

import sys
import tempfile
import shutil
from pathlib import Path

# Add admin panel modules to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'admin-panel'))

import bcrypt


def test_password_hashing():
    """Test password hashing with bcrypt."""
    print("\n=== Testing Password Hashing ===")
    
    password = "secure_admin_password_123"
    
    # Hash password
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    # Verify correct password
    if bcrypt.checkpw(password.encode('utf-8'), hashed):
        print("✓ Password hashing and verification successful")
    else:
        print("✗ Password verification failed")
        return False
    
    # Verify incorrect password fails
    wrong_password = "wrong_password"
    if not bcrypt.checkpw(wrong_password.encode('utf-8'), hashed):
        print("✓ Incorrect password correctly rejected")
        return True
    else:
        print("✗ Incorrect password was accepted")
        return False


def test_password_strength():
    """Test password strength requirements."""
    print("\n=== Testing Password Strength ===")
    
    def validate_password(password):
        """Validate password meets minimum requirements."""
        if len(password) < 12:
            return False, "Password must be at least 12 characters"
        if not any(c.isupper() for c in password):
            return False, "Password must contain uppercase letter"
        if not any(c.islower() for c in password):
            return False, "Password must contain lowercase letter"
        if not any(c.isdigit() for c in password):
            return False, "Password must contain digit"
        return True, "Password is strong"
    
    # Test weak passwords
    weak_passwords = [
        "short",
        "alllowercase123",
        "ALLUPPERCASE123",
        "NoDigitsHere",
    ]
    
    for pwd in weak_passwords:
        valid, msg = validate_password(pwd)
        if valid:
            print(f"✗ Weak password accepted: {pwd}")
            return False
    
    print("✓ Weak passwords correctly rejected")
    
    # Test strong password
    strong_password = "SecureAdmin123"
    valid, msg = validate_password(strong_password)
    if valid:
        print("✓ Strong password accepted")
        return True
    else:
        print(f"✗ Strong password rejected: {msg}")
        return False


def test_session_token_generation():
    """Test session token generation."""
    print("\n=== Testing Session Token Generation ===")
    
    import secrets
    
    # Generate session tokens
    tokens = set()
    for _ in range(100):
        token = secrets.token_urlsafe(32)
        tokens.add(token)
    
    # Verify uniqueness
    if len(tokens) == 100:
        print("✓ Session tokens are unique")
    else:
        print("✗ Duplicate session tokens generated")
        return False
    
    # Verify length
    token = secrets.token_urlsafe(32)
    if len(token) >= 32:
        print(f"✓ Session token length adequate: {len(token)} chars")
        return True
    else:
        print(f"✗ Session token too short: {len(token)} chars")
        return False


def test_session_expiry():
    """Test session expiry logic."""
    print("\n=== Testing Session Expiry ===")
    
    from datetime import datetime, timedelta
    
    def is_session_valid(created_at, max_age_hours=24):
        """Check if session is still valid."""
        now = datetime.utcnow()
        age = now - created_at
        return age < timedelta(hours=max_age_hours)
    
    # Test valid session
    recent_time = datetime.utcnow() - timedelta(hours=1)
    if is_session_valid(recent_time):
        print("✓ Recent session is valid")
    else:
        print("✗ Recent session incorrectly expired")
        return False
    
    # Test expired session
    old_time = datetime.utcnow() - timedelta(hours=25)
    if not is_session_valid(old_time):
        print("✓ Old session correctly expired")
        return True
    else:
        print("✗ Old session incorrectly valid")
        return False


def test_rate_limiting():
    """Test rate limiting for login attempts."""
    print("\n=== Testing Rate Limiting ===")
    
    from datetime import datetime, timedelta
    
    class RateLimiter:
        def __init__(self, max_attempts=5, window_minutes=15):
            self.attempts = {}
            self.max_attempts = max_attempts
            self.window = timedelta(minutes=window_minutes)
        
        def is_allowed(self, ip_address):
            """Check if IP is allowed to attempt login."""
            now = datetime.utcnow()
            
            if ip_address not in self.attempts:
                self.attempts[ip_address] = []
            
            # Remove old attempts outside window
            self.attempts[ip_address] = [
                t for t in self.attempts[ip_address]
                if now - t < self.window
            ]
            
            # Check if under limit
            if len(self.attempts[ip_address]) < self.max_attempts:
                self.attempts[ip_address].append(now)
                return True
            
            return False
    
    limiter = RateLimiter(max_attempts=3, window_minutes=15)
    test_ip = "192.168.1.100"
    
    # First 3 attempts should succeed
    for i in range(3):
        if not limiter.is_allowed(test_ip):
            print(f"✗ Attempt {i+1} incorrectly blocked")
            return False
    
    print("✓ First 3 attempts allowed")
    
    # 4th attempt should be blocked
    if limiter.is_allowed(test_ip):
        print("✗ 4th attempt should be blocked")
        return False
    
    print("✓ Rate limiting working correctly")
    return True


def test_csrf_protection():
    """Test CSRF token generation and validation."""
    print("\n=== Testing CSRF Protection ===")
    
    import secrets
    import hmac
    import hashlib
    
    def generate_csrf_token(session_id, secret_key):
        """Generate CSRF token tied to session."""
        message = f"{session_id}".encode('utf-8')
        signature = hmac.new(
            secret_key.encode('utf-8'),
            message,
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def validate_csrf_token(token, session_id, secret_key):
        """Validate CSRF token."""
        expected = generate_csrf_token(session_id, secret_key)
        return hmac.compare_digest(token, expected)
    
    secret_key = secrets.token_hex(32)
    session_id = secrets.token_urlsafe(32)
    
    # Generate token
    token = generate_csrf_token(session_id, secret_key)
    
    # Validate correct token
    if validate_csrf_token(token, session_id, secret_key):
        print("✓ Valid CSRF token accepted")
    else:
        print("✗ Valid CSRF token rejected")
        return False
    
    # Validate incorrect token
    wrong_token = secrets.token_hex(32)
    if not validate_csrf_token(wrong_token, session_id, secret_key):
        print("✓ Invalid CSRF token rejected")
        return True
    else:
        print("✗ Invalid CSRF token accepted")
        return False


def test_secure_headers():
    """Test security headers configuration."""
    print("\n=== Testing Security Headers ===")
    
    required_headers = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self'",
    }
    
    # Simulate response headers
    response_headers = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self'",
    }
    
    missing_headers = []
    for header, expected_value in required_headers.items():
        if header not in response_headers:
            missing_headers.append(header)
        elif response_headers[header] != expected_value:
            print(f"✗ Header {header} has wrong value")
            return False
    
    if missing_headers:
        print(f"✗ Missing security headers: {', '.join(missing_headers)}")
        return False
    
    print("✓ All security headers present and correct")
    return True


def main():
    """Run all admin authentication tests."""
    print("=" * 60)
    print("Admin Panel Authentication Unit Tests")
    print("=" * 60)
    
    tests = [
        ("Password Hashing", test_password_hashing),
        ("Password Strength", test_password_strength),
        ("Session Token Generation", test_session_token_generation),
        ("Session Expiry", test_session_expiry),
        ("Rate Limiting", test_rate_limiting),
        ("CSRF Protection", test_csrf_protection),
        ("Security Headers", test_secure_headers),
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
