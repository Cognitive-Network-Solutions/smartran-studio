# Backend Architecture

FastAPI-based command processor for the CNS CLI interface.

## 📁 Structure

```
interface_backend/
├── backend.py              # FastAPI app & command router
├── config.py               # Configuration management
├── session.py              # Session state tracking
├── models.py               # Pydantic request/response models
├── api_client.py           # HTTP client for Sionna API
├── formatting.py           # Output formatting utilities
├── commands/               # Command handlers
│   ├── __init__.py        # Package exports
│   ├── connection.py      # connect, networks, status, help
│   ├── initialization.py  # init wizard
│   ├── query.py           # query cells/sites/ues
│   ├── update.py          # update commands
│   └── simulation.py      # compute, drop ues
├── config.yaml             # Network configuration
├── requirements.txt        # Python dependencies
├── Dockerfile.backend      # Container definition
└── README.md               # This file
```

## 🔧 Core Modules

### `backend.py` (~170 lines)
**Role:** Application entry point and request router

```python
# Creates FastAPI app
# Defines /command endpoint
# Routes commands to handlers
# Manages CORS
```

**Key Endpoints:**
- `GET /` - Health check
- `POST /command` - Execute CLI command

### `config.py` (~27 lines)
**Role:** Configuration management

```python
def load_config() -> Dict[str, Any]:
    # Loads config.yaml
    # Provides network settings
    # Fallback to defaults if not found
```

**Exports:** `CONFIG` dict

### `session.py` (~40 lines)
**Role:** Session state management

```python
class SessionState:
    connected_network: str
    init_mode: bool
    init_step: int
    init_config: Dict
    
    def get_api_url() -> str
    def start_init_wizard()
    def end_init_wizard()
```

**Exports:** `session` singleton instance

### `models.py` (~18 lines)
**Role:** Request/response models

```python
class CommandRequest(BaseModel):
    command: str

class CommandResponse(BaseModel):
    result: str
    exit_code: int = 0
    data: Optional[Dict] = None
```

### `api_client.py` (~49 lines)
**Role:** HTTP client for API communication

```python
async def api_request(
    method: str,
    endpoint: str,
    data: Optional[Dict] = None,
    params: Optional[Dict] = None
) -> Dict:
    # Makes async HTTP requests to Sionna API
    # 300s timeout for long-running operations
    # Error handling with HTTPException
```

### `formatting.py` (~29 lines)
**Role:** Output formatting utilities

```python
def format_as_html_table(data: List[List], headers: List[str]) -> str:
    # Converts data to HTML table
    # Used for query results
    # Returns formatted HTML string
```

## 🎯 Command Modules

### `commands/connection.py`
Network connection management

| Command | Function | Description |
|---------|----------|-------------|
| `help` | `cmd_help()` | Show CLI help |
| `connect` | `cmd_connect(args)` | Connect to network |
| `networks` | `cmd_networks(args)` | List networks |
| `status` | `cmd_status(args)` | Connection status |

### `commands/initialization.py`
Simulation initialization

| Function | Purpose |
|----------|---------|
| `cmd_init_interactive(args)` | Main init handler |
| `get_init_wizard_prompt()` | Generate wizard prompts |
| `process_init_wizard_input(value)` | Handle wizard input |
| `finalize_init_wizard()` | Complete initialization |

**Wizard Steps:** 14 parameters from site count to UE layout

### `commands/query.py`
Query operations

| Command | Function | Description |
|---------|----------|-------------|
| `query cells` | `cmd_query_cells(args)` | Query cells with filters |
| `query sites` | `cmd_query_sites(args)` | List sites |
| `query ues` | `cmd_query_ues(args)` | Show UE info |

**Valid Filters (cells):**
- `--band`, `--site-name`, `--sector-id`, `--tilt-min/max`
- `--fc-ghz-min/max`, `--bs-rows/cols`, `--limit`, `--offset`

### `commands/update.py`
Cell configuration updates

| Command | Function | Description |
|---------|----------|-------------|
| `update cell` | `cmd_update_cell(args)` | Update single cell |
| `update cells query` | `cmd_update_cells_query(args)` | Update by query |

**Update Parameters:**
- `--update-tilt-deg`, `--update-tx-rs-power-dbm`
- `--update-bs-rows`, `--update-bs-cols`

### `commands/simulation.py`
Simulation operations

| Command | Function | Description |
|---------|----------|-------------|
| `compute` | `cmd_compute(args)` | Run simulation |
| `drop ues` | `cmd_drop_ues(args)` | Drop/redrop UEs |

## 🔄 Request Flow

### Example: `cns query cells --band=H`

```
1. Frontend → POST /command
   {"command": "cns query cells --band=H"}
   
2. backend.py receives request
   ├─ Parses command string
   ├─ Removes 'cns' prefix
   ├─ Lowercases verb: "query"
   └─ Preserves args: ["cells", "--band=H"]
   
3. Routes to query handler
   ├─ cmd == "query" → check args[0]
   ├─ args[0] == "cells"
   └─ Call cmd_query_cells(["--band=H"])
   
4. cmd_query_cells() executes
   ├─ Parses --band=H → {"band": "H"}
   ├─ Validates arguments
   ├─ Calls api_request("POST", "/query-cells", {"band": "H"})
   │   ├─ session.get_api_url() → "http://cns-sionna-sim:8000"
   │   ├─ Makes async HTTP POST
   │   └─ Returns JSON response
   ├─ Formats as HTML table
   │   └─ format_as_html_table(data, headers)
   └─ Returns formatted output
   
5. backend.py wraps in CommandResponse
   {"result": "...", "exit_code": 0}
   
6. Frontend renders output
```

