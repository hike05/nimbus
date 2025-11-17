# Migration Guide

This guide explains how to migrate an existing Stealth VPN Server deployment to the new version with improved configurations.

## Overview

The migration script (`scripts/migrate-to-new-version.sh`) automates the process of upgrading your existing deployment with:

- Improved resource limits in docker-compose.yml
- Corrected Caddyfile syntax
- Preserved SSL certificates and user data
- Automatic backup before migration
- Rollback capability

## Prerequisites

Before running the migration:

1. **Backup Access**: Ensure you have access to create backups
2. **Docker Running**: Docker and Docker Compose must be installed and running
3. **Sufficient Disk Space**: At least 2GB free for backups and new images
4. **Admin Access**: Run as a user with Docker permissions (or root)

## Migration Process

### Step 1: Review Current Deployment

Check your current deployment status:

```bash
# Check running services
docker compose ps

# Check service health
./scripts/health-check.sh

# Check disk space
df -h
```

### Step 2: Run Migration Script

Execute the migration script:

```bash
./scripts/migrate-to-new-version.sh
```

The script will:

1. **Create Backup**: Automatically backup all configurations using BackupManager
2. **Stop Services**: Gracefully stop all running services
3. **Update Configurations**: 
   - Update docker-compose.yml with resource limits
   - Fix Caddyfile syntax issues
4. **Preserve Data**:
   - SSL certificates
   - User configurations
   - VPN service configs
5. **Rebuild Images**: Build new Docker images with latest changes
6. **Restart Services**: Start all services with new configurations
7. **Verify**: Check that all services are running correctly

### Step 3: Verify Migration

After migration completes, verify everything is working:

```bash
# Check service status
docker compose ps

# Check service logs
docker compose logs -f

# Run health checks
./scripts/health-check.sh

# Test admin panel access
curl -k https://your-domain.com/admin

# Test VPN connectivity with existing users
```

## What Gets Migrated

### Preserved Items

✅ **SSL Certificates**: All Let's Encrypt certificates are preserved  
✅ **User Data**: All user accounts and credentials remain intact  
✅ **VPN Configurations**: Xray, Trojan, Sing-box, WireGuard configs preserved  
✅ **Client Configurations**: All generated client configs remain available  
✅ **Environment Variables**: Your .env file is not modified  

### Updated Items

🔄 **docker-compose.yml**: Updated with resource limits and security improvements  
🔄 **Caddyfile**: Syntax corrections for Caddy v2 compatibility  
🔄 **Docker Images**: Rebuilt with latest code changes  

### Backup Items

💾 **Pre-migration Backup**: Automatic backup created before any changes  
💾 **docker-compose.yml.pre-migration**: Backup of original docker-compose.yml  
💾 **Caddyfile.pre-migration**: Backup of original Caddyfile  

## Rollback Procedure

If something goes wrong during migration, you can rollback:

### Automatic Rollback

The migration script creates backups automatically. If critical failures occur, it may attempt automatic rollback.

### Manual Rollback

If you need to manually rollback:

```bash
# 1. Stop current services
docker compose down

# 2. Restore docker-compose.yml
cp docker-compose.yml.pre-migration docker-compose.yml

# 3. Restore Caddyfile
cp config/Caddyfile.pre-migration config/Caddyfile

# 4. Restore configuration backup via admin panel
# Access admin panel and restore the latest backup
# Or manually:
# tar -xzf data/stealth-vpn/backups/backup_TIMESTAMP.tar.gz -C /

# 5. Restart services
docker compose up -d

# 6. Verify services
docker compose ps
./scripts/health-check.sh
```

## Troubleshooting

### Migration Fails to Start

**Problem**: Script exits immediately  
**Solution**: 
- Check you're in the project root directory
- Verify docker-compose.yml exists
- Ensure Docker is running: `docker ps`

### Backup Creation Fails

**Problem**: Cannot create backup  
**Solution**:
- Check disk space: `df -h`
- Verify backup directory permissions: `ls -la data/stealth-vpn/backups`
- Ensure admin container is running: `docker ps | grep admin`

### Services Fail to Start After Migration

