# Stealth VPN Server - Test Suite

Comprehensive testing suite for the Stealth VPN Server project, including unit tests and integration tests.

## Test Structure

```
tests/
├── unit/                          # Unit tests for core functionality
│   ├── test_json_storage.py      # JSON storage operations
│   ├── test_config_generation.py # VPN config generation
│   └── test_admin_auth.py        # Admin authentication
│
├── integration/                   # Integration tests
│   ├── test_vpn_connectivity.py  # VPN protocol connectivity
│   ├── test_admin_panel_e2e.py   # Admin panel end-to-end
│   └── test_docker_orchestration.py # Docker container orchestration
│
├── run_unit_tests.py             # Unit test runner
├── run_integration_tests.py      # Integration test runner
└── run_all_tests.py              # Master test runner
```

## Prerequisites

- Python 3.7+
- Docker and Docker Compose
- All project dependencies installed

## Running Tests

### Run All Tests

```bash
python3 tests/run_all_tests.py
```

This runs both unit and integration tests with comprehensive reporting.

### Run Unit Tests Only

```bash
python3 tests/run_unit_tests.py
```

Unit tests do not require Docker containers to be running.

### Run Integration Tests Only

```bash
python3 tests/run_integration_tests.py
```

**Important:** Integration tests require Docker containers to be running:

```bash
docker compose up -d
python3 tests/run_integration_tests.py
```

### Run Individual Test Files

```bash
# Unit tests
python3 tests/unit/test_json_storage.py
python3 tests/unit/test_config_generation.py
python3 tests/unit/test_admin_auth.py

# Integration tests
python3 tests/integration/test_vpn_connectivity.py
python3 tests/integration/test_admin_panel_e2e.py
python3 tests/integration/test_docker_orchestration.py
```

## Test Coverage

### Unit Tests

#### JSON Storage Tests (`test_json_storage.py`)
- JSON serialization and deserialization
- Atomic write operations
- Backup creation and rotation
- Data recovery from backups
- Concurrent access handling

#### Configuration Generation Tests (`test_config_generation.py`)
- Xray configuration generation (server and client)
- Trojan-Go configuration generation
- Sing-box configuration generation (ShadowTLS, Hysteria2, TUIC)
- WireGuard configuration generation
- Multi-user configuration handling
- Configuration validation

#### Admin Authentication Tests (`test_admin_auth.py`)
- Password hashing with bcrypt
- Password strength validation
- Session token generation
- Session expiry logic
- Rate limiting for login attempts
- CSRF protection
- Security headers configuration

### Integration Tests

#### VPN Connectivity Tests (`test_vpn_connectivity.py`)
- Docker container status checks
- Xray service connectivity
- Trojan-Go service connectivity
- Sing-box service connectivity
- WireGuard service connectivity
- Caddy reverse proxy functionality
- Docker network connectivity

#### Admin Panel E2E Tests (`test_admin_panel_e2e.py`)
- Admin panel container status
- Flask application health
- User storage operations
- Configuration file generation
- Client configuration generation
- Backup system functionality
- Log file creation
- Data persistence across restarts

#### Docker Orchestration Tests (`test_docker_orchestration.py`)
- Docker Compose configuration validity
- All containers running status
- Container health checks
- Docker network configuration
- Volume mount verification
- Config volume access from containers
- Container dependency ordering
- Restart policy configuration
- Resource limit monitoring

## Test Output

Tests provide colored output for easy reading:
- 🟢 **Green**: Passed tests
- 🔴 **Red**: Failed tests
- 🟡 **Yellow**: Warnings or non-critical issues
- 🔵 **Blue**: Informational messages

## Continuous Integration

To integrate with CI/CD pipelines:

```bash
# Run tests and exit with appropriate code
python3 tests/run_all_tests.py
EXIT_CODE=$?

# Exit code 0 = all tests passed
# Exit code 1 = some tests failed
exit $EXIT_CODE
```

## Troubleshooting

### Unit Tests Failing

1. Check Python dependencies:
   ```bash
   pip3 install -r admin-panel/requirements.txt
   ```

2. Verify core modules are accessible:
   ```bash
   python3 -c "from core.interfaces import User; print('OK')"
   ```

### Integration Tests Failing

1. Ensure Docker is running:
   ```bash
   docker ps
   ```

2. Start all containers:
   ```bash
   docker compose up -d
   ```

3. Check container logs:
   ```bash
   docker compose logs
   ```

4. Verify container status:
   ```bash
   docker compose ps
   ```

### Common Issues

**Issue:** `ModuleNotFoundError` in unit tests
**Solution:** Ensure you're running tests from the project root directory

**Issue:** Integration tests timeout
**Solution:** Increase timeout values in test files or check container performance

**Issue:** Permission denied errors
**Solution:** Ensure test scripts are executable:
```bash
chmod +x tests/*.py tests/unit/*.py tests/integration/*.py
```

## Adding New Tests

### Adding Unit Tests

1. Create a new test file in `tests/unit/`:
   ```python
   #!/usr/bin/env python3
   """Test description."""
   
   def test_feature():
       """Test a specific feature."""
       # Test implementation
       return True
   
   def main():
       """Run all tests."""
       tests = [
           ("Feature Test", test_feature),
       ]
       # Run tests and report results
   
   if __name__ == "__main__":
       success = main()
       sys.exit(0 if success else 1)
   ```

2. The test will be automatically picked up by `run_unit_tests.py`

### Adding Integration Tests

1. Create a new test file in `tests/integration/`
2. Follow the same pattern as existing integration tests
3. Use colored output for consistency
4. The test will be automatically picked up by `run_integration_tests.py`

## Best Practices

1. **Keep tests focused**: Each test should verify one specific behavior
2. **Use descriptive names**: Test names should clearly indicate what they test
3. **Clean up resources**: Always clean up temporary files and directories
4. **Handle exceptions**: Catch and report exceptions gracefully
5. **Provide clear output**: Use colored output and descriptive messages
6. **Test both success and failure**: Verify both positive and negative cases
7. **Avoid external dependencies**: Mock external services when possible
8. **Keep tests fast**: Unit tests should run in seconds, integration tests in minutes

## Test Maintenance

- Review and update tests when adding new features
- Remove obsolete tests when features are deprecated
- Keep test dependencies minimal
- Document any special test requirements
- Ensure tests are idempotent (can be run multiple times)

## Support

For issues or questions about the test suite:
1. Check this README
2. Review test output for specific error messages
3. Check container logs: `docker compose logs`
4. Verify system requirements are met