## ⚙️ Configuration

### `config.yaml`

```yaml
networks:
  sim:
    name: "CNS Sionna Simulation"
    type: "simulation"
    api_url: "http://cns-sionna-sim:8000"
    enabled: true

default_network: "sim"
```

**API URL Configuration:**

| Scenario | URL |
|----------|-----|
| Both in Docker (same network) | `http://cns-sionna-sim:8000` |
| Backend in Docker, Sionna on host | `http://host.docker.internal:8000` |
| Backend outside Docker | `http://localhost:8000` |

## 🔒 Validation & Help

### Argument Validation
All commands strictly validate input:

```python
# Define valid flags
VALID_FLAGS = {'band', 'site-name', 'tilt-min', 'tilt-max', ...}

# Track invalid arguments
invalid_args = []

# Validate during parsing
for arg in args:
    if not is_valid(arg):
        invalid_args.append(arg)

# Return error if invalid
if invalid_args:
    return f"❌ Error: Invalid arguments: {', '.join(invalid_args)}\n..."
```

### Context-Sensitive Help
Every command supports `--help`:

```python
if args and args[0] in ['--help', '-h']:
    return """
    [Description]
    
    Usage: cns <command> [options]
    
    Options:
      --flag=<value>    Description
    
    Examples:
      cns command example
    """
```

## 🛠️ Adding New Commands

### Step 1: Create Command Function

```python
# commands/my_feature.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import List
from api_client import api_request

async def cmd_my_feature(args: List[str]) -> str:
    """Handle my-feature command"""
    
    # Help check
    if args and args[0] in ['--help', '-h']:
        return """Usage: cns my-feature [options]"""
    
    # Validate arguments
    # ... validation logic ...
    
    # Make API call
    result = await api_request("GET", "/my-endpoint")
    
    # Format output
    return f"✓ Success: {result['message']}"
```

### Step 2: Export from `commands/__init__.py`

```python
from commands.my_feature import cmd_my_feature
```

### Step 3: Add Route in `backend.py`

```python
@app.post("/command")
async def execute_command(req: CommandRequest) -> CommandResponse:
    # ... existing routing ...
    
    elif cmd == "my-feature":
        result = await cmd_my_feature(args)
    
    # ... rest of routing ...
```

### Step 4: Test

```bash
# Restart backend
docker compose restart backend

# Test command
cns my-feature --help
cns my-feature
```

## 🔌 Adding New Network Sources

### Step 1: Update `config.yaml`

```yaml
networks:
  prod:
    name: "Production Network"
    type: "production"
    api_url: "https://api.cns.network"
    auth_token: "${CNS_API_TOKEN}"  # Optional
    enabled: true
```

### Step 2: Connect

```bash
cns connect prod
cns query cells
```

**No code changes needed!** The backend automatically:
- Lists new network in `cns networks`
- Routes API calls to configured URL
- Maintains session state per network

## 📊 State Management

### Global State
```python
CONFIG = load_config()     # Loaded once at startup
session = SessionState()   # Single instance
```

### Session State
```python
session.connected_network = "sim"     # Current network
session.init_mode = False             # In wizard?
session.init_step = 0                 # Wizard step
session.init_config = {}              # Partial config
```

### Configuration Access Pattern
```python
commands → session.get_api_url()
              ↓
       session.get_network_config()
              ↓
       CONFIG["networks"][network]
```

## 🐛 Error Handling

```python
# Commands return error strings
if error_condition:
    return "❌ Error: Something went wrong\n\nTry: cns command --help"

# API client raises HTTPException
if response.status_code != 200:
    raise HTTPException(status_code=500, detail="API error")

# FastAPI handles exceptions
@app.exception_handler(Exception)
async def exception_handler(request, exc):
    return JSONResponse(status_code=500, content={"detail": str(exc)})
```

## 🚀 Performance

### Async/Await
- All API calls are asynchronous
- Non-blocking I/O throughout
- Concurrent request handling

### Timeouts
- API requests: 300s (for long-running compute)
- Adjustable per endpoint

### Memory
- Single session instance (minimal state)
- Config loaded once at startup
- No request-based state accumulation

## 🔍 Debugging

### View Backend Logs
```bash
docker compose logs -f backend
```

### Test API Directly
```bash
# Health check
curl http://localhost:8001/

# Execute command
curl -X POST http://localhost:8001/command \
  -H "Content-Type: application/json" \
  -d '{"command": "status"}'
```

### Run Outside Docker
```bash
cd interface_backend
python backend.py
# Server starts on http://localhost:8001
```

## 📝 Development Tips

1. **Use `--help` flags** - Make help comprehensive
2. **Validate everything** - Prevent silent failures
3. **Format consistently** - Use HTML tables for structured data
4. **Test error cases** - Invalid args, API failures
5. **Keep modules focused** - Single responsibility per file
6. **Document API responses** - See `API_RESPONSE_REFERENCE.md`

## 🔮 Future Enhancements

- [ ] Caching layer for query results
- [ ] WebSocket support for real-time updates
- [ ] Metrics/monitoring endpoints
- [ ] Rate limiting
- [ ] Authentication middleware
- [ ] Request logging and tracing
- [ ] Connection pooling for API calls

---

**For CLI usage, see:** [Frontend README](../interface_frontend/README.md)

