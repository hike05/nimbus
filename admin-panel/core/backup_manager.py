"""
Backup and restore functionality for VPN server configurations.
"""

import json
import shutil
import tarfile
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import os


class BackupManager:
    """Manages configuration backups and restoration."""
    
    def __init__(self, config_dir: str = "/data/stealth-vpn/configs"):
        self.config_dir = Path(config_dir)
        self.backup_dir = self.config_dir.parent / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Define paths for additional backup items
        self.ssl_cert_dir = Path("/data/caddy/certificates")
        self.caddyfile_path = Path("/etc/caddy/Caddyfile")
        self.docker_compose_path = Path("/app/docker-compose.yml")
        
        # Version info
        self.backup_version = "2.0"
    
    def create_backup(self, description: str = "") -> str:
        """Create a full backup of all configurations including SSL certs and system configs."""
        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}.tar.gz"
            backup_path = self.backup_dir / backup_name
            
            # Track what's included in this backup
            included_items = []
            
            # Create tar archive
            with tarfile.open(backup_path, "w:gz") as tar:
                # Add users.json
                users_file = self.config_dir / "users.json"
                if users_file.exists():
                    tar.add(users_file, arcname="configs/users.json")
                    included_items.append("users.json")
                
                # Add server configs
                for config_file in ["xray.json", "trojan.json", "singbox.json"]:
                    config_path = self.config_dir / config_file
                    if config_path.exists():
                        tar.add(config_path, arcname=f"configs/{config_file}")
                        included_items.append(config_file)
                
                # Add WireGuard configs
                wg_dir = self.config_dir / "wireguard"
                if wg_dir.exists():
                    tar.add(wg_dir, arcname="configs/wireguard")
                    included_items.append("wireguard configs")
                
                # Add client configs
                clients_dir = self.config_dir / "clients"
                if clients_dir.exists():
                    tar.add(clients_dir, arcname="configs/clients")
                    included_items.append("client configs")
                
                # Add SSL certificates (if accessible)
                if self.ssl_cert_dir.exists() and os.access(self.ssl_cert_dir, os.R_OK):
                    try:
                        tar.add(self.ssl_cert_dir, arcname="certificates")
                        included_items.append("SSL certificates")
                    except (PermissionError, OSError) as e:
                        print(f"Warning: Could not backup SSL certificates: {e}")
                
                # Add Caddyfile (if accessible)
                if self.caddyfile_path.exists() and os.access(self.caddyfile_path, os.R_OK):
                    try:
                        tar.add(self.caddyfile_path, arcname="Caddyfile")
                        included_items.append("Caddyfile")
                    except (PermissionError, OSError) as e:
                        print(f"Warning: Could not backup Caddyfile: {e}")
                
                # Add docker-compose.yml (if accessible)
                if self.docker_compose_path.exists() and os.access(self.docker_compose_path, os.R_OK):
                    try:
                        tar.add(self.docker_compose_path, arcname="docker-compose.yml")
                        included_items.append("docker-compose.yml")
                    except (PermissionError, OSError) as e:
                        print(f"Warning: Could not backup docker-compose.yml: {e}")
            
            # Save enhanced backup metadata
            metadata = {
                "version": self.backup_version,
                "timestamp": timestamp,
                "description": description,
                "filename": backup_name,
                "size": backup_path.stat().st_size,
                "included_items": included_items,
                "created_at": datetime.utcnow().isoformat() + "Z"
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
    
    def validate_backup_integrity(self, backup_name: str) -> Dict[str, any]:
        """Validate backup file integrity and return metadata."""
        try:
            backup_path = self.backup_dir / backup_name
            
            if not backup_path.exists():
                return {
                    'valid': False,
                    'error': f"Backup file {backup_name} not found"
                }
            
            # Try to open and read the tar.gz file
            try:
                with tarfile.open(backup_path, "r:gz") as tar:
                    members = tar.getmembers()
                    
                    # Check for essential files
                    member_names = [m.name for m in members]
                    has_users = any('users.json' in name for name in member_names)
                    has_configs = any('configs/' in name for name in member_names)
                    
                    return {
                        'valid': True,
                        'file_count': len(members),
                        'has_users': has_users,
                        'has_configs': has_configs,
                        'size': backup_path.stat().st_size,
                        'members': member_names[:10]  # First 10 files for preview
                    }
            except tarfile.TarError as e:
                return {
                    'valid': False,
                    'error': f"Invalid tar.gz file: {str(e)}"
                }
            except Exception as e:
                return {
                    'valid': False,
                    'error': f"Cannot read backup file: {str(e)}"
                }
                
        except Exception as e:
            return {
                'valid': False,
                'error': f"Validation error: {str(e)}"
            }
    
    def restore_backup(self, backup_name: str, service_manager=None) -> Dict[str, any]:
        """
        Restore configurations from a backup with service management.
        
        Args:
            backup_name: Name of the backup file to restore
            service_manager: Optional DockerServiceManager instance for stopping/starting services
            
        Returns:
            Dictionary with success status, message, and details
        """
        result = {
            'success': False,
            'message': '',
            'safety_backup': None,
            'services_stopped': [],
            'services_restarted': [],
            'files_restored': [],
            'errors': []
        }
        
        try:
            backup_path = self.backup_dir / backup_name
            
            if not backup_path.exists():
                result['message'] = f"Backup {backup_name} not found"
                return result
            
            # Step 1: Validate backup integrity
            print("Validating backup integrity...")
            validation = self.validate_backup_integrity(backup_name)
            if not validation['valid']:
                result['message'] = f"Backup validation failed: {validation.get('error', 'Unknown error')}"
                return result
            
            # Step 2: Create a safety backup before restoring
            print("Creating safety backup before restore...")
            try:
                safety_backup_name = self.create_backup(description="Pre-restore safety backup (automatic)")
                result['safety_backup'] = safety_backup_name
                print(f"Safety backup created: {safety_backup_name}")
            except Exception as e:
                result['errors'].append(f"Failed to create safety backup: {str(e)}")
                result['message'] = "Cannot proceed without safety backup"
                return result
            
            # Step 3: Stop VPN services if service_manager is provided
            if service_manager:
                print("Stopping VPN services...")
                services_to_stop = ['xray', 'trojan', 'singbox', 'wireguard']
                for service in services_to_stop:
                    try:
                        if service_manager.stop_service(service):
                            result['services_stopped'].append(service)
                            print(f"Stopped service: {service}")
                        else:
                            result['errors'].append(f"Failed to stop service: {service}")
                    except Exception as e:
                        result['errors'].append(f"Error stopping {service}: {str(e)}")
            
            # Step 4: Extract and restore backup
            print("Extracting backup...")
            temp_dir = self.backup_dir / "temp_restore"
            temp_dir.mkdir(exist_ok=True)
            
            try:
                # Extract backup to temp directory
                with tarfile.open(backup_path, "r:gz") as tar:
                    tar.extractall(temp_dir)
                
                # Restore configs
                configs_dir = temp_dir / "configs"
                if configs_dir.exists():
                    # Restore users.json
                    users_file = configs_dir / "users.json"
                    if users_file.exists():
                        shutil.copy2(users_file, self.config_dir / "users.json")
                        result['files_restored'].append("users.json")
                    
                    # Restore server configs
                    for config_file in ["xray.json", "trojan.json", "singbox.json"]:
                        src = configs_dir / config_file
                        if src.exists():
                            shutil.copy2(src, self.config_dir / config_file)
                            result['files_restored'].append(config_file)
                    
                    # Restore WireGuard configs
                    wg_src = configs_dir / "wireguard"
                    wg_dst = self.config_dir / "wireguard"
                    if wg_src.exists():
                        if wg_dst.exists():
                            shutil.rmtree(wg_dst)
                        shutil.copytree(wg_src, wg_dst)
                        result['files_restored'].append("wireguard/")
                    
                    # Restore client configs
                    clients_src = configs_dir / "clients"
                    clients_dst = self.config_dir / "clients"
                    if clients_src.exists():
                        if clients_dst.exists():
                            shutil.rmtree(clients_dst)
                        shutil.copytree(clients_src, clients_dst)
                        result['files_restored'].append("clients/")
                
                # Restore SSL certificates (if present and writable)
                certs_src = temp_dir / "certificates"
                if certs_src.exists() and self.ssl_cert_dir.exists():
                    try:
                        if os.access(self.ssl_cert_dir, os.W_OK):
                            # Clear existing certificates
                            for item in self.ssl_cert_dir.iterdir():
                                if item.is_file():
                                    item.unlink()
                                elif item.is_dir():
                                    shutil.rmtree(item)
                            # Copy restored certificates
                            for item in certs_src.iterdir():
                                if item.is_file():
                                    shutil.copy2(item, self.ssl_cert_dir / item.name)
                                elif item.is_dir():
                                    shutil.copytree(item, self.ssl_cert_dir / item.name)
                            result['files_restored'].append("SSL certificates")
                    except (PermissionError, OSError) as e:
                        result['errors'].append(f"Could not restore SSL certificates: {str(e)}")
                
                # Restore Caddyfile (if present and writable)
                caddyfile_src = temp_dir / "Caddyfile"
                if caddyfile_src.exists() and os.access(self.caddyfile_path.parent, os.W_OK):
                    try:
                        shutil.copy2(caddyfile_src, self.caddyfile_path)
                        result['files_restored'].append("Caddyfile")
                    except (PermissionError, OSError) as e:
                        result['errors'].append(f"Could not restore Caddyfile: {str(e)}")
                
                print(f"Restored {len(result['files_restored'])} items")
                
            finally:
                # Clean up temp directory
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
            
            # Step 5: Restart VPN services if service_manager is provided
            if service_manager and result['services_stopped']:
                print("Restarting VPN services...")
                for service in result['services_stopped']:
                    try:
                        if service_manager.start_service(service):
                            result['services_restarted'].append(service)
                            print(f"Restarted service: {service}")
                        else:
                            result['errors'].append(f"Failed to restart service: {service}")
                    except Exception as e:
                        result['errors'].append(f"Error restarting {service}: {str(e)}")
                
                # Check if critical services failed to restart
                critical_failures = [s for s in result['services_stopped'] if s not in result['services_restarted']]
                if critical_failures:
                    result['errors'].append(f"Critical services failed to restart: {', '.join(critical_failures)}")
                    result['message'] = "Restore completed but some services failed to restart. Consider rollback."
                    
                    # Attempt rollback if too many failures
                    if len(critical_failures) >= 2:
                        print("Too many service failures, attempting rollback...")
                        result['errors'].append("Attempting automatic rollback to safety backup...")
                        
                        # Recursive call to restore the safety backup
                        if result['safety_backup']:
                            rollback_result = self.restore_backup(result['safety_backup'], service_manager)
                            if rollback_result['success']:
                                result['message'] = "Restore failed. Rolled back to previous state successfully."
                            else:
                                result['message'] = "Restore failed and rollback also failed. Manual intervention required."
                        
                        return result
            
            # Success!
            result['success'] = True
            result['message'] = f"Backup restored successfully. {len(result['files_restored'])} items restored."
            
            if result['errors']:
                result['message'] += f" ({len(result['errors'])} warnings)"
            
            return result
            
        except Exception as e:
            result['message'] = f"Error restoring backup: {str(e)}"
            result['errors'].append(str(e))
            
            # Attempt rollback on critical failure
            if result['safety_backup'] and service_manager:
                print("Critical error during restore, attempting rollback...")
                result['errors'].append("Attempting automatic rollback to safety backup...")
                rollback_result = self.restore_backup(result['safety_backup'], service_manager)
                if rollback_result['success']:
                    result['message'] = "Restore failed. Rolled back to previous state successfully."
                else:
                    result['message'] = "Restore failed and rollback also failed. Manual intervention required."
            
            return result
    
    def list_backups(self) -> List[Dict]:
        """List all available backups with enhanced metadata."""
        backups = []
        
        for metadata_file in sorted(self.backup_dir.glob("backup_*.json"), reverse=True):
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    
                    # Ensure all expected fields are present (backward compatibility)
                    if "version" not in metadata:
                        metadata["version"] = "1.0"
                    if "included_items" not in metadata:
                        metadata["included_items"] = ["users.json", "vpn configs", "client configs"]
                    if "created_at" not in metadata and "timestamp" in metadata:
                        # Convert old timestamp format to ISO format
                        try:
                            dt = datetime.strptime(metadata["timestamp"], "%Y%m%d_%H%M%S")
                            metadata["created_at"] = dt.isoformat() + "Z"
                        except:
                            metadata["created_at"] = metadata["timestamp"]
                    
                    # Add human-readable size
                    if "size" in metadata:
                        metadata["size_human"] = self._format_size(metadata["size"])
                    
                    backups.append(metadata)
            except Exception as e:
                print(f"Warning: Could not read metadata from {metadata_file}: {e}")
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
    
    def get_backup_metadata(self, backup_name: str) -> Optional[Dict]:
        """Get metadata for a specific backup."""
        try:
            timestamp = backup_name.replace("backup_", "").replace(".tar.gz", "")
            metadata_file = self.backup_dir / f"backup_{timestamp}.json"
            
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    # Add human-readable size
                    if "size" in metadata:
                        metadata["size_human"] = self._format_size(metadata["size"])
                    return metadata
            return None
        except Exception as e:
            print(f"Error reading backup metadata: {e}")
            return None
    
    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format size in bytes to human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"
    
    def export_backup(self, backup_name: str) -> Optional[Path]:
        """Get path to backup file for download."""
        backup_path = self.backup_dir / backup_name
        return backup_path if backup_path.exists() else None
    
    def upload_backup(self, file_data: bytes, filename: str) -> bool:
        """
        Save uploaded backup file to backup directory.
        
        Args:
            file_data: Binary content of the backup file
            filename: Name for the backup file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            backup_path = self.backup_dir / filename
            
            # Write the file
            backup_path.write_bytes(file_data)
            
            # Set proper permissions (readable by owner and group)
            backup_path.chmod(0o640)
            
            # Create metadata for the uploaded backup
            timestamp = filename.replace('backup_', '').replace('.tar.gz', '').replace('_uploaded', '')
            metadata = {
                "version": self.backup_version,
                "timestamp": timestamp,
                "description": "Uploaded backup",
                "filename": filename,
                "size": len(file_data),
                "included_items": ["Unknown - uploaded backup"],
                "created_at": datetime.utcnow().isoformat() + "Z",
                "uploaded": True
            }
            
            # Try to extract actual metadata from the backup if possible
            try:
                import tarfile
                from io import BytesIO
                
                with tarfile.open(fileobj=BytesIO(file_data), mode='r:gz') as tar:
                    members = tar.getmembers()
                    member_names = [m.name for m in members]
                    
                    # Check for metadata.json in the backup
                    if 'metadata.json' in member_names:
                        metadata_member = tar.extractfile('metadata.json')
                        if metadata_member:
                            existing_metadata = json.load(metadata_member)
                            # Merge with existing metadata
                            metadata.update(existing_metadata)
                            metadata['uploaded'] = True
                    else:
                        # Infer included items from tar contents
                        included = []
                        if any('users.json' in name for name in member_names):
                            included.append('users.json')
                        if any('configs/' in name for name in member_names):
                            included.append('vpn configs')
                        if any('clients/' in name for name in member_names):
                            included.append('client configs')
                        if any('certificates' in name for name in member_names):
                            included.append('SSL certificates')
                        if any('Caddyfile' in name for name in member_names):
                            included.append('Caddyfile')
                        
                        if included:
                            metadata['included_items'] = included
            except Exception as e:
                print(f"Warning: Could not extract metadata from uploaded backup: {e}")
            
            # Save metadata
            metadata_file = self.backup_dir / filename.replace('.tar.gz', '.json')
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"Uploaded backup saved: {filename}")
            return True
            
        except Exception as e:
            print(f"Error uploading backup: {e}")
            return False
