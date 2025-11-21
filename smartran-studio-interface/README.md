# SmartRAN Studio - Interface

Web-based command-line interface for SmartRAN Studio simulation control.

## Overview

The interface provides a terminal-style web UI for interacting with the simulation engine. It consists of three components:
1. **Frontend** - React-based CLI interface
2. **Backend** - FastAPI command processor
3. **Database** - ArangoDB for state persistence

## Components

### Frontend (`interface_frontend/`)

**Technology**: React 18 + Vite + TailwindCSS

Web-based CLI with:
- Terminal-style command input
- Command history and autocomplete
- Interactive initialization wizard
- Real-time response rendering
- Session persistence

**Access**: http://localhost:8080

[Frontend README](interface_frontend/README.md)

### Backend (`interface_backend/`)

**Technology**: FastAPI (Python 3.11)

Command processing engine with:
- Command framework with automatic registration
- Argument parsing and validation
- Session state management
- Simulation engine API client
- Configuration save/load

**API**: http://localhost:8001

[Backend README](interface_backend/README.md)

### Database (`interface_db/`)

**Technology**: ArangoDB 3.11

Persistent storage for:
- Simulation configurations
- Measurement snapshots
- Session state

**Access**: http://localhost:8529

[Database README](interface_db/README.md)

## Running

The interface runs as part of the main Docker Compose stack. From the repository root:

```bash
docker compose up -d
```

Then access the web UI at: **http://localhost:8080**

## Command Framework

The backend uses a flexible command framework located in `interface_backend/framework/`. Commands are auto-registered from the `commands/` directory.

### Adding a Command

1. Create command module in `interface_backend/commands/`
2. Use `@command` decorator
3. Define arguments with `CommandArgument`
4. Return `CommandResponse`

Example:

```python
from framework import command, CommandResponse, ResponseType

@command(
    name="my-command",
    description="Does something useful",
    usage="srs my-command [args]",
    category="General"
)
async def cmd_my_command(args: Dict[str, Any]) -> CommandResponse:
    # Process command
    return CommandResponse(
        content="Command executed successfully",
        response_type=ResponseType.SUCCESS
    )
```

## Configuration

### Backend Config (`interface_backend/config.yaml`)

```yaml
networks:
  sim:
    name: "SmartRAN Studio Simulation"
    api_url: "http://smartran-studio-sim-engine:8000"
    enabled: true

default_network: "sim"
```

### Environment Variables

Set via Docker Compose:
- `SIONNA_API_URL` - Simulation engine URL
- `ARANGO_HOST` - Database host
- `ARANGO_USERNAME` - Database user
- `ARANGO_PASSWORD` - Database password
- `ARANGO_DATABASE` - Database name

## Development

### Frontend Development

```bash
cd interface_frontend
npm install
npm run dev
```

Access at: http://localhost:5173

### Backend Development

Hot reload is enabled in Docker Compose via volume mounts:
- `backend.py` → `/app/backend.py`
- `config.yaml` → `/app/config.yaml`

Changes are applied automatically.

### Local Backend (Without Docker)

```bash
cd interface_backend
pip install -r requirements.txt
uvicorn backend:app --reload --port 8001
```

## Documentation

### Interface-Specific Docs

- [Framework Quick Reference](FRAMEWORK_QUICK_REFERENCE.md) - Command framework guide
- [Changelog](CHANGELOG.md) - Version history

### Main Documentation

See `docs/` in repository root:
- [Getting Started](../docs/GETTING_STARTED.md)
- [CLI Reference](../docs/CLI_REFERENCE.md)
- [Architecture](../docs/ARCHITECTURE.md)

## License

See main repository LICENSE file.
