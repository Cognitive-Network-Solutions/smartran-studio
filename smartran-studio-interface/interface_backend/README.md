# Backend - CLI Command Processor

FastAPI-based command processing engine for SmartRAN Studio.

## Technology Stack

- **FastAPI** - Web framework
- **Pydantic** - Data validation
- **python-arango** - Database client
- **httpx** - Async HTTP client

## Features

- Command framework with auto-registration
- Flexible argument parsing
- Session state management
- Simulation engine API client
- Configuration save/load
- Hot reload for development

## Structure

```
interface_backend/
├── backend.py              # FastAPI app & command router
├── commands/               # Command modules
│   ├── __init__.py
│   ├── connection.py       # Network management
│   ├── initialization.py   # Simulation init
│   ├── query.py           # Cell/site/UE queries
│   ├── update.py          # Cell updates
│   ├── simulation.py      # Compute operations
│   ├── config_management.py # Save/load configs
│   └── site_management.py # Add sites/cells
├── framework/             # Command framework
│   ├── __init__.py
│   ├── command_registry.py # Command registration
│   ├── argument_parser.py  # Argument parsing
│   └── response_types.py   # Response formatting
├── api_client.py          # Simulation engine client
├── config.py              # Config loading
├── config.yaml            # Network configuration
├── session.py             # Session state
├── arango_client.py       # Database client
├── models.py              # Pydantic models
├── requirements.txt       # Dependencies
└── Dockerfile.backend     # Docker configuration
```

## Running

### Via Docker Compose (Recommended)

```bash
# From repository root
docker compose up -d backend
```

Access API at: http://localhost:8001

### Local Development (Optional)

**Note**: Hot reload is already enabled in Docker via volume mounts. Local development is only useful if you want to run the backend outside Docker.

**Requirements**: Simulation engine and database must be running (via Docker).

```bash
cd interface_backend
pip install -r requirements.txt

# Update config.yaml to point to Docker services
# Change api_url to "http://localhost:8000"
# Change ARANGO_HOST to "http://localhost:8529"

uvicorn backend:app --reload --port 8001
```

**Recommended**: Use Docker with hot reload instead (code changes apply automatically).

## API Endpoints

### Execute Command

```bash
POST /api/command
Content-Type: application/json

{
  "command": "srs query cells --band=H"
}
```

**Response**:
```json
{
  "result": "...formatted output...",
  "exit_code": 0,
  "data": {
    "response_type": "table",
    "columns": [...],
    "rows": [...]
  }
}
```

### Health Check

```bash
GET /
```

## Command Framework

### Creating a Command

Use the `@command` decorator in a module under `commands/`:

```python
from framework import command, CommandResponse, ResponseType, CommandArgument, ArgumentType

@command(
    name="my-command",
    description="Short description",
    usage="srs my-command <arg>",
    examples=["srs my-command value"],
    category="General",
    requires_connection=True,
    arguments=[
        CommandArgument("arg", ArgumentType.STRING, required=True,
                       help_text="Argument description")
    ]
)
async def cmd_my_command(args: Dict[str, Any]) -> CommandResponse:
    # Access parsed arguments
    arg_value = args.get("arg")
    
    # Call simulation engine API
    from api_client import api_request
    result = await api_request("GET", "/some-endpoint")
    
    # Return formatted response
    return CommandResponse(
        content=f"Result: {result}",
        response_type=ResponseType.SUCCESS,
        data=result
    )
```

### Response Types

- `ResponseType.TEXT` - Plain text
- `ResponseType.TABLE` - Tabular data
- `ResponseType.JSON` - JSON data
- `ResponseType.SUCCESS` - Success message (green)
- `ResponseType.ERROR` - Error message (red)
- `ResponseType.INFO` - Info message (blue)

### Argument Types

- `ArgumentType.STRING`
- `ArgumentType.INTEGER`
- `ArgumentType.FLOAT`
- `ArgumentType.BOOLEAN`
- `ArgumentType.JSON`

## Configuration

### `config.yaml`

Network configuration:

```yaml
networks:
  sim:
    name: "SmartRAN Studio Simulation"
    api_url: "http://smartran-studio-sim-engine:8000"
    enabled: true

default_network: "sim"
```

### Environment Variables

- `SIONNA_API_URL` - Simulation engine API URL
- `ARANGO_HOST` - Database host
- `ARANGO_USERNAME` - Database username
- `ARANGO_PASSWORD` - Database password
- `ARANGO_DATABASE` - Database name

## Session Management

Tracks per-session state:
- Connected network
- Initialization status
- Interactive mode state

Located in `session.py`.

## Database Integration

Uses ArangoDB for persistent storage:
- `session_cache` - Current sim state
- `saved_configs` - User configurations

Client in `arango_client.py`.

## API Client

`api_client.py` provides async HTTP client for simulation engine:

```python
from api_client import api_request

# GET request
result = await api_request("GET", "/status")

# POST request with body
result = await api_request("POST", "/initialize", json=config)
```

## Development

### Hot Reload

Volume mounts in Docker Compose enable hot reload:
- `backend.py` → `/app/backend.py`
- `config.yaml` → `/app/config.yaml`

Changes apply immediately without rebuild.

### Adding Commands

1. Create new module in `commands/`
2. Define command with `@command` decorator
3. Import in `commands/__init__.py`
4. Restart backend (or wait for hot reload)

Command is automatically registered and available via CLI.

## Testing

```bash
# Unit tests
pytest tests/

# Integration tests
pytest tests/integration/
```

## License

See main repository LICENSE file.
