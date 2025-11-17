# Project Structure

## Directory Organization

```
stealth-vpn-server/
├── core/                      # Core Python modules (business logic)
│   ├── interfaces.py         # Abstract interfaces and data models
│   ├── service_manager.py    # Service lifecycle management
│   ├── xray_manager.py       # Xray config generation
│   ├── trojan_manager.py     # Trojan config generation
│   ├── singbox_manager.py    # Sing-box config generation
│   └── xray_api.py           # Xray gRPC API client
│
├── scripts/                   # Standalone utility scripts
│   ├── *-config-manager.py   # Config generation and testing
│   ├── test-*-integration.py # Integration tests
│   ├── setup-*.sh            # Service setup scripts
│   └── health-check.sh       # Health monitoring
│
├── admin-panel/              # Flask admin panel container
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── templates/            # Jinja2 HTML templates
│   └── static/               # CSS/JS assets
│
├── xray/                     # Xray-core container
│   ├── Dockerfile
│   └── entrypoint.sh
│
├── trojan/                   # Trojan-Go container
│   ├── Dockerfile
│   └── entrypoint.sh
│
├── singbox/                  # Sing-box container
│   ├── Dockerfile
│   └── entrypoint.sh
│
├── config/                   # Static configuration files
│   ├── Caddyfile            # Caddy reverse proxy config
│   └── Caddyfile.template   # Template for generation
│
├── data/                     # Runtime data (created during setup)
│   ├── stealth-vpn/
│   │   ├── configs/         # Generated VPN configs
│   │   │   ├── clients/     # Per-user client configs
│   │   │   ├── *.json       # Server configs
│   │   │   └── *.template.json  # Config templates
│   │   ├── logs/            # Service logs
│   │   └── backups/         # Config backups
│   ├── caddy/               # Caddy data and SSL certs
│   └── www/                 # Cover website files
│       ├── index.html       # Landing page
│       ├── dashboard.html   # Fake dashboard
│       ├── api/v1/docs.html # Fake API docs
│       ├── css/
│       └── js/
│
├── docs/                     # Documentation
├── .env.example             # Environment template
├── docker-compose.yml       # Service orchestration
└── install.sh               # Automated installer
```

## Architecture Patterns

### Interface-Based Design

All core modules implement abstract interfaces defined in `core/interfaces.py`:
- `UserStorageInterface` - User data persistence
- `ConfigGeneratorInterface` - VPN config generation
- `ServiceManagerInterface` - Service lifecycle
- `ObfuscationInterface` - Endpoint obfuscation
- `AuthenticationInterface` - Admin authentication
- `WebServiceInterface` - Cover web service

### Data Models

Dataclasses in `core/interfaces.py` define all data structures:
- `User` - User account with all protocol credentials
- `ServerConfig` - Server-wide configuration
- `*Config` - Protocol-specific client configs (XrayConfig, TrojanConfig, etc.)

### Configuration Management

- **Templates**: `*.template.json` files with `{{VARIABLE}}` placeholders
- **Generation**: Manager classes replace placeholders and generate configs
- **Storage**: Generated configs saved to `data/stealth-vpn/configs/`
- **Backups**: Automatic backups before config updates

### Service Communication

- Services communicate via Docker network (`stealth-vpn`)
- Caddy reverse proxies to internal services
- Xray uses gRPC API for runtime management (port 10085)
- No direct inter-service dependencies except through Caddy

## Code Conventions

### Python Style

- Use dataclasses for data models
- Abstract base classes (ABC) for interfaces
- Type hints on all function signatures
- Docstrings for all classes and public methods
- Path objects from `pathlib` for file operations
- JSON for configuration serialization

### Configuration Files

- JSON format for VPN configs (Xray, Trojan, Sing-box)
- Template files use `{{VARIABLE}}` syntax
- Environment variables in `.env` file
- Caddyfile for reverse proxy rules

### Naming Conventions

- Scripts: `{action}-{service}-{purpose}.py` or `.sh`
- Managers: `{protocol}_manager.py`
- Configs: `{protocol}.json` and `{protocol}.template.json`
- Client configs: `{protocol}-{variant}.json`
- Container names: `stealth-{service}`

### Error Handling

- Scripts use colored output (RED, GREEN, YELLOW, BLUE)
- Logging functions: `log()`, `warn()`, `error()`
- `set -e` in bash scripts for fail-fast behavior
- Try-except blocks in Python with descriptive error messages

## Key Design Principles

1. **Obfuscation First**: All endpoints and paths must look legitimate
2. **Container Isolation**: Each service runs independently
3. **Template-Based Config**: Never hardcode values, use templates
4. **Graceful Degradation**: Multiple protocols provide fallback options
5. **Minimal Dependencies**: Keep Python dependencies lean
6. **Stateless Services**: All state in mounted volumes
