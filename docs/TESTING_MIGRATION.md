# Testing Migration on Server

This guide provides step-by-step instructions for testing the migration script on your test server.

## Prerequisites

Before testing migration:

- [ ] Test server with existing Stealth VPN deployment
- [ ] SSH access to the server
- [ ] Backup of current deployment (just in case)
- [ ] At least 2GB free disk space

## Step 1: Prepare Local Files

On your local machine, verify migration scripts are ready:

```bash
# Run verification script
./scripts/verify-migration-ready.sh

# Expected output: All checks should pass ✓
```

## Step 2: Copy Files to Server

Copy the migration scripts and updated files to your server:

```bash
# Set your server details
SERVER_USER="your-username"
SERVER_HOST="your-server-ip-or-domain"
SERVER_PATH="/home/$SERVER_USER/stealth-vpn-server"

# Copy migration scripts
scp scripts/migrate-to-new-version.sh \
    scripts/rollback-migration.sh \
    scripts/verify-migration-ready.sh \
    $SERVER_USER@$SERVER_HOST:$SERVER_PATH/scripts/

# Copy documentation
scp docs/MIGRATION_GUIDE.md \
    docs/MIGRATION_SCRIPTS.md \
    $SERVER_USER@$SERVER_HOST:$SERVER_PATH/docs/

# Make scripts executable on server
ssh $SERVER_USER@$SERVER_HOST "chmod +x $SERVER_PATH/scripts/*.sh"
```

## Step 3: Connect to Server

```bash
ssh $SERVER_USER@$SERVER_HOST
cd stealth-vpn-server
```

## Step 4: Pre-Migration Checks

Before running migration, check current state:

```bash
# Check current services
docker compose ps

# Check disk space
df -h

# Check current docker-compose.yml
head -20 docker-compose.yml

# Check Caddyfile
head -20 config/Caddyfile

# Verify backup directory exists
ls -la data/stealth-vpn/backups/
```

## Step 5: Create Manual Backup (Safety)

Create an additional manual backup before migration:

```bash
# Create backup directory
mkdir -p ~/backups

# Backup entire deployment
tar -czf ~/backups/stealth-vpn-pre-migration-$(date +%Y%m%d_%H%M%S).tar.gz \
    docker-compose.yml \
    config/Caddyfile \
    .env \
    data/stealth-vpn/configs/ \
    data/caddy/certificates/

# Verify backup was created
ls -lh ~/backups/
```

## Step 6: Run Migration (Dry Run First)

First, let's review what the migration will do:

```bash
# Review migration script
less scripts/migrate-to-new-version.sh

# Check what will be updated
grep -A 5 "update_docker_compose\|update_caddyfile" scripts/migrate-to-new-version.sh
```

## Step 7: Run Actual Migration

Now run the migration:

```bash
# Run migration script
./scripts/migrate-to-new-version.sh

# The script will:
# 1. Ask for confirmation - type 'y' to continue
# 2. Create automatic backup
# 3. Stop services
# 4. Update configurations
# 5. Rebuild images
# 6. Start services
# 7. Verify everything works
```

**Expected Output:**
```
╔════════════════════════════════════════════════════════════╗
║     Stealth VPN Server Migration to New Version           ║
╚════════════════════════════════════════════════════════════╝

This script will:
  • Create a backup of your current configuration
  • Stop running services
  • Update docker-compose.yml with new resource limits
  • Update Caddyfile with corrected syntax
  • Preserve SSL certificates and user data
  • Rebuild Docker images
  • Restart services

Do you want to continue? (y/n): y

[INFO] Starting migration process...
[INFO] Creating backup of current configuration...
[SUCCESS] ✓ Backup created: backup_20241118_012345.tar.gz
...
```

## Step 8: Verify Migration Success

After migration completes, verify everything works:

```bash
# Check service status
docker compose ps

# All services should show "Up" and "healthy"
# Example output:
# NAME              STATUS          PORTS
# stealth-admin     Up (healthy)    8010/tcp
# stealth-caddy     Up (healthy)    80/tcp, 443/tcp, 443/udp
# stealth-xray      Up (healthy)    
# stealth-trojan    Up (healthy)    
# stealth-singbox   Up (healthy)    
# stealth-wireguard Up (healthy)    

# Check service logs
docker compose logs --tail=50

# Run health check
./scripts/health-check.sh

# Check resource usage
docker stats --no-stream

# Verify admin panel access
curl -k https://your-domain.com/admin
# Should return HTML page

# Check SSL certificates
ls -la data/caddy/certificates/

# Verify user data
cat data/stealth-vpn/configs/users.json
```

## Step 9: Test VPN Connectivity

Test that existing VPN users can still connect:

