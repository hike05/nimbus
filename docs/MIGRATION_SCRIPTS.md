# Migration Scripts Documentation

This document describes the migration scripts available for upgrading existing Stealth VPN Server deployments.

## Overview

Three scripts are provided for migration management:

1. **migrate-to-new-version.sh** - Main migration script
2. **rollback-migration.sh** - Rollback to pre-migration state
3. **test-migration.sh** - Test migration script functionality

## Scripts

### 1. migrate-to-new-version.sh

**Purpose**: Migrate existing deployment to new version with improved configurations.

**Location**: `scripts/migrate-to-new-version.sh`

**What it does**:
- Creates automatic backup using BackupManager
- Stops all running services gracefully
- Updates docker-compose.yml with resource limits
- Fixes Caddyfile syntax issues
- Preserves SSL certificates and user data
- Rebuilds Docker images
- Restarts services
- Verifies all services are healthy

**Usage**:
```bash
./scripts/migrate-to-new-version.sh
```

**Requirements**:
- Existing Stealth VPN Server deployment
- Docker and Docker Compose installed
- Sufficient disk space for backups
- User with Docker permissions

**Output**:
- Migration log: `migration_TIMESTAMP.log`
- Backup files in `data/stealth-vpn/backups/`
- Pre-migration backups: `docker-compose.yml.pre-migration`, `config/Caddyfile.pre-migration`

### 2. rollback-migration.sh

**Purpose**: Rollback to pre-migration state if issues occur.

**Location**: `scripts/rollback-migration.sh`

**What it does**:
- Stops all running services
- Restores docker-compose.yml from backup
- Restores Caddyfile from backup
- Optionally restores configuration backup
- Rebuilds Docker images
- Restarts services
- Verifies services are running

**Usage**:
```bash
./scripts/rollback-migration.sh
```

**Requirements**:
- Pre-migration backup files must exist
- Docker and Docker Compose installed
- User with Docker permissions

**Output**:
- Rollback log: `rollback_TIMESTAMP.log`
- Restored system to pre-migration state

### 3. test-migration.sh

**Purpose**: Test migration script functionality without running actual migration.

**Location**: `scripts/test-migration.sh`

**What it does**:
- Checks if migration script exists and is executable
- Validates script syntax
- Checks for required functions
- Verifies backup functionality
- Tests rollback instructions
- Checks prerequisites (Docker, Python, etc.)
- Validates data directory structure

**Usage**:
```bash
./scripts/test-migration.sh
```

**Requirements**:
- None (can run on any system)

**Output**:
- Test results with pass/fail status
- Summary of test execution

## Migration Workflow

### Standard Migration

```
1. Run test script (optional)
   ./scripts/test-migration.sh

2. Run migration
   ./scripts/migrate-to-new-version.sh

3. Verify services
   docker compose ps
   ./scripts/health-check.sh

4. Test functionality
   - Access admin panel
   - Test VPN connectivity
```

### Migration with Rollback

```
1. Run migration
   ./scripts/migrate-to-new-version.sh

2. If issues occur, rollback
   ./scripts/rollback-migration.sh

3. Investigate issues
   - Check migration log
   - Review error messages
   - Check service logs

4. Fix issues and retry
   ./scripts/migrate-to-new-version.sh
```

## Key Features

### Automatic Backup

The migration script automatically creates a backup before making any changes:

- Uses BackupManager if admin container is running
- Falls back to manual tar.gz backup
- Includes all configurations, SSL certificates, and user data
- Stored in `data/stealth-vpn/backups/`

### Graceful Error Handling

Both scripts use `set +e` to handle errors gracefully:

- Tracks successful, failed, and warning steps
- Continues execution even if non-critical steps fail
- Provides detailed summary at the end
- Logs all operations to timestamped log files

### Service Verification

After migration or rollback:

- Checks each service status
- Reports running/stopped state
- Runs health checks if available
- Provides troubleshooting guidance

### Rollback Safety

Multiple rollback mechanisms:

- Pre-migration file backups (docker-compose.yml, Caddyfile)
- Configuration backups via BackupManager
- Manual rollback script
- Automatic rollback on critical failures

## Configuration Updates

### docker-compose.yml Updates

The migration script updates docker-compose.yml with:

- Resource limits (CPU and memory)
- Security improvements
- Health check adjustments
- Volume mount corrections

**Note**: Current version notes that manual updates may be needed. Review the new docker-compose.yml format in the repository.

### Caddyfile Updates

The migration script fixes Caddyfile syntax:

- Removes invalid `auto_https` directive
- Ensures HTTP/3 is properly configured
- Moves headers from global to site blocks
- Validates syntax using Caddy

## Preserved Data

The following data is always preserved during migration:

✅ **SSL Certificates**: All Let's Encrypt certificates  
✅ **User Data**: All user accounts and credentials  
✅ **VPN Configurations**: Xray, Trojan, Sing-box, WireGuard configs  
✅ **Client Configurations**: All generated client configs  
✅ **Environment Variables**: .env file is not modified  
✅ **Logs**: Existing log files are preserved  

## Troubleshooting

### Migration Fails to Start

**Check**:
- You're in the project root directory
- docker-compose.yml exists
- Docker is running: `docker ps`

### Backup Creation Fails

**Check**:
- Disk space: `df -h`
- Backup directory permissions
- Admin container status

### Services Don't Start After Migration

**Check**:
- Service logs: `docker compose logs -f`
- Resource usage: `docker stats`
- Configuration syntax: `docker compose config`

**Solution**: Use rollback script to restore previous state

### Rollback Fails

**Check**:
- Pre-migration backup files exist
- Backup directory is accessible
- Docker is running

**Manual Recovery**:
```bash
# Restore files manually
cp docker-compose.yml.pre-migration docker-compose.yml
cp config/Caddyfile.pre-migration config/Caddyfile

# Restore configuration
tar -xzf data/stealth-vpn/backups/backup_TIMESTAMP.tar.gz -C /

# Restart services
docker compose up -d
```

## Best Practices

1. **Test First**: Run test-migration.sh before actual migration
2. **Backup Manually**: Create additional manual backup before migration
3. **Low Traffic**: Migrate during low-traffic periods
4. **Monitor**: Watch logs and metrics after migration
5. **Keep Backups**: Maintain at least 3-5 recent backups
6. **Document Changes**: Note any custom modifications before migration

## Related Documentation

- [Migration Guide](MIGRATION_GUIDE.md) - Detailed migration instructions
- [Deployment Guide](../DEPLOYMENT.md) - Initial deployment instructions
- [Troubleshooting Guide](../TROUBLESHOOTING.md) - Common issues and solutions
- [Backup Documentation](BACKUP_ENHANCEMENTS.md) - Backup system details

## Script Maintenance

### Adding New Migration Steps

To add new migration steps to `migrate-to-new-version.sh`:

1. Create a new function for the step
2. Add error handling and logging
3. Call the function in the `main()` function
4. Update the confirmation prompt
5. Test thoroughly before deployment

### Updating Rollback Script

When adding new migration steps:

1. Add corresponding rollback function
2. Update rollback order (reverse of migration)
3. Test rollback with new changes
4. Update documentation

## Version History

- **v1.0** (2024-11-18): Initial migration scripts
  - Basic migration functionality
  - Backup and rollback support
  - Configuration updates
  - Service verification

## Support

For issues with migration scripts:

1. Check migration/rollback logs
2. Review service logs: `docker compose logs -f`
3. Consult troubleshooting section
4. Check related documentation
5. Report issues with log files attached
