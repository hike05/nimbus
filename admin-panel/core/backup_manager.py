"""
Backup and restore functionality for VPN server configurations.
"""

import json
import shutil
import tarfile
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional


class BackupManager:
    """Manages configuration backups and restoration."""
    
    def __init__(self, config_dir: str = "/data/stealth-vpn/configs"):
        self.config_dir = Path(config_dir)
        self.backup_dir = self.config_dir.parent / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def create_backup(self, description: str = "") -> str:
        """Create a full backup of all configurations."""
        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}.tar.gz"
            backup_path = self.backup_dir / backup_name
            
            # Create tar archive
            with tarfile.open(backup_path, "w:gz") as tar:
                # Add users.json
                users_file = self.config_dir / "users.json"
                if users_file.exists():
                    tar.add(users_file, arcname="users.json")
                
                # Add server configs
                for config_file in ["xray.json", "trojan.json", "singbox.json"]:
                    config_path = self.config_dir / config_file
                    if config_path.exists():
                        tar.add(config_path, arcname=config_file)
                
                # Add WireGuard configs
                wg_dir = self.config_dir / "wireguard"
                if wg_dir.exists():
                    tar.add(wg_dir, arcname="wireguard")
                
                # Add client configs
                clients_dir = self.config_dir / "clients"
                if clients_dir.exists():
                    tar.add(clients_dir, arcname="clients")
            
            # Save backup metadata
            metadata = {
                "timestamp": timestamp,
                "description": description,
                "filename": backup_name,
                "size": backup_path.stat().st_size
            }
            
            metadata_file = self.backup_dir / f"backup_{timestamp}.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Keep only last 20 backups
            self._cleanup_old_backups(keep=20)
            
            return backup_name
        except Exception as e:
            print(f"Error creating backup: {e}")
            raise
    
    def restore_backup(self, backup_name: str) -> bool:
        """Restore configurations from a backup."""
        try:
            backup_path = self.backup_dir / backup_name
            
            if not backup_path.exists():
                raise FileNotFoundError(f"Backup {backup_name} not found")
            
            # Create a safety backup before restoring
            self.create_backup(description="Pre-restore safety backup")
            
            # Extract backup
            with tarfile.open(backup_path, "r:gz") as tar:
                tar.extractall(self.config_dir)
            
            return True
        except Exception as e:
            print(f"Error restoring backup: {e}")
            return False
    
    def list_backups(self) -> List[Dict]:
        """List all available backups."""
        backups = []
        
        for metadata_file in sorted(self.backup_dir.glob("backup_*.json"), reverse=True):
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    backups.append(metadata)
            except:
                continue
        
        return backups
    
    def delete_backup(self, backup_name: str) -> bool:
        """Delete a specific backup."""
        try:
            backup_path = self.backup_dir / backup_name
            metadata_name = backup_name.replace('.tar.gz', '.json')
            metadata_path = self.backup_dir / metadata_name
            
            if backup_path.exists():
                backup_path.unlink()
            
            if metadata_path.exists():
                metadata_path.unlink()
            
            return True
        except Exception as e:
            print(f"Error deleting backup: {e}")
            return False
    
    def _cleanup_old_backups(self, keep: int = 20):
        """Keep only the most recent N backups."""
        backups = sorted(self.backup_dir.glob("backup_*.tar.gz"))
        
        if len(backups) > keep:
            for old_backup in backups[:-keep]:
                try:
                    old_backup.unlink()
                    # Also delete metadata
                    metadata_file = old_backup.with_suffix('.json')
                    if metadata_file.exists():
                        metadata_file.unlink()
                except:
                    continue
    
    def export_backup(self, backup_name: str) -> Optional[Path]:
        """Get path to backup file for download."""
        backup_path = self.backup_dir / backup_name
        return backup_path if backup_path.exists() else None
