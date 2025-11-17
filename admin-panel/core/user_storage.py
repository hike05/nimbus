"""
User storage implementation for the Stealth VPN Server.
Handles JSON-based user data persistence with backup functionality.
"""

import json
import uuid
import secrets
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Any, List
import shutil
import fcntl
import tempfile

import sys
sys.path.insert(0, '/app/core')
from interfaces import User, UserStorageInterface, ServerConfig


class UserStorage(UserStorageInterface):
    """JSON-based user storage with atomic operations and automatic backups."""
    
    # Schema version for data migration
    SCHEMA_VERSION = 1
    
    def __init__(self, config_dir: str = "/data/stealth-vpn/configs"):
        self.config_dir = Path(config_dir)
        self.users_file = self.config_dir / "users.json"
        self.backup_dir = self.config_dir.parent / "backups"
        self.lock_file = self.config_dir / ".users.lock"
        
        # Ensure directories exist
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize users file if it doesn't exist
        if not self.users_file.exists():
            self._initialize_users_file()
        else:
            # Migrate data if needed
            self._migrate_data_if_needed()
    
    def _initialize_users_file(self):
        """Create initial users.json file with schema version."""
        initial_data = {
            "schema_version": self.SCHEMA_VERSION,
            "users": {},
            "server": {
                "created_at": datetime.utcnow().isoformat() + "Z"
            }
        }
        self._atomic_write(self.users_file, initial_data)
    
    def _atomic_write(self, file_path: Path, data: Dict[str, Any]) -> None:
        """
        Atomically write data to file using temp file and rename.
        This ensures data integrity even if the process is interrupted.
        """
        # Create temp file in the same directory for atomic rename
        temp_fd, temp_path = tempfile.mkstemp(
            dir=file_path.parent,
            prefix=f".{file_path.name}.",
            suffix=".tmp"
        )
        
        try:
            with open(temp_fd, 'w') as f:
                json.dump(data, f, indent=2, sort_keys=True)
                f.flush()
                # Ensure data is written to disk
                import os
                os.fsync(f.fileno())
            
            # Atomic rename
            Path(temp_path).replace(file_path)
        except Exception as e:
            # Clean up temp file on error
            try:
                Path(temp_path).unlink()
            except:
                pass
            raise e
    
    def _create_backup(self, backup_type: str = "auto") -> Path:
        """
        Create a timestamped backup of the users file.
        
        Args:
            backup_type: Type of backup ('auto', 'manual', 'pre-migration')
        
        Returns:
            Path to the created backup file
        """
        if not self.users_file.exists():
            raise FileNotFoundError(f"Users file not found: {self.users_file}")
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"users_{backup_type}_{timestamp}.json"
        
        shutil.copy2(self.users_file, backup_file)
        
        # Keep only last 10 auto backups, unlimited manual/migration backups
        if backup_type == "auto":
            backups = sorted(self.backup_dir.glob("users_auto_*.json"))
            if len(backups) > 10:
                for old_backup in backups[:-10]:
                    old_backup.unlink()
        
        return backup_file
    
    def _acquire_lock(self) -> Any:
        """Acquire file lock for thread-safe operations."""
        lock_fd = open(self.lock_file, 'w')
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        return lock_fd
    
    def _release_lock(self, lock_fd: Any) -> None:
        """Release file lock."""
        if lock_fd:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
            lock_fd.close()
    
    def load_users(self) -> Dict[str, User]:
        """
        Load all users from storage with validation.
        
        Returns:
            Dictionary of username to User objects
        
        Raises:
            ValueError: If user data validation fails
            FileNotFoundError: If users file doesn't exist
        """
        lock_fd = None
        try:
            lock_fd = self._acquire_lock()
            
            with open(self.users_file, 'r') as f:
                data = json.load(f)
            
            users = {}
            errors = []
            
            for username, user_data in data.get("users", {}).items():
                try:
                    # Use from_dict for validation
                    user = User.from_dict({
                        "username": username,
                        "id": user_data.get("id", ""),
                        "xray_uuid": user_data.get("xray_uuid", ""),
                        "wireguard_private_key": user_data.get("wireguard_private_key", ""),
                        "wireguard_public_key": user_data.get("wireguard_public_key", ""),
                        "trojan_password": user_data.get("trojan_password", ""),
                        "shadowtls_password": user_data.get("shadowtls_password"),
                        "shadowsocks_password": user_data.get("shadowsocks_password"),
                        "hysteria2_password": user_data.get("hysteria2_password"),
                        "tuic_uuid": user_data.get("tuic_uuid"),
                        "tuic_password": user_data.get("tuic_password"),
                        "created_at": user_data.get("created_at", ""),
                        "last_seen": user_data.get("last_seen"),
                        "is_active": user_data.get("is_active", True)
                    })
                    users[username] = user
                except ValueError as e:
                    errors.append(f"User {username}: {str(e)}")
            
            if errors:
                print(f"Warning: Some users failed validation:\n" + "\n".join(errors))
            
            return users
            
        except FileNotFoundError:
            print(f"Users file not found: {self.users_file}")
            return {}
        except json.JSONDecodeError as e:
            print(f"Error parsing users file: {e}")
            # Try to restore from backup
            return self._restore_from_latest_backup()
        except Exception as e:
            print(f"Error loading users: {e}")
            return {}
        finally:
            self._release_lock(lock_fd)
    
    def save_users(self, users: Dict[str, User]) -> None:
        """
        Save users to storage with automatic backup and atomic write.
        
        Args:
            users: Dictionary of username to User objects
        
        Raises:
            ValueError: If user validation fails
            IOError: If file operations fail
        """
        lock_fd = None
        try:
            lock_fd = self._acquire_lock()
            
            # Validate all users before saving
            for username, user in users.items():
                user.validate()
            
            # Create backup before saving
            if self.users_file.exists():
                self._create_backup(backup_type="auto")
            
            # Load existing data to preserve server config and schema version
            existing_data = {}
            if self.users_file.exists():
                with open(self.users_file, 'r') as f:
                    existing_data = json.load(f)
            
            # Convert users to dict using to_dict method
            users_data = {}
            for username, user in users.items():
                users_data[username] = user.to_dict()
            
            # Update data with schema version
            data = {
                "schema_version": self.SCHEMA_VERSION,
                "users": users_data,
                "server": existing_data.get("server", {}),
                "last_modified": datetime.utcnow().isoformat() + "Z"
            }
            
            # Write atomically
            self._atomic_write(self.users_file, data)
            
        except Exception as e:
            print(f"Error saving users: {e}")
            raise
        finally:
            self._release_lock(lock_fd)
    
    def add_user(self, username: str) -> User:
        """Create a new user with generated credentials."""
        users = self.load_users()
        
        if username in users:
            raise ValueError(f"User {username} already exists")
        
        # Generate credentials
        user = User(
            username=username,
            id=str(uuid.uuid4()),
            xray_uuid=str(uuid.uuid4()),
            wireguard_private_key=self._generate_wireguard_key(),
            wireguard_public_key="",  # Will be generated from private key
            trojan_password=secrets.token_urlsafe(32),
            shadowtls_password=secrets.token_urlsafe(32),
            shadowsocks_password=secrets.token_urlsafe(32),
            hysteria2_password=secrets.token_urlsafe(32),
            tuic_uuid=str(uuid.uuid4()),
            tuic_password=secrets.token_urlsafe(32),
            created_at=datetime.utcnow().isoformat() + "Z",
            last_seen=None,
            is_active=True
        )
        
        # Generate WireGuard public key from private key
        user.wireguard_public_key = self._generate_wireguard_public_key(user.wireguard_private_key)
        
        users[username] = user
        self.save_users(users)
        
        return user
    
    def remove_user(self, username: str) -> bool:
        """Remove user from storage."""
        users = self.load_users()
        
        if username not in users:
            return False
        
        del users[username]
        self.save_users(users)
        
        return True
    
    def get_user(self, username: str) -> Optional[User]:
        """Get specific user by username."""
        users = self.load_users()
        return users.get(username)
    
    def _generate_wireguard_key(self) -> str:
        """Generate WireGuard private key."""
        import subprocess
        try:
            result = subprocess.run(
                ["wg", "genkey"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except:
            # Fallback to random base64 if wg command not available
            import base64
            return base64.b64encode(secrets.token_bytes(32)).decode('utf-8')
    
    def _generate_wireguard_public_key(self, private_key: str) -> str:
        """Generate WireGuard public key from private key."""
        import subprocess
        try:
            result = subprocess.run(
                ["wg", "pubkey"],
                input=private_key,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except:
            # Fallback to random base64 if wg command not available
            import base64
            return base64.b64encode(secrets.token_bytes(32)).decode('utf-8')
    
    def _migrate_data_if_needed(self) -> None:
        """
        Check schema version and migrate data if needed.
        """
        try:
            with open(self.users_file, 'r') as f:
                data = json.load(f)
            
            current_version = data.get("schema_version", 0)
            
            if current_version < self.SCHEMA_VERSION:
                print(f"Migrating data from version {current_version} to {self.SCHEMA_VERSION}")
                self._migrate_data(current_version, self.SCHEMA_VERSION)
        except Exception as e:
            print(f"Error checking schema version: {e}")
    
    def _migrate_data(self, from_version: int, to_version: int) -> None:
        """
        Migrate data between schema versions.
        
        Args:
            from_version: Current schema version
            to_version: Target schema version
        """
        # Create pre-migration backup
        backup_file = self._create_backup(backup_type="pre-migration")
        print(f"Created pre-migration backup: {backup_file}")
        
        try:
            with open(self.users_file, 'r') as f:
                data = json.load(f)
            
            # Migration logic for version 0 -> 1
            if from_version == 0 and to_version >= 1:
                # Add schema_version field
                data["schema_version"] = 1
                
                # Ensure all users have required Sing-box fields
                for username, user_data in data.get("users", {}).items():
                    if "shadowtls_password" not in user_data:
                        user_data["shadowtls_password"] = secrets.token_urlsafe(32)
                    if "shadowsocks_password" not in user_data:
                        user_data["shadowsocks_password"] = secrets.token_urlsafe(32)
                    if "hysteria2_password" not in user_data:
                        user_data["hysteria2_password"] = secrets.token_urlsafe(32)
                    if "tuic_uuid" not in user_data:
                        user_data["tuic_uuid"] = str(uuid.uuid4())
                    if "tuic_password" not in user_data:
                        user_data["tuic_password"] = secrets.token_urlsafe(32)
            
            # Write migrated data
            self._atomic_write(self.users_file, data)
            print(f"Successfully migrated data to version {to_version}")
            
        except Exception as e:
            print(f"Error during migration: {e}")
            print(f"Restoring from backup: {backup_file}")
            shutil.copy2(backup_file, self.users_file)
            raise
    
    def _restore_from_latest_backup(self) -> Dict[str, User]:
        """
        Restore users from the latest backup file.
        
        Returns:
            Dictionary of restored users
        """
        backups = sorted(self.backup_dir.glob("users_*.json"), reverse=True)
        
        if not backups:
            print("No backup files found")
            return {}
        
        for backup_file in backups:
            try:
                print(f"Attempting to restore from backup: {backup_file}")
                shutil.copy2(backup_file, self.users_file)
                
                # Try to load the restored file
                users = self.load_users()
                print(f"Successfully restored from backup: {backup_file}")
                return users
            except Exception as e:
                print(f"Failed to restore from {backup_file}: {e}")
                continue
        
        print("All backup restoration attempts failed")
        return {}
    
    def restore_from_backup(self, backup_file: Path) -> bool:
        """
        Manually restore from a specific backup file.
        
        Args:
            backup_file: Path to the backup file
        
        Returns:
            True if restoration was successful
        """
        lock_fd = None
        try:
            lock_fd = self._acquire_lock()
            
            if not backup_file.exists():
                raise FileNotFoundError(f"Backup file not found: {backup_file}")
            
            # Create a backup of current state before restoring
            if self.users_file.exists():
                self._create_backup(backup_type="pre-restore")
            
            # Validate backup file before restoring
            with open(backup_file, 'r') as f:
                data = json.load(f)
            
            # Copy backup to users file
            shutil.copy2(backup_file, self.users_file)
            
            # Verify restoration by loading users
            users = self.load_users()
            print(f"Successfully restored {len(users)} users from {backup_file}")
            
            return True
            
        except Exception as e:
            print(f"Error restoring from backup: {e}")
            return False
        finally:
            self._release_lock(lock_fd)
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """
        List all available backup files with metadata.
        
        Returns:
            List of backup file information
        """
        backups = []
        
        for backup_file in sorted(self.backup_dir.glob("users_*.json"), reverse=True):
            try:
                stat = backup_file.stat()
                backups.append({
                    "filename": backup_file.name,
                    "path": str(backup_file),
                    "size": stat.st_size,
                    "created": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "type": backup_file.stem.split("_")[1] if "_" in backup_file.stem else "unknown"
                })
            except Exception as e:
                print(f"Error reading backup file {backup_file}: {e}")
        
        return backups
