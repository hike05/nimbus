#!/bin/bash

# Quick script to deploy migration files to server

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}=== Deploy Migration Scripts to Server ===${NC}"
echo

# Check if server details are provided
if [[ -z "$1" ]]; then
    echo -e "${YELLOW}Usage: $0 user@server:/path/to/stealth-vpn-server${NC}"
    echo
    echo "Example:"
    echo "  $0 root@vov.sneakernet.top:/root/stealth-vpn-server"
    echo
    exit 1
fi

SERVER_PATH="$1"

# Verify local files exist
echo "Checking local files..."
if [[ ! -f scripts/migrate-to-new-version.sh ]]; then
    echo -e "${RED}Error: Migration script not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Local files ready"
echo

# Copy migration scripts
echo "Copying migration scripts..."
scp scripts/migrate-to-new-version.sh \
    scripts/rollback-migration.sh \
    scripts/verify-migration-ready.sh \
    "${SERVER_PATH}/scripts/" || {
    echo -e "${RED}Failed to copy scripts${NC}"
    exit 1
}

echo -e "${GREEN}✓${NC} Scripts copied"
echo

# Copy documentation
echo "Copying documentation..."
scp docs/MIGRATION_GUIDE.md \
    docs/MIGRATION_SCRIPTS.md \
    docs/TESTING_MIGRATION.md \
    "${SERVER_PATH}/docs/" || {
    echo -e "${YELLOW}Warning: Failed to copy documentation${NC}"
}

echo -e "${GREEN}✓${NC} Documentation copied"
echo

# Make scripts executable on server
echo "Making scripts executable..."
SERVER_HOST=$(echo "$SERVER_PATH" | cut -d: -f1)
SERVER_DIR=$(echo "$SERVER_PATH" | cut -d: -f2)

ssh "$SERVER_HOST" "chmod +x ${SERVER_DIR}/scripts/migrate-to-new-version.sh ${SERVER_DIR}/scripts/rollback-migration.sh ${SERVER_DIR}/scripts/verify-migration-ready.sh" || {
    echo -e "${YELLOW}Warning: Failed to set executable permissions${NC}"
}

echo -e "${GREEN}✓${NC} Scripts are executable"
echo

# Display next steps
echo -e "${GREEN}=== Deployment Complete ===${NC}"
echo
echo "Next steps:"
echo "  1. SSH to server:"
echo "     ssh $SERVER_HOST"
echo
echo "  2. Navigate to project directory:"
echo "     cd $SERVER_DIR"
echo
echo "  3. Verify migration readiness:"
echo "     ./scripts/verify-migration-ready.sh"
echo
echo "  4. Run migration:"
echo "     ./scripts/migrate-to-new-version.sh"
echo
echo "See MIGRATION_TEST_CHECKLIST.md for detailed testing steps."
echo
