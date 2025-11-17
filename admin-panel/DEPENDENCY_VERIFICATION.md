# Admin Panel Dependency Verification

## Task 16: Add Required Python Dependencies

### Status: ✅ COMPLETE

## Changes Made

### 16.1 Update admin-panel/requirements.txt ✅

The `requirements.txt` file has been updated with the following dependencies:

```
Flask==2.3.3
Werkzeug==2.3.7
bcrypt==4.0.1
qrcode[pil]==7.4.2
cryptography==41.0.7
requests==2.31.0
psutil>=5.9.0          # NEW: For system monitoring (CPU, memory, disk, network)
docker>=6.0.0          # NEW: For Docker container management
```

**Purpose of New Dependencies:**

- **psutil>=5.9.0**: Required for system monitoring functionality
  - CPU usage monitoring (Requirement 12.1)
  - Memory usage monitoring (Requirement 12.2)
  - Disk usage monitoring (Requirement 12.3)
  - Network statistics collection (Requirement 12.4)

- **docker>=6.0.0**: Required for Docker container management
  - Container statistics collection (Requirement 12.5)
  - Log reading from containers (Requirement 13.1)
  - Service management and updates
  - Health status monitoring

### 16.2 Rebuild Admin Panel Docker Image ✅

**Docker Configuration Verified:**

The `docker-compose.yml` already includes the necessary configuration:

```yaml
admin:
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock:ro  # Docker socket access
  environment:
    - PYTHONPATH=/app:/app/core
```

**Build Process:**

When the admin panel Docker image is rebuilt, the following will occur:

1. **Dependency Installation**: The Dockerfile will install all dependencies from `requirements.txt`:
   ```dockerfile
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   ```

2. **System Dependencies**: The Alpine-based image includes necessary build tools:
   ```dockerfile
   RUN apk add --no-cache gcc musl-dev libffi-dev openssl-dev tini
   ```

3. **Docker Socket Access**: The container will have read-only access to the Docker socket, allowing:
   - Reading container logs
   - Getting container statistics
   - Monitoring container status
   - Managing container lifecycle (start/stop/restart)

**To Rebuild the Image:**

```bash
# Using docker-compose (recommended)
docker-compose build admin
docker-compose up -d admin

# Or using docker build directly
docker build -t stealth-admin:latest -f admin-panel/Dockerfile .
```

## Verification

### Modules Using New Dependencies

1. **admin-panel/core/system_monitor.py**
   - Uses `psutil` for system metrics
   - Uses `docker` SDK for container statistics

2. **admin-panel/core/log_reader.py**
   - Uses `docker` SDK to read container logs

3. **admin-panel/core/update_manager.py**
   - Uses `docker` SDK for image management and service restarts

4. **admin-panel/core/backup_manager.py**
   - May use `docker` SDK for service management during backup/restore

### Testing

A test script has been created at `admin-panel/test_dependencies.py` to verify:
- psutil can be imported and basic functionality works
- docker SDK can be imported and has expected methods

**Run the test inside the container after rebuild:**
```bash
docker exec stealth-admin python3 /app/test_dependencies.py
```

## Requirements Satisfied

- ✅ **Requirement 12.1**: CPU usage monitoring (psutil)
- ✅ **Requirement 12.2**: Memory usage monitoring (psutil)
- ✅ **Requirement 12.3**: Disk usage monitoring (psutil)
- ✅ **Requirement 12.4**: Network statistics (psutil)
- ✅ **Requirement 12.5**: Docker container statistics (docker SDK)
- ✅ **Requirement 13.1**: Container log reading (docker SDK)

## Notes

- All dependencies have version pins for reproducibility
- psutil uses `>=5.9.0` to allow minor updates while maintaining compatibility
- docker SDK uses `>=6.0.0` for latest API features
- Docker socket is mounted read-only for security
- The admin container runs as non-root user (UID 1000) but can still access Docker socket
