#!/usr/bin/env python3
"""
Setup script for admin panel.
Generates bcrypt password hash for admin user.
"""

import bcrypt
import secrets
import sys


def generate_password_hash(password: str) -> str:
    """Generate bcrypt hash for password."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def generate_session_secret() -> str:
    """Generate random session secret."""
    return secrets.token_hex(32)


def main():
    print("=" * 60)
    print("Multi-Protocol Proxy Server - Admin Panel Setup")
    print("=" * 60)
    print()
    
    # Get admin password
    if len(sys.argv) > 1:
        password = sys.argv[1]
    else:
        password = input("Enter admin password: ")
    
    if not password:
        print("Error: Password cannot be empty")
        sys.exit(1)
    
    # Generate hash
    print("\nGenerating password hash...")
    password_hash = generate_password_hash(password)
    
    # Generate session secret
    print("Generating session secret...")
    session_secret = generate_session_secret()
    
    # Output
    print("\n" + "=" * 60)
    print("Configuration for .env file:")
    print("=" * 60)
    print()
    print(f"ADMIN_USERNAME=admin")
    print(f"ADMIN_PASSWORD_HASH={password_hash}")
    print(f"SESSION_SECRET={session_secret}")
    print()
    print("=" * 60)
    print("Add these lines to your .env file")
    print("=" * 60)


if __name__ == '__main__':
    main()