**Problem**: Services don't start or are unhealthy  
**Solution**:
1. Check logs: `docker compose logs -f`
2. Check resource usage: `docker stats`
3. Verify configurations: `docker compose config`
4. If needed, rollback using manual procedure above

### Caddyfile Validation Fails

**Problem**: Caddyfile syntax errors  
**Solution**:
1. Review Caddyfile changes: `diff config/Caddyfile.pre-migration config/Caddyfile`
2. Restore original: `cp config/Caddyfile.pre-migration config/Caddyfile`
3. Manually apply fixes from new Caddyfile template
4. Validate: `docker compose exec caddy caddy validate --config /etc/caddy/Caddyfile`

### SSL Certificates Lost

**Problem**: SSL certificates not working after migration  
**Solution**:
- Certificates should be preserved automatically
- Check: `ls -la data/caddy/certificates`
- If missing, restore from backup or let Caddy regenerate them
- Caddy will automatically obtain new certificates on first run

### User Data Missing

**Problem**: Users or configurations missing  
**Solution**:
1. Check users.json: `cat data/stealth-vpn/configs/users.json`
2. Restore from backup via admin panel
3. Or manually restore: Use the backup created before migration

## Testing Migration (Staging)

Before migrating production, test on a staging environment:

### Create Staging Environment

```bash
# 1. Clone your production data to staging
rsync -av data/ staging-data/

# 2. Update staging docker-compose to use staging-data
# Edit docker-compose.yml to point to staging-data

# 3. Run migration on staging
./scripts/migrate-to-new-version.sh

# 4. Verify staging works correctly
./scripts/health-check.sh

# 5. Test VPN connectivity

# 6. If successful, proceed with production migration
```

## Post-Migration Checklist

After successful migration:

- [ ] All services are running: `docker compose ps`
- [ ] Health checks pass: `./scripts/health-check.sh`
- [ ] Admin panel accessible: `https://your-domain.com/admin`
- [ ] Existing users can connect via VPN
- [ ] SSL certificates are valid
- [ ] Logs show no errors: `docker compose logs`
- [ ] Resource usage is normal: `docker stats`
- [ ] Backup was created successfully
- [ ] Old backup files can be deleted (keep at least 3-5 recent backups)

## Migration Log

The migration script creates a detailed log file:

```bash
# View migration log
cat migration_TIMESTAMP.log

# Search for errors
grep ERROR migration_TIMESTAMP.log

# Search for warnings
grep WARNING migration_TIMESTAMP.log
```

## Cleanup After Successful Migration

Once you've verified everything works:

```bash
# Remove pre-migration backup files (optional)
rm docker-compose.yml.pre-migration
rm config/Caddyfile.pre-migration

# Clean up old Docker images (optional)
docker image prune -a

# Keep migration log for reference
# Keep at least one configuration backup
```

## Getting Help

If you encounter issues:

1. Check the migration log: `migration_TIMESTAMP.log`
2. Check service logs: `docker compose logs -f`
3. Review troubleshooting section above
4. Check project documentation in `docs/`
5. Rollback if necessary and report the issue

## Version Compatibility

This migration script is designed for:

- **From**: Initial deployment versions (pre-resource-limits)
- **To**: Current version with resource limits and Caddyfile fixes

If you're running a very old version, you may need to perform intermediate migrations.

## Best Practices

1. **Always backup before migration**: The script does this automatically, but manual backups are also recommended
2. **Test in staging first**: If possible, test migration on a staging environment
3. **Migrate during low-traffic periods**: Minimize impact on users
4. **Monitor after migration**: Watch logs and metrics for 24-48 hours
5. **Keep backups**: Maintain at least 3-5 recent backups
6. **Document custom changes**: If you've made custom modifications, document them before migration

## Automated Migration (Advanced)

For automated deployments, you can run migration non-interactively:

```bash
# Set environment variable to skip prompts
export MIGRATION_AUTO_CONFIRM=yes

# Run migration
./scripts/migrate-to-new-version.sh

# Check exit code
if [ $? -eq 0 ]; then
    echo "Migration successful"
else
    echo "Migration failed"
    # Trigger rollback or alert
fi
```

**Note**: Automated migration is not recommended for production without thorough testing.
