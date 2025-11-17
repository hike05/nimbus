#!/bin/bash

# Test script for migration functionality
# This script validates the migration script without actually running it on production

set +e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results
TESTS_PASSED=0
TESTS_FAILED=0
declare -a FAILED_TESTS=()

# Test functions
test_pass() {
    echo -e "${GREEN}✓ PASS:${NC} $1"
    ((TESTS_PASSED++))
}

test_fail() {
    echo -e "${RED}✗ FAIL:${NC} $1"
    ((TESTS_FAILED++))
    FAILED_TESTS+=("$1")
}

test_info() {
    echo -e "${BLUE}ℹ INFO:${NC} $1"
}

test_warn() {
    echo -e "${YELLOW}⚠ WARN:${NC} $1"
}

# Test 1: Check if migration script exists
test_migration_script_exists() {
    test_info "Test 1: Checking if migration script exists..."
    
    if [[ -f scripts/migrate-to-new-version.sh ]]; then
        test_pass "Migration script exists"
    else
        test_fail "Migration script not found"
    fi
}

# Test 2: Check if migration script is executable
test_migration_script_executable() {
    test_info "Test 2: Checking if migration script is executable..."
    
    if [[ -x scripts/migrate-to-new-version.sh ]]; then
        test_pass "Migration script is executable"
    else
        test_fail "Migration script is not executable"
    fi
}

# Test 3: Check script syntax
test_migration_script_syntax() {
    test_info "Test 3: Checking migration script syntax..."
    
    if bash -n scripts/migrate-to-new-version.sh 2>/dev/null; then
        test_pass "Migration script syntax is valid"
    else
        test_fail "Migration script has syntax errors"
    fi
}

