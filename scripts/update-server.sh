#!/bin/bash

# Update test server with latest changes
# Usage: ./scripts/update-server.sh [user@host] [path]

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Default values
SERVER="${1:-root@vov.sneakernet.top}"
REMOTE_PATH="${2:-/root/stealth-vpn-server}"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║          Update Server with Latest Changes                ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo
echo "Target server: $SERVER"
echo "Remote path: $REMOTE_PATH"
echo

# Step 1: Pull latest changes on server
echo -e "${BLUE}[1/4] Pulling latest changes from git...${NC}"
ssh "$SERVER" "cd $REMOTE_PATH && git pull origin main"
echo -e "${GREEN}✓ Git pull complete${NC}"
echo

# Step 2: Check current status
echo -e "${BLUE}[2/4] Checking current server status...${NC}"
ssh "$SERVER" "cd $REMOTE_PATH && docker compose ps"
echo

# Step 3: Run status check
echo -e "${BLUE}[3/4] Running status check...${NC}"
ssh "$SERVER" "cd $REMOTE_PATH && bash scripts/check-server-status.sh"
echo

# Step 4: Show next steps
echo -e "${BLUE}[4/4] Next steps${NC}"
echo
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              Server Updated Successfully!                  ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo
echo "Server is now up to date with latest changes."
echo
echo "To apply the changes, you can:"
echo
echo "1. Run migration (recommended):"
echo "   ssh $SERVER"
echo "   cd $REMOTE_PATH"
echo "   ./scripts/migrate-to-new-version.sh"
echo
echo "2. Or manually rebuild and restart:"
echo "   ssh $SERVER"
echo "   cd $REMOTE_PATH"
echo "   docker compose down"
echo "   docker compose build"
echo "   docker compose up -d"
echo
echo "3. Check status after changes:"
echo "   ./scripts/check-server-status.sh"
echo