```bash
# Check VPN service logs
docker compose logs xray --tail=20
docker compose logs trojan --tail=20
docker compose logs singbox --tail=20
docker compose logs wireguard --tail=20

# From client machine, test VPN connection
# (Use existing client configuration)
```

## Step 10: Review Migration Log

Check the migration log for any warnings or errors:

```bash
# Find migration log
ls -lt migration_*.log | head -1

# View migration log
cat migration_*.log

# Check for errors
grep ERROR migration_*.log

# Check for warnings
grep WARNING migration_*.log
```

## If Migration Fails

If migration fails or services don't start properly:

### Option 1: Use Rollback Script

```bash
# Run rollback script
./scripts/rollback-migration.sh

# Follow prompts to restore previous state
```

### Option 2: Manual Rollback

```bash
# Stop services
docker compose down

# Restore docker-compose.yml
cp docker-compose.yml.pre-migration docker-compose.yml

# Restore Caddyfile
cp config/Caddyfile.pre-migration config/Caddyfile

# Restart services
docker compose up -d

# Verify services
docker compose ps
```

### Option 3: Restore from Manual Backup

```bash
# Stop services
docker compose down

# Extract backup
cd ~
tar -xzf backups/stealth-vpn-pre-migration-*.tar.gz -C /home/$USER/stealth-vpn-server/

# Restart services
cd stealth-vpn-server
docker compose up -d
```

## Common Issues and Solutions

### Issue: Services fail to start after migration

**Check:**
```bash
# Check logs
docker compose logs

# Check resource limits
docker stats

# Check configuration syntax
docker compose config
```

**Solution:**
- Review error messages in logs
- Check if resource limits are too restrictive
- Verify configuration files are valid

### Issue: Caddyfile validation fails

**Check:**
```bash
# Validate Caddyfile
docker compose exec caddy caddy validate --config /etc/caddy/Caddyfile
```

**Solution:**
```bash
# Restore original Caddyfile
cp config/Caddyfile.pre-migration config/Caddyfile

# Restart Caddy
docker compose restart caddy
```

### Issue: SSL certificates missing

**Check:**
```bash
ls -la data/caddy/certificates/
```

**Solution:**
- Certificates should be preserved automatically
- If missing, Caddy will regenerate them on next start
- Wait 2-3 minutes for certificate generation

### Issue: User data lost

**Check:**
```bash
cat data/stealth-vpn/configs/users.json
```

**Solution:**
```bash
# Restore from backup
./scripts/rollback-migration.sh
# Select 'y' when asked to restore configuration backup
```

## Post-Migration Checklist

After successful migration:

- [ ] All services running and healthy
- [ ] Admin panel accessible
- [ ] VPN connectivity working for existing users
- [ ] SSL certificates valid
- [ ] No errors in logs
- [ ] Resource usage normal
- [ ] Backup created successfully
- [ ] Migration log reviewed

## Cleanup

After verifying everything works for 24-48 hours:

```bash
# Remove pre-migration backup files (optional)
rm docker-compose.yml.pre-migration
rm config/Caddyfile.pre-migration

# Keep migration log for reference
# Keep at least one configuration backup

# Clean up old Docker images (optional)
docker image prune -a
```

## Reporting Issues

If you encounter issues during testing:

1. **Collect Information:**
   ```bash
   # Save migration log
   cat migration_*.log > migration-issue.log
   
   # Save service logs
   docker compose logs > service-logs.txt
   
   # Save system info
   docker compose ps > service-status.txt
   docker stats --no-stream > resource-usage.txt
   ```

2. **Create Issue Report:**
   - Migration log
   - Service logs
   - Error messages
   - Steps to reproduce
   - Server specifications

3. **Rollback if Needed:**
   - Use rollback script to restore working state
   - Document what went wrong
   - Report issue with logs

## Success Criteria

Migration is successful when:

✅ All services show "Up (healthy)" status  
✅ Admin panel is accessible  
✅ Existing VPN users can connect  
✅ SSL certificates are valid  
✅ No errors in service logs  
✅ Resource usage is normal  
✅ Backup was created successfully  

## Next Steps

After successful migration on test server:

1. Monitor for 24-48 hours
2. Test all VPN protocols
3. Verify backup/restore functionality
4. Document any issues encountered
5. Plan production migration
6. Update runbook with lessons learned

## Production Migration

Once testing is successful:

1. Schedule maintenance window
2. Notify users of brief downtime
3. Follow same migration procedure
4. Monitor closely for first 24 hours
5. Keep rollback option ready

## Support

For help with migration:

- Review [Migration Guide](MIGRATION_GUIDE.md)
- Check [Migration Scripts Documentation](MIGRATION_SCRIPTS.md)
- Review [Troubleshooting Guide](../TROUBLESHOOTING.md)
- Check migration logs for detailed error messages
