# User Storage Implementation

## Overview

Task 8 has been completed, implementing a robust JSON-based user storage system with data validation, atomic operations, and automatic backups.

## Components Implemented

### 1. Data Models with Validation (Task 8.1)

#### User Data Model (`core/interfaces.py`)
- **Validation Features:**
  - Username: 3-32 characters, alphanumeric with underscore/hyphen
  - UUID format validation for user ID, Xray UUID, and TUIC UUID
  - Minimum key length validation (32+ characters for WireGuard keys)
  - Minimum password length validation (16+ characters for Trojan)
  - ISO 8601 date format validation for timestamps
  
- **Serialization:**
  - `to_dict()`: Convert User object to dictionary for JSON storage
  - `from_dict()`: Create User object from dictionary with validation
  - Automatic validation on object creation via `__post_init__`

#### ServerConfig Data Model
- **Validation Features:**
  - WireGuard server key validation (32+ characters)
  - Xray private key validation (32+ characters)
  - Admin password hash presence check
  - Session secret validation (32+ characters)
  - Obfuscated endpoints type checking

- **Serialization:**
  - `to_dict()` and `from_dict()` methods for JSON operations

### 2. Storage Operations (Task 8.2)

#### Atomic Write Operations
- **Implementation:** `_atomic_write()` method
- **Features:**
  - Uses temporary file + atomic rename for data integrity
  - Ensures data is flushed to disk before rename
  - Automatic cleanup on failure
  - Prevents data corruption during write operations

#### Automatic Backup System
- **Implementation:** `_create_backup()` method
- **Features:**
  - Timestamped backups with type classification (auto, manual, pre-migration, pre-restore)
  - Automatic retention policy (keeps last 10 auto backups)
  - Unlimited retention for manual and migration backups
  - Backup before every save operation

#### File Locking
- **Implementation:** `_acquire_lock()` and `_release_lock()` methods
- **Features:**
  - Thread-safe operations using fcntl file locking
  - Prevents concurrent write conflicts
  - Automatic lock release on operation completion

#### Data Migration
- **Implementation:** `_migrate_data_if_needed()` and `_migrate_data()` methods
- **Features:**
  - Schema version tracking
  - Automatic migration on version mismatch
  - Pre-migration backup creation
  - Automatic rollback on migration failure
  - Version 0 → 1 migration: Adds Sing-box protocol credentials

#### Backup Management
- **Implementation:** `restore_from_backup()`, `_restore_from_latest_backup()`, `list_backups()` methods
- **Features:**
  - Manual restoration from specific backup
  - Automatic restoration from latest backup on corruption
  - Backup listing with metadata (filename, size, created date, type)
  - Pre-restore backup creation

#### Enhanced Load/Save Operations
- **Load Users:**
  - File locking for thread safety
  - Validation of all loaded users
  - Error collection and reporting
  - Automatic restoration from backup on JSON parse errors
  
- **Save Users:**
  - Pre-save validation of all users
  - Automatic backup before save
  - Atomic write operation
  - Schema version and last_modified timestamp tracking
  - Preservation of server configuration

## File Structure

```
core/
├── interfaces.py              # Data models with validation

admin-panel/core/
├── interfaces.py              # Copy of data models for container
├── user_storage.py            # Storage implementation

scripts/
└── test-user-storage.py       # Validation and serialization tests

data/stealth-vpn/
├── configs/
│   ├── users.json            # Main user data file
│   └── .users.lock           # Lock file for atomic operations
└── backups/
    ├── users_auto_*.json     # Automatic backups
    ├── users_manual_*.json   # Manual backups
    └── users_pre-migration_*.json  # Pre-migration backups
```

## Data Format

### users.json Structure
```json
{
  "schema_version": 1,
  "users": {
    "username": {
      "id": "uuid",
      "xray_uuid": "uuid",
      "wireguard_private_key": "key",
      "wireguard_public_key": "key",
      "trojan_password": "password",
      "shadowtls_password": "password",
      "shadowsocks_password": "password",
      "hysteria2_password": "password",
      "tuic_uuid": "uuid",
      "tuic_password": "password",
      "created_at": "ISO8601",
      "last_seen": "ISO8601 or null",
      "is_active": true
    }
  },
  "server": {
    "created_at": "ISO8601"
  },
  "last_modified": "ISO8601"
}
```

## Testing

All tests pass successfully:
- ✓ User validation (username, UUID, password, date formats)
- ✓ User serialization (to_dict/from_dict)
- ✓ ServerConfig validation

Run tests with:
```bash
python3 scripts/test-user-storage.py
```

## Requirements Satisfied

- **Requirement 4.1:** User data models with validation ✓
- **Requirement 4.2:** JSON serialization/deserialization ✓
- **Requirement 4.3:** Atomic storage operations with file locking ✓
- **Requirement 4.4:** Automatic backup system with retention policy ✓

## Error Handling

The implementation includes comprehensive error handling:
- Validation errors with descriptive messages
- JSON parse error recovery via backup restoration
- File operation error handling with cleanup
- Migration failure rollback
- Concurrent access protection via file locking

## Security Features

- Password and key length validation
- UUID format validation to prevent injection
- Atomic writes prevent partial data corruption
- File locking prevents race conditions
- Automatic backups enable recovery from errors
