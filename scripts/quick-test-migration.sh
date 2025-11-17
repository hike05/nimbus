#!/bin/bash

# Quick test and deploy script for migration
# This script runs all tests locally and optionally deploys to server

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Quick Migration Test & Deploy                         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo

# Step 1: Run local tests
echo -e "${BLUE}Step 1: Running local tests...${NC}"
echo
if ./scripts/test-migration.sh; then
    echo
    echo -e "${GREEN}✓ All local tests passed!${NC}"
else
    echo
    echo -e "${RED}✗ Some tests failed. Please review the output above.${NC}"
    exit 1
fi

echo
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo

# Step 2: Ask about deployment
echo -e "${YELLOW}Do you want to deploy to test server now?${NC}"
echo "This will copy migration scripts to vov.sneakernet.top"
echo
read -p "Deploy to server? (y/n): " DEPLOY

if [[ ! "$DEPLOY" =~ ^[Yy]$ ]]; then
    echo
    echo -e "${BLUE}Deployment skipped.${NC}"
    echo
    echo "To deploy manually later, run:"
    echo "  ./scripts/deploy-to-test-server.sh root@vov.sneakernet.top"
    echo
    exit 0
fi

echo
echo -e "${BLUE}Step 2: Deploying to test server...${NC}"
echo

# Step 3: Deploy to server
if ./scripts/deploy-to-test-server.sh root@vov.sneakernet.top; then
    echo
    echo -e "${GREEN}✓ Deployment successful!${NC}"
else
    echo
    echo -e "${RED}✗ Deployment failed. Please check the output above.${NC}"
    exit 1
fi

echo
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo

# Step 4: Display next steps
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              Ready for Server Testing!                     ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo
echo "Next steps on the server:"
echo
echo "1. Connect to server:"
echo -e "   ${BLUE}ssh root@vov.sneakernet.top${NC}"
echo
echo "2. Navigate to directory:"
echo -e "   ${BLUE}cd /root/stealth-vpn-server${NC}"
echo
echo "3. Run tests on server:"
echo -e "   ${BLUE}./scripts/test-migration.sh${NC}"
echo
echo "4. Review the guide:"
echo -e "   ${BLUE}cat TEST_ON_SERVER.md${NC}"
echo
echo "5. Create manual backup (recommended):"
echo -e "   ${BLUE}tar -czf ~/backup-\$(date +%Y%m%d_%H%M%S).tar.gz docker-compose.yml config/ data/ .env${NC}"
echo
echo "6. Run migration:"
echo -e "   ${BLUE}./scripts/migrate-to-new-version.sh${NC}"
echo
echo "7. Verify results:"
echo -e "   ${BLUE}docker compose ps${NC}"
echo -e "   ${BLUE}docker compose logs --tail=50${NC}"
echo
echo -e "${YELLOW}⚠ Important:${NC}"
echo "  • Migration will take ~5-10 minutes"
echo "  • Services will be briefly unavailable"
echo "  • Automatic backup will be created"
echo "  • Rollback is available if needed"
echo
echo "Documentation:"
echo "  • Quick guide: TEST_ON_SERVER.md"
echo "  • Full guide: docs/MIGRATION_GUIDE.md"
echo "  • Test results: MIGRATION_TEST_RESULTS.md"
echo
