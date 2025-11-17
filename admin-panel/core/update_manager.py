"""
System update functionality for VPN server.
Handles Docker image updates, service restarts, and rollback capability.
"""

import docker
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from backup_manager import BackupManager


class UpdateManager:
    """Manages system updates with automatic backup and rollback capability."""
    
    def __init__(self, data_dir: str = "/data/stealth-vpn"):
        self.docker_client = docker.from_env()
        self.data_dir = Path(data_dir)
        self.backup_manager = BackupManager(str(self.data_dir / "configs"))
        
        # Define services and their image names
        self.services = {
            'caddy': 'caddy:2-alpine',
            'xray': 'stealth-xray:latest',
            'trojan': 'stealth-trojan:latest',
            'singbox': 'stealth-singbox:latest',
            'wireguard': 'stealth-wireguard:latest',
            'admin': 'stealth-admin:latest'
        }
    
    def check_for_updates(self) -> Dict[str, Any]:
        """
        Check if updates are available for Docker images.
        
        Returns:
            Dictionary with update availability information
        """
        try:
            update_info = {
                'updates_available': False,
                'services': {},
                'checked_at': datetime.utcnow().isoformat()
            }
            
            for service, image_name in self.services.items():
                try:
                    # Get local image
                    local_image = self.docker_client.images.get(image_name)
                    local_id = local_image.id
                    
                    # Pull latest image info (without downloading)
                    # Note: Docker API doesn't have a direct "check without pull" method
                    # We'll need to pull to check, but we can compare IDs
                    
                    update_info['services'][service] = {
                        'current_image': image_name,
                        'local_id': local_id[:12],  # Short ID
                        'status': 'checking'
                    }
                    
                except docker.errors.ImageNotFound:
                    update_info['services'][service] = {
                        'current_image': image_name,
                        'local_id': None,
                        'status': 'not_installed'
                    }
                except Exception as e:
                    update_info['services'][service] = {
                        'current_image': image_name,
                        'error': str(e),
                        'status': 'error'
                    }
            
            return update_info
            
        except Exception as e:
            return {
                'error': str(e),
                'updates_available': False,
                'checked_at': datetime.utcnow().isoformat()
            }
    
    def pull_latest_images(self) -> Dict[str, bool]:
        """
        Pull latest Docker images for all services.
        
        Returns:
            Dictionary mapping service names to success status
        """
        results = {}
        
        for service, image_name in self.services.items():
            try:
                print(f"Pulling {image_name}...")
                
                # For custom images (stealth-*), we need to rebuild
                if image_name.startswith('stealth-'):
                    results[service] = {
                        'success': True,
                        'message': 'Custom image - requires rebuild',
                        'action': 'rebuild_required'
                    }
                else:
                    # Pull official images (like Caddy)
                    self.docker_client.images.pull(image_name)
                    results[service] = {
                        'success': True,
                        'message': f'Successfully pulled {image_name}',
                        'action': 'pulled'
                    }
                    
            except Exception as e:
                results[service] = {
                    'success': False,
                    'error': str(e),
                    'action': 'failed'
                }
                print(f"Failed to pull {service}: {e}")
        
        return results
    
    def rebuild_custom_images(self) -> Dict[str, bool]:
        """
        Rebuild custom Docker images from source.
        
        Returns:
            Dictionary mapping service names to success status
        """
        results = {}
        
        # Custom images that need rebuilding
        custom_services = {
            'xray': 'xray',
            'trojan': 'trojan',
            'singbox': 'singbox',
            'wireguard': 'wireguard',
            'admin': 'admin-panel'
        }
        
        for service, build_dir in custom_services.items():
            try:
                print(f"Rebuilding {service}...")
                
                # Use docker-compose to rebuild
                result = subprocess.run(
                    ['docker-compose', 'build', '--no-cache', service],
                    cwd='/app',
                    capture_output=True,
                    text=True,
                    timeout=600  # 10 minute timeout
                )
                
                if result.returncode == 0:
                    results[service] = {
                        'success': True,
                        'message': f'Successfully rebuilt {service}'
                    }
                else:
                    results[service] = {
                        'success': False,
                        'error': result.stderr or 'Build failed',
                        'stdout': result.stdout
                    }
                    
            except subprocess.TimeoutExpired:
                results[service] = {
                    'success': False,
                    'error': 'Build timeout (10 minutes)'
                }
            except Exception as e:
                results[service] = {
                    'success': False,
                    'error': str(e)
                }
                print(f"Failed to rebuild {service}: {e}")
        
        return results
    
    def restart_service(self, service: str, preserve_data: bool = True) -> Dict[str, Any]:
        """
        Restart a specific service with new image.
        
        Args:
            service: Service name (e.g., 'xray', 'caddy')
            preserve_data: Whether to preserve data volumes
            
        Returns:
            Dictionary with restart status
        """
        try:
            container_name = f"stealth-{service}"
            
            # Get container
            try:
                container = self.docker_client.containers.get(container_name)
                
                # Graceful stop
                print(f"Stopping {container_name}...")
                container.stop(timeout=30)
                
                # Remove container
                container.remove()
                
            except docker.errors.NotFound:
                print(f"Container {container_name} not found, will create new one")
            
            # Restart with docker-compose
            print(f"Starting {service}...")
            result = subprocess.run(
                ['docker-compose', 'up', '-d', service],
                cwd='/app',
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'message': f'Service {service} restarted successfully'
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr or 'Restart failed',
                    'stdout': result.stdout
                }
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Restart timeout (2 minutes)'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def restart_all_services(self) -> Dict[str, Any]:
        """
        Restart all services with new images.
        
        Returns:
            Dictionary mapping service names to restart status
        """
        results = {}
        
        # Restart order: VPN services first, then Caddy, then admin last
        restart_order = ['xray', 'trojan', 'singbox', 'wireguard', 'caddy', 'admin']
        
        for service in restart_order:
            if service in self.services:
                results[service] = self.restart_service(service)
        
        return results
    
    def create_pre_update_backup(self) -> str:
        """
        Create a backup before performing update.
        
        Returns:
            Backup filename
        """
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        description = f"Automatic backup before system update - {timestamp}"
        
        return self.backup_manager.create_backup(description)
    
    def rollback_from_backup(self, backup_name: str) -> bool:
        """
        Rollback system to a previous backup.
        
        Args:
            backup_name: Name of backup to restore
            
        Returns:
            True if rollback successful
        """
        try:
            # Restore backup
            success = self.backup_manager.restore_backup(backup_name)
            
            if success:
                # Restart all services to apply restored configs
                restart_results = self.restart_all_services()
                
                # Check if all services restarted successfully
                all_success = all(
                    result.get('success', False) 
                    for result in restart_results.values()
                )
                
                return all_success
            
            return False
            
        except Exception as e:
            print(f"Rollback failed: {e}")
            return False
    
    def perform_update(self, rebuild_images: bool = False) -> Dict[str, Any]:
        """
        Perform full system update with automatic backup and rollback on failure.
        
        Args:
            rebuild_images: Whether to rebuild custom images from source
            
        Returns:
            Dictionary with update results
        """
        update_result = {
            'success': False,
            'backup_created': None,
            'pull_results': {},
            'rebuild_results': {},
            'restart_results': {},
            'errors': [],
            'started_at': datetime.utcnow().isoformat()
        }
        
        try:
            # Step 1: Create backup
            print("Creating pre-update backup...")
            backup_name = self.create_pre_update_backup()
            update_result['backup_created'] = backup_name
            print(f"Backup created: {backup_name}")
            
            # Step 2: Pull latest images
            print("Pulling latest images...")
            pull_results = self.pull_latest_images()
            update_result['pull_results'] = pull_results
            
            # Check if any pulls failed
            pull_failures = [
                service for service, result in pull_results.items()
                if not result.get('success', False)
            ]
            
            if pull_failures:
                update_result['errors'].append(
                    f"Failed to pull images for: {', '.join(pull_failures)}"
                )
            
            # Step 3: Rebuild custom images if requested
            if rebuild_images:
                print("Rebuilding custom images...")
                rebuild_results = self.rebuild_custom_images()
                update_result['rebuild_results'] = rebuild_results
                
                # Check if any rebuilds failed
                rebuild_failures = [
                    service for service, result in rebuild_results.items()
                    if not result.get('success', False)
                ]
                
                if rebuild_failures:
                    update_result['errors'].append(
                        f"Failed to rebuild images for: {', '.join(rebuild_failures)}"
                    )
                    
                    # If critical services failed, rollback
                    if any(s in rebuild_failures for s in ['xray', 'admin']):
                        print("Critical service rebuild failed, rolling back...")
                        rollback_success = self.rollback_from_backup(backup_name)
                        update_result['rollback_performed'] = True
                        update_result['rollback_success'] = rollback_success
                        update_result['completed_at'] = datetime.utcnow().isoformat()
                        return update_result
            
            # Step 4: Restart services
            print("Restarting services...")
            restart_results = self.restart_all_services()
            update_result['restart_results'] = restart_results
            
            # Check if any restarts failed
            restart_failures = [
                service for service, result in restart_results.items()
                if not result.get('success', False)
            ]
            
            if restart_failures:
                update_result['errors'].append(
                    f"Failed to restart services: {', '.join(restart_failures)}"
                )
                
                # If critical services failed, rollback
                if any(s in restart_failures for s in ['xray', 'admin', 'caddy']):
                    print("Critical service restart failed, rolling back...")
                    rollback_success = self.rollback_from_backup(backup_name)
                    update_result['rollback_performed'] = True
                    update_result['rollback_success'] = rollback_success
                    update_result['completed_at'] = datetime.utcnow().isoformat()
                    return update_result
            
            # Step 5: Verify services are running
            print("Verifying services...")
            all_services_ok = True
            for service in self.services.keys():
                try:
                    container_name = f"stealth-{service}"
                    container = self.docker_client.containers.get(container_name)
                    if container.status != 'running':
                        all_services_ok = False
                        update_result['errors'].append(
                            f"Service {service} is not running after update"
                        )
                except:
                    all_services_ok = False
                    update_result['errors'].append(
                        f"Service {service} container not found after update"
                    )
            
            # Determine overall success
            update_result['success'] = all_services_ok and len(update_result['errors']) == 0
            update_result['completed_at'] = datetime.utcnow().isoformat()
            
            if update_result['success']:
                print("Update completed successfully!")
            else:
                print(f"Update completed with errors: {update_result['errors']}")
            
            return update_result
            
        except Exception as e:
            update_result['errors'].append(f"Update failed: {str(e)}")
            update_result['completed_at'] = datetime.utcnow().isoformat()
            
            # Attempt rollback on unexpected error
            if update_result['backup_created']:
                print(f"Unexpected error, rolling back: {e}")
                rollback_success = self.rollback_from_backup(update_result['backup_created'])
                update_result['rollback_performed'] = True
                update_result['rollback_success'] = rollback_success
            
            return update_result
    
    def get_service_versions(self) -> Dict[str, Any]:
        """
        Get current version information for all services.
        
        Returns:
            Dictionary with version information
        """
        versions = {}
        
        for service, image_name in self.services.items():
            try:
                container_name = f"stealth-{service}"
                container = self.docker_client.containers.get(container_name)
                
                # Get image info
                image = container.image
                
                versions[service] = {
                    'image': image_name,
                    'image_id': image.id[:12],
                    'created': image.attrs.get('Created', 'unknown'),
                    'status': container.status,
                    'container_id': container.id[:12]
                }
                
            except docker.errors.NotFound:
                versions[service] = {
                    'image': image_name,
                    'status': 'not_running'
                }
            except Exception as e:
                versions[service] = {
                    'image': image_name,
                    'error': str(e)
                }
        
        return versions
