# Migration Test Checklist

Quick checklist for testing migration on server.

## Pre-Migration

- [ ] Server accessible via SSH
- [ ] Current deployment is working
- [ ] At least 2GB free disk space
- [ ] Manual backup created: `tar -czf ~/backup-$(date +%Y%m%d).tar.gz docker-compose.yml config/ data/ .env`

## Copy Files to Server

```bash
# Set variables
SERVER="user@your-server"
PATH="/path/to/stealth-vpn-server"

# Copy scripts
scp scripts/migrate-to-new-version.sh scripts/rollback-migration.sh $SERVER:$PATH/scripts/
ssh $SERVER "chmod +x $PATH/scripts/*.sh"
```

## Run Migration

```bash
# On server
cd /path/to/stealth-vpn-server

# Check current status
docker compose ps

# Run migration
./scripts/migrate-to-new-version.sh
```

## Verify Success

- [ ] Migration completed without errors
- [ ] All services show "Up (healthy)": `docker compose ps`
- [ ] Admin panel accessible: `curl -k https://your-domain.com/admin`
- [ ] No errors in logs: `docker compose logs --tail=50`
- [ ] SSL certificates present: `ls data/caddy/certificates/`
- [ ] User data intact: `cat data/stealth-vpn/configs/users.json`
- [ ] VPN connectivity works (test with client)

## If Issues Occur

```bash
# Rollback
./scripts/rollback-migration.sh

# Or manual rollback
docker compose down
cp docker-compose.yml.pre-migration docker-compose.yml
cp config/Caddyfile.pre-migration config/Caddyfile
docker compose up -d
```

## Post-Migration

- [ ] Monitor logs for 30 minutes: `docker compose logs -f`
- [ ] Check resource usage: `docker stats`
- [ ] Test all VPN protocols
- [ ] Review migration log: `cat migration_*.log`
- [ ] Document any issues

## Success Criteria

✅ All services healthy  
✅ Admin panel works  
✅ VPN connectivity works  
✅ No errors in logs  
✅ Backup created  

## Files Created

- Migration log: `migration_TIMESTAMP.log`
- Backup: `data/stealth-vpn/backups/backup_TIMESTAMP.tar.gz`
- Pre-migration backups: `docker-compose.yml.pre-migration`, `config/Caddyfile.pre-migration`

## Rollback if Needed

If anything goes wrong, rollback is safe and easy:
```bash
./scripts/rollback-migration.sh
```

## Documentation

- Full guide: [docs/TESTING_MIGRATION.md](docs/TESTING_MIGRATION.md)
- Migration guide: [docs/MIGRATION_GUIDE.md](docs/MIGRATION_GUIDE.md)
- Scripts docs: [docs/MIGRATION_SCRIPTS.md](docs/MIGRATION_SCRIPTS.md)
