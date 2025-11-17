#!/bin/bash

# Quick status check for test server
# Run this on the server: ./scripts/check-server-status.sh

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║           Server Status Check                              ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo

# 1. Check Docker services
echo -e "${BLUE}[1/7] Docker Services Status${NC}"
docker compose ps
echo

# 2. Check service health
echo -e "${BLUE}[2/7] Service Health${NC}"
docker compose ps --format "table {{.Name}}\t{{.Status}}" | grep -E "Up|healthy|unhealthy" || echo "No services running"
echo

# 3. Check recent logs (last 20 lines)
echo -e "${BLUE}[3/7] Recent Logs (last 20 lines)${NC}"
docker compose logs --tail=20 --no-log-prefix 2>&1 | tail -20
echo

# 4. Check admin panel
echo -e "${BLUE}[4/7] Admin Panel Check${NC}"
if curl -k -s -o /dev/null -w "%{http_code}" https://localhost/api/v2/storage/login | grep -q "200\|401\|405"; then
    echo -e "${GREEN}✓ Admin panel responding${NC}"
else
    echo -e "${RED}✗ Admin panel not responding${NC}"
fi
echo

# 5. Check users
echo -e "${BLUE}[5/7] Users Configuration${NC}"
if [ -f "data/stealth-vpn/configs/users.json" ]; then
    echo "Users found:"
    cat data/stealth-vpn/configs/users.json | python3 -m json.tool 2>/dev/null | grep -E "username|enabled" | head -10
else
    echo -e "${YELLOW}No users.json found${NC}"
fi
echo

# 6. Check disk space
echo -e "${BLUE}[6/7] Disk Space${NC}"
df -h / | tail -1
echo

# 7. Check recent changes
echo -e "${BLUE}[7/7] Recent File Changes (last 24h)${NC}"
find . -type f -mtime -1 -not -path "*/\.*" -not -path "*/logs/*" 2>/dev/null | head -10 || echo "No recent changes"
echo

echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              Status Check Complete                         ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
