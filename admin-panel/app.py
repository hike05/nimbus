"""
Stealth VPN Server Admin Panel
Masqueraded as a cloud storage management interface.
"""

import os
import sys
import json
import secrets
from pathlib import Path
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
import bcrypt

# Add core modules to path
sys.path.insert(0, '/app/core')
sys.path.insert(0, '/app')

from user_storage import UserStorage
from config_generator import ConfigGenerator
from service_manager import DockerServiceManager
from client_config_manager import ClientConfigManager
from backup_manager import BackupManager

# Try to import endpoint manager from parent directory
try:
    from core.endpoint_manager import EndpointManager
except ImportError:
    # Fallback if not available
    EndpointManager = None

app = Flask(__name__)
app.secret_key = os.environ.get('SESSION_SECRET', secrets.token_hex(32))
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Configuration
DATA_DIR = Path(os.environ.get('DATA_DIR', '/app/data'))
CONFIG_DIR = DATA_DIR / 'configs'
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD_HASH = os.environ.get('ADMIN_PASSWORD_HASH', '')
DOMAIN = os.environ.get('DOMAIN', 'your-domain.com')

# Initialize managers
user_storage = UserStorage(str(CONFIG_DIR))
config_generator = ConfigGenerator(str(CONFIG_DIR), DOMAIN)
service_manager = DockerServiceManager()
client_config_manager = ClientConfigManager(str(CONFIG_DIR), DOMAIN)
backup_manager = BackupManager(str(CONFIG_DIR))

# Initialize endpoint manager if available
endpoint_manager = None
if EndpointManager:
    try:
        endpoint_manager = EndpointManager(str(DATA_DIR / 'endpoints.json'))
    except Exception as e:
        print(f"Warning: Could not initialize endpoint manager: {e}")


def get_current_endpoints():
    """Get current obfuscated endpoints from configuration."""
    if endpoint_manager:
        endpoints = endpoint_manager.load_endpoints()
        if endpoints:
            return endpoints
    
    # Fallback to default endpoints if not configured
    return {
        'admin_panel': '/api/v2/storage/upload',
        'xray_websocket': '/cdn/assets/js/analytics.min.js',
        'wireguard_websocket': '/static/fonts/woff2/roboto-regular.woff2',
        'trojan_websocket': '/api/v1/files/sync'
    }


