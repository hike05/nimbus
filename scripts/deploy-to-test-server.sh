#!/bin/bash

# Quick deployment script for test server
# Usage: ./scripts/deploy-to-test-server.sh [user@host] [path]

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Default values
SERVER="${1:-root@vov.sneakernet.top}"
REMOTE_PATH="${2:-/root/stealth-vpn-server}"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Deploy Migration Scripts to Test Server               ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo
echo "Target server: $SERVER"
echo "Remote path: $REMOTE_PATH"
echo

# Check if we can connect
echo -e "${BLUE}Testing SSH connection...${NC}"
if ! ssh -o ConnectTimeout=5 "$SERVER" "echo 'Connection OK'" 2>/dev/null; then
    echo -e "${YELLOW}Warning: Cannot connect to server${NC}"
    echo "Please check:"
    echo "  - Server is accessible"
    echo "  - SSH key is configured"
    echo "  - Server address is correct"
    exit 1
fi
echo -e "${GREEN}✓ SSH connection successful${NC}"
echo

# Copy migration scripts
echo -e "${BLUE}Copying migration scripts...${NC}"
ssh "$SERVER" "mkdir -p $REMOTE_PATH/scripts"

scp scripts/migrate-to-new-version.sh "$SERVER:$REMOTE_PATH/scripts/"
scp scripts/rollback-migration.sh "$SERVER:$REMOTE_PATH/scripts/"
scp scripts/test-migration.sh "$SERVER:$REMOTE_PATH/scripts/"

echo -e "${GREEN}✓ Scripts copied${NC}"
echo

# Copy documentation
echo -e "${BLUE}Copying documentation...${NC}"
scp TEST_ON_SERVER.md "$SERVER:$REMOTE_PATH/"
scp QUICK_START_MIGRATION_TEST.md "$SERVER:$REMOTE_PATH/"
scp MIGRATION_TEST_CHECKLIST.md "$SERVER:$REMOTE_PATH/" 2>/dev/null || true

echo -e "${GREEN}✓ Documentation copied${NC}"
echo

# Set executable permissions
echo -e "${BLUE}Setting permissions...${NC}"
ssh "$SERVER" "chmod +x $REMOTE_PATH/scripts/*.sh"
echo -e "${GREEN}✓ Permissions set${NC}"
echo

# Display next steps
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              Deployment Complete!                          ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo
echo "Next steps:"
echo
echo "1. Connect to server:"
echo "   ssh $SERVER"
echo
echo "2. Navigate to directory:"
echo "   cd $REMOTE_PATH"
echo
echo "3. Run tests:"
echo "   ./scripts/test-migration.sh"
echo
echo "4. Review the guide:"
echo "   cat TEST_ON_SERVER.md"
echo
echo "5. Run migration:"
echo "   ./scripts/migrate-to-new-version.sh"
echo