# Test 4: Check for required functions
test_required_functions() {
    test_info "Test 4: Checking for required functions in migration script..."
    
    local required_functions=(
        "create_backup"
        "stop_services"
        "update_docker_compose"
        "update_caddyfile"
        "preserve_ssl_certificates"
        "preserve_user_data"
        "start_services"
        "verify_services"
    )
    
    local missing_functions=()
    
    for func in "${required_functions[@]}"; do
        if grep -q "^${func}()" scripts/migrate-to-new-version.sh; then
            test_info "  ✓ Function '$func' found"
        else
            test_warn "  ✗ Function '$func' not found"
            missing_functions+=("$func")
        fi
    done
    
    if [[ ${#missing_functions[@]} -eq 0 ]]; then
        test_pass "All required functions present"
    else
        test_fail "Missing functions: ${missing_functions[*]}"
    fi
}

# Test 5: Check for backup functionality
test_backup_functionality() {
    test_info "Test 5: Checking backup functionality..."
    
    if grep -q "BackupManager" scripts/migrate-to-new-version.sh; then
        test_pass "Uses BackupManager for backups"
    else
        test_warn "BackupManager not referenced (may use manual backup)"
    fi
    
    if grep -q "tar -czf" scripts/migrate-to-new-version.sh; then
        test_pass "Has fallback manual backup"
    else
        test_fail "No fallback backup mechanism"
    fi
}

# Test 6: Check for rollback instructions
test_rollback_instructions() {
    test_info "Test 6: Checking for rollback instructions..."
    
    if grep -q "display_rollback_instructions" scripts/migrate-to-new-version.sh; then
        test_pass "Rollback instructions function present"
    else
        test_fail "No rollback instructions function"
    fi
}

# Test 7: Check for service verification
test_service_verification() {
    test_info "Test 7: Checking for service verification..."
    
    if grep -q "verify_services" scripts/migrate-to-new-version.sh; then
        test_pass "Service verification function present"
    else
        test_fail "No service verification function"
    fi
}

# Test 8: Check for Caddyfile validation
test_caddyfile_validation() {
    test_info "Test 8: Checking for Caddyfile validation..."
    
    if grep -q "validate_caddyfile" scripts/migrate-to-new-version.sh; then
        test_pass "Caddyfile validation function present"
    else
        test_fail "No Caddyfile validation function"
    fi
}

# Test 9: Check for proper error handling
test_error_handling() {
    test_info "Test 9: Checking for proper error handling..."
    
    if grep -q "set +e" scripts/migrate-to-new-version.sh; then
        test_pass "Script uses graceful error handling (set +e)"
    else
        test_warn "Script may exit on first error"
    fi
    
    if grep -q "track_failure\|track_warning" scripts/migrate-to-new-version.sh; then
        test_pass "Script tracks failures and warnings"
    else
        test_fail "No failure/warning tracking"
    fi
}

# Test 10: Check for logging
test_logging() {
    test_info "Test 10: Checking for logging functionality..."
    
    if grep -q "MIGRATION_LOG=" scripts/migrate-to-new-version.sh; then
        test_pass "Migration log file defined"
    else
        test_fail "No migration log file"
    fi
    
    if grep -q "tee -a.*MIGRATION_LOG" scripts/migrate-to-new-version.sh; then
        test_pass "Commands output to log file"
    else
        test_warn "Not all commands may be logged"
    fi
}

# Test 11: Simulate dry-run (check prerequisites)
test_prerequisites() {
    test_info "Test 11: Checking prerequisites for migration..."
    
    # Check if docker is available
    if command -v docker &> /dev/null; then
        test_pass "Docker is installed"
    else
        test_warn "Docker not found (required for migration)"
    fi
    
    # Check if docker compose is available
    if docker compose version &> /dev/null 2>&1; then
        test_pass "Docker Compose is available"
    else
        test_warn "Docker Compose not available (required for migration)"
    fi
    
    # Check if python3 is available
    if command -v python3 &> /dev/null; then
        test_pass "Python3 is installed"
    else
        test_warn "Python3 not found (needed for BackupManager)"
    fi
}

# Test 12: Check for user confirmation
test_user_confirmation() {
    test_info "Test 12: Checking for user confirmation prompts..."
    
    if grep -q "read -p.*Continue" scripts/migrate-to-new-version.sh; then
        test_pass "Script asks for user confirmation"
    else
        test_fail "No user confirmation prompt"
    fi
}

# Test 13: Verify docker-compose.yml exists
test_docker_compose_exists() {
    test_info "Test 13: Checking if docker-compose.yml exists..."
    
    if [[ -f docker-compose.yml ]]; then
        test_pass "docker-compose.yml exists"
    else
        test_warn "docker-compose.yml not found (needed for migration)"
    fi
}

# Test 14: Verify Caddyfile exists
test_caddyfile_exists() {
    test_info "Test 14: Checking if Caddyfile exists..."
    
    if [[ -f config/Caddyfile ]]; then
        test_pass "Caddyfile exists"
    else
        test_warn "Caddyfile not found (needed for migration)"
    fi
}

# Test 15: Check for data directory structure
test_data_directory() {
    test_info "Test 15: Checking data directory structure..."
    
    if [[ -d data/stealth-vpn ]]; then
        test_pass "data/stealth-vpn directory exists"
    else
        test_warn "data/stealth-vpn directory not found"
    fi
    
    if [[ -d data/stealth-vpn/backups ]]; then
        test_pass "Backup directory exists"
    else
        test_warn "Backup directory not found (will be created)"
    fi
}

# Display test summary
display_test_summary() {
    echo
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║              Migration Test Summary                        ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo
    echo "Tests Passed: ${GREEN}${TESTS_PASSED}${NC}"
    echo "Tests Failed: ${RED}${TESTS_FAILED}${NC}"
    echo
    
    if [[ ${#FAILED_TESTS[@]} -gt 0 ]]; then
        echo -e "${RED}Failed Tests:${NC}"
        for test in "${FAILED_TESTS[@]}"; do
            echo -e "  ${RED}✗${NC} $test"
        done
        echo
    fi
    
    if [[ $TESTS_FAILED -eq 0 ]]; then
        echo -e "${GREEN}✓ All tests passed!${NC}"
        echo "Migration script is ready to use."
        echo
        echo "To run the migration:"
        echo "  ./scripts/migrate-to-new-version.sh"
        echo
        return 0
    else
        echo -e "${RED}✗ Some tests failed.${NC}"
        echo "Please review the failures above before running migration."
        echo
        return 1
    fi
}

# Main test execution
main() {
    echo
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║         Migration Script Test Suite                       ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo
    
    # Run all tests
    test_migration_script_exists
    test_migration_script_executable
    test_migration_script_syntax
    test_required_functions
    test_backup_functionality
    test_rollback_instructions
    test_service_verification
    test_caddyfile_validation
    test_error_handling
    test_logging
    test_prerequisites
    test_user_confirmation
    test_docker_compose_exists
    test_caddyfile_exists
    test_data_directory
    
    # Display summary
    display_test_summary
}

# Run tests
main "$@"