def require_auth(f):
    """Decorator to require authentication for routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'authenticated' not in session or not session['authenticated']:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/health')
def health():
    """Health check endpoint for Docker."""
    return jsonify({'status': 'healthy'}), 200


@app.route('/api/v2/storage/login', methods=['GET'])
def login():
    """Login page (masqueraded as storage login)."""
    if 'authenticated' in session and session['authenticated']:
        return redirect(url_for('admin_panel'))
    return render_template('login.html')


@app.route('/api/v2/storage/auth', methods=['POST'])
def authenticate():
    """Authenticate admin user."""
    data = request.get_json()
    username = data.get('username', '')
    password = data.get('password', '')
    
    # Verify credentials
    if username == ADMIN_USERNAME:
        # Check password hash
        if ADMIN_PASSWORD_HASH:
            if bcrypt.checkpw(password.encode('utf-8'), ADMIN_PASSWORD_HASH.encode('utf-8')):
                session['authenticated'] = True
                session['username'] = username
                session.permanent = True
                return jsonify({'success': True, 'redirect': '/api/v2/storage/upload'})
        else:
            # Development mode - allow any password if hash not set
            session['authenticated'] = True
            session['username'] = username
            session.permanent = True
            return jsonify({'success': True, 'redirect': '/api/v2/storage/upload'})
    
    return jsonify({'error': 'Invalid credentials'}), 401


@app.route('/api/v2/storage/logout', methods=['POST'])
def logout():
    """Logout admin user."""
    session.clear()
    return jsonify({'success': True})


@app.route('/api/v2/storage/upload', methods=['GET'])
@require_auth
def admin_panel():
    """Main admin panel (masqueraded as file upload interface)."""
    return render_template('admin.html', domain=DOMAIN)


@app.route('/api/v2/storage/files', methods=['GET'])
@require_auth
def list_users():
    """List all VPN users (masqueraded as file listing)."""
    try:
        users = user_storage.load_users()
        
        # Convert to API response format
        user_list = []
        for username, user in users.items():
            user_list.append({
                'username': username,
                'id': user.id,
                'created_at': user.created_at,
                'last_seen': user.last_seen,
                'is_active': user.is_active
            })
        
        return jsonify({
            'success': True,
            'files': user_list  # Masqueraded as "files"
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v2/storage/files', methods=['POST'])
@require_auth
def create_user():
    """Create new VPN user (masqueraded as file upload)."""
    try:
        data = request.get_json()
        username = data.get('filename', '').strip()  # Masqueraded as "filename"
        
        if not username:
            return jsonify({'error': 'Username is required'}), 400
        
        # Check if user already exists
        existing_users = user_storage.load_users()
        if username in existing_users:
            return jsonify({'error': 'User already exists'}), 400
        
        # Create user
        user = user_storage.add_user(username)
        
        # Save client configuration files
        client_config_manager.save_client_configs(username, user)
        
        # Update server configurations
        config_generator.update_server_configs()
        
        return jsonify({
            'success': True,
            'message': f'User {username} created successfully',
            'user': {
                'username': username,
                'id': user.id,
                'created_at': user.created_at,
                'is_active': user.is_active
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v2/storage/files/<username>', methods=['DELETE'])
@require_auth
def delete_user(username):
    """Delete VPN user (masqueraded as file deletion)."""
    try:
        success = user_storage.remove_user(username)
        
        if success:
            # Delete client configuration files
            client_config_manager.delete_client_configs(username)
            
            # Update server configurations
            config_generator.update_server_configs()
            
            return jsonify({
                'success': True,
                'message': f'User {username} deleted successfully'
            })
        else:
            return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v2/storage/files/<username>/download', methods=['GET'])
@require_auth
def download_configs(username):
    """Download user configurations (real functionality)."""
    try:
        users = user_storage.load_users()
        user = users.get(username)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Generate all client configurations
        configs = config_generator.generate_client_configs(username, user)
        
        return jsonify({
            'success': True,
            'username': username,
            'configs': configs
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v2/storage/files/<username>/qrcode/<protocol>', methods=['GET'])
@require_auth
def get_qrcode(username, protocol):
    """Generate QR code for mobile clients (PNG image)."""
    try:
        import qrcode
        from io import BytesIO
        
        users = user_storage.load_users()
        user = users.get(username)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Generate configurations
        configs = config_generator.generate_client_configs(username, user)
        
        # Get the appropriate link/config for QR code
        qr_data = None
        if protocol == 'xray-xtls':
            qr_data = configs.get('xray_xtls_link')
        elif protocol == 'xray-ws':
            qr_data = configs.get('xray_ws_link')
        elif protocol == 'trojan':
            qr_data = configs.get('trojan_link')
        elif protocol == 'hysteria2':
            qr_data = configs.get('hysteria2_link')
        elif protocol == 'wireguard':
            qr_data = configs.get('wireguard_conf')
        elif protocol == 'shadowtls':
            qr_data = configs.get('shadowtls_json')
        elif protocol == 'tuic':
            qr_data = configs.get('tuic_json')
        
        if not qr_data:
            return jsonify({'error': 'Protocol not supported or not configured'}), 400
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save to BytesIO
        img_io = BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)
        
        return send_file(img_io, mimetype='image/png')
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v2/storage/files/<username>/qrcodes', methods=['GET'])
@require_auth
def get_all_qrcodes(username):
    """Get all QR codes for a user as base64 encoded images."""
    try:
        users = user_storage.load_users()
        user = users.get(username)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Generate all QR codes
        qr_codes = client_config_manager.get_qr_codes(username, user)
        
        return jsonify({
            'success': True,
            'username': username,
            'qr_codes': qr_codes
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v2/storage/status', methods=['GET'])
@require_auth
def get_status():
    """Get system and service status."""
    try:
        service_status = service_manager.get_service_status()
        users = user_storage.load_users()
        
        return jsonify({
            'success': True,
            'services': service_status,
            'stats': {
                'total_users': len(users),
                'active_users': sum(1 for u in users.values() if u.is_active)
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v2/storage/backup', methods=['POST'])
@require_auth
def create_backup():
    """Create a backup of all configurations."""
    try:
        data = request.get_json() or {}
        description = data.get('description', '')
        
        backup_name = backup_manager.create_backup(description)
        
        return jsonify({
            'success': True,
            'message': 'Backup created successfully',
            'backup_name': backup_name
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v2/storage/backup', methods=['GET'])
@require_auth
def list_backups():
    """List all available backups."""
    try:
        backups = backup_manager.list_backups()
        
        return jsonify({
            'success': True,
            'backups': backups
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v2/storage/backup/<backup_name>', methods=['DELETE'])
@require_auth
def delete_backup(backup_name):
    """Delete a specific backup."""
    try:
        success = backup_manager.delete_backup(backup_name)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Backup {backup_name} deleted successfully'
            })
        else:
            return jsonify({'error': 'Failed to delete backup'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v2/storage/backup/<backup_name>/restore', methods=['POST'])
@require_auth
def restore_backup(backup_name):
    """Restore configurations from a backup."""
    try:
        success = backup_manager.restore_backup(backup_name)
        
        if success:
            # Reload all services after restore
            for service in ['xray', 'trojan', 'singbox', 'wireguard']:
                service_manager.reload_service(service)
            
            return jsonify({
                'success': True,
                'message': f'Backup {backup_name} restored successfully'
            })
        else:
            return jsonify({'error': 'Failed to restore backup'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v2/storage/backup/<backup_name>/download', methods=['GET'])
@require_auth
def download_backup(backup_name):
    """Download a backup file."""
    try:
        backup_path = backup_manager.export_backup(backup_name)
        
        if backup_path:
            return send_file(backup_path, as_attachment=True, download_name=backup_name)
        else:
            return jsonify({'error': 'Backup not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v2/storage/services/<service_name>/reload', methods=['POST'])
@require_auth
def reload_service(service_name):
    """Reload a specific VPN service."""
    try:
        success = service_manager.reload_service(service_name)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Service {service_name} reloaded successfully'
            })
        else:
            return jsonify({'error': f'Failed to reload service {service_name}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v2/storage/configs/update', methods=['POST'])
@require_auth
def update_all_configs():
    """Update all server configurations and reload services."""
    try:
        # Update all server configs
        success = config_generator.update_server_configs()
        
        if not success:
            return jsonify({'error': 'Failed to update configurations'}), 500
        
        # Reload all services
        reload_results = {}
        for service in ['xray', 'trojan', 'singbox', 'wireguard']:
            reload_results[service] = service_manager.reload_service(service)
        
        return jsonify({
            'success': True,
            'message': 'All configurations updated and services reloaded',
            'reload_results': reload_results
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v2/storage/endpoints', methods=['GET'])
@require_auth
def get_endpoints():
    """Get current obfuscated endpoints."""
    try:
        endpoints = get_current_endpoints()
        
        # Calculate endpoint age if available
        age_info = None
        if endpoint_manager and endpoints:
            age = endpoint_manager.get_endpoint_age(endpoints)
            if age:
                age_info = {
                    'days': age.days,
                    'hours': age.seconds // 3600,
                    'should_rotate': endpoint_manager.should_rotate(endpoints)
                }
        
        return jsonify({
            'success': True,
            'endpoints': endpoints,
            'age': age_info
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v2/storage/endpoints/rotate', methods=['POST'])
@require_auth
def rotate_endpoints():
    """Rotate obfuscated endpoints."""
    try:
        if not endpoint_manager:
            return jsonify({'error': 'Endpoint manager not available'}), 500
        
        data = request.get_json() or {}
        force = data.get('force', False)
        
        new_endpoints = endpoint_manager.rotate_endpoints(force=force)
        
        if new_endpoints is None:
            return jsonify({
                'success': False,
                'message': 'Endpoints are still fresh, use force=true to rotate anyway'
            })
        
        return jsonify({
            'success': True,
            'message': 'Endpoints rotated successfully',
            'endpoints': new_endpoints,
            'warning': 'Remember to update Caddyfile and restart Caddy container'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Ensure data directories exist
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    # Run Flask app
    app.run(host='0.0.0.0', port=8010, debug=False)
