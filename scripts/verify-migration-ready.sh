#!/bin/bash

# Quick verification script for migration readiness

echo "=== Migration Readiness Check ==="
echo

# Check 1: Migration script exists
if [[ -f scripts/migrate-to-new-version.sh ]]; then
    echo "✓ Migration script exists"
else
    echo "✗ Migration script missing"
    exit 1
fi

# Check 2: Script is executable
if [[ -x scripts/migrate-to-new-version.sh ]]; then
    echo "✓ Migration script is executable"
else
    echo "✗ Migration script not executable"
    exit 1
fi

# Check 3: Syntax check
if bash -n scripts/migrate-to-new-version.sh 2>/dev/null; then
    echo "✓ Migration script syntax valid"
else
    echo "✗ Migration script has syntax errors"
    exit 1
fi

# Check 4: Rollback script exists
if [[ -f scripts/rollback-migration.sh ]] && [[ -x scripts/rollback-migration.sh ]]; then
    echo "✓ Rollback script ready"
else
    echo "✗ Rollback script missing or not executable"
fi

# Check 5: Documentation exists
if [[ -f docs/MIGRATION_GUIDE.md ]]; then
    echo "✓ Migration guide available"
else
    echo "⚠ Migration guide missing"
fi

# Check 6: Required functions in migration script
echo
echo "Checking required functions..."
required_funcs=("create_backup" "stop_services" "update_docker_compose" "update_caddyfile" "start_services")
missing=0

for func in "${required_funcs[@]}"; do
    if grep -q "^${func}()" scripts/migrate-to-new-version.sh; then
        echo "  ✓ $func"
    else
        echo "  ✗ $func missing"
        ((missing++))
    fi
done

if [[ $missing -eq 0 ]]; then
    echo "✓ All required functions present"
else
    echo "✗ $missing function(s) missing"
    exit 1
fi

echo
echo "=== Migration scripts are ready! ==="
echo
echo "To test on server:"
echo "  1. Copy scripts to server: scp -r scripts/ user@server:/path/to/stealth-vpn-server/"
echo "  2. SSH to server: ssh user@server"
echo "  3. Run migration: cd /path/to/stealth-vpn-server && ./scripts/migrate-to-new-version.sh"
echo
