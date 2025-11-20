# SmartRAN Studio Architecture

## System Overview

SmartRAN Studio is a microservices-based platform for radio access network simulation and optimization.

```
┌─────────────────────────────────────────────────────────┐
│                    User Browser                         │
│                  (localhost:8080)                       │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│              Frontend (React + Vite)                    │
│         • CLI Interface                                 │
│         • Interactive Widgets                           │
│         • Real-time Command Execution                   │
└───────────────────────┬─────────────────────────────────┘
                        │ HTTP/REST
                        ▼
┌─────────────────────────────────────────────────────────┐
│          Backend (FastAPI - Port 8001)                  │
│         • CLI Command Parser                            │
│         • Session Management                            │
│         • Configuration Management                      │
└─────┬──────────────────────────┬────────────────────────┘
      │                          │
      │ HTTP/REST                │ ArangoDB Protocol
      ▼                          ▼
┌──────────────────┐    ┌─────────────────────────────────┐
│  Sim Engine      │    │   Database (ArangoDB)           │
│  (Port 8000)     │    │   • Simulation State            │
│  • RF Simulation │◄───┤   • Saved Configurations        │
│  • GPU Compute   │    │   • Measurement Snapshots       │
│  • Cell Mgmt     │    │   (Port 8529)                   │
└──────────────────┘    └─────────────────────────────────┘
```

## Components

### 1. Frontend (`smartran-studio-interface/interface_frontend`)

**Technology**: React 18 + Vite + TailwindCSS

**Purpose**: Web-based CLI interface

**Key Features**:
- Terminal-style command interface
- Command history and autocomplete
- Interactive initialization wizard
- Session persistence
- Real-time response rendering (tables, JSON, text)

**Container**: `smartran-studio-frontend`
- Port: 8080
- Nginx serves static build

### 2. Backend (`smartran-studio-interface/interface_backend`)

**Technology**: FastAPI (Python 3.11)

**Purpose**: CLI command processing and orchestration

**Key Features**:
- Command framework with automatic registration
- Argument parsing and validation
- Session state management
- API client for simulation engine
- Configuration save/load

**Container**: `smartran-studio-backend`
- Port: 8001
- Hot reload enabled for development

**Architecture**:
```
interface_backend/
├── backend.py              # FastAPI app & command router
├── commands/               # Command modules
│   ├── connection.py       # Network connection management
│   ├── initialization.py   # Simulation initialization
│   ├── query.py           # Cell/site/UE queries
│   ├── update.py          # Cell configuration updates
│   ├── simulation.py      # Compute operations
│   ├── config_management.py # Save/load configs
│   └── site_management.py # Add sites/cells
├── framework/             # Command framework
│   ├── command_registry.py
│   ├── argument_parser.py
│   └── response_types.py
├── api_client.py          # HTTP client for sim engine
├── config.py              # Configuration loading
├── session.py             # Session state
└── arango_client.py       # Database client
```

### 3. Simulation Engine (`smartran-studio-sim-engine`)

**Technology**: FastAPI + Sionna + TensorFlow + CUDA

**Purpose**: GPU-accelerated RF simulation

**Key Features**:
- Multi-cell propagation simulation
- Per-cell antenna array configuration
- UE distribution and management
- RSRP computation (chunked for memory efficiency)
- Site/cell management API

**Container**: `smartran-studio-sim-engine`
- Port: 8000
- Requires NVIDIA GPU

**Architecture**:
```
smartran-studio-sim-engine/
├── api/
│   ├── main.py            # FastAPI app & endpoints
│   ├── cell_query.py      # Cell query logic
│   ├── cell_update.py     # Cell update logic
│   └── ue_management.py   # UE management
├── simulation/
│   ├── engine.py          # MultiCellSim class (core)
│   ├── helpers.py         # Site/cell creation helpers
│   └── initialization.py  # Sim initialization
├── analysis/
│   ├── beampattern_analysis.py
│   └── beampattern_generation.py
└── db/
    ├── arango_client.py   # Database connection
    └── persist_run.py     # Snapshot persistence
```

**Core Simulation Class**: `MultiCellSim`
- Manages cells, sites, UEs
- Sionna channel models (UMa - Urban Macro)
- GPU-accelerated computation
- Configurable antenna arrays per cell

### 4. Database (`smartran-studio-arangodb`)

**Technology**: ArangoDB 3.11

**Purpose**: Persistent state storage

**Collections**:
- `session_cache` - Current simulation state
- `saved_configs` - User-saved configurations
- `sim_runs` - Simulation run metadata (one per compute run)
- `sim_reports` - Per-UE RSRP measurement reports (linked to sim_runs)

**Container**: `smartran-studio-arangodb`
- Port: 8529 (Web UI + API)
- Volumes: Persistent data storage

**Schema Documentation**: See **[Database Schema Reference](DATABASE_SCHEMA.md)** for complete schema details, query examples, and data extraction guides.

## Network Architecture

All services communicate on `smartran-studio-network` (Docker bridge network):

```
smartran-studio-network
├── smartran-studio-arangodb:8529     (Database)
├── smartran-studio-sim-engine:8000   (Simulation)
├── backend:8001                      (CLI Backend)
└── frontend:80                       (Web UI)
```

**External Access**:
- Frontend: `localhost:8080` → `frontend:80`
- Backend API: `localhost:8001` → `backend:8001`
- Sim Engine API: `localhost:8000` → `smartran-studio-sim-engine:8000`
- Database UI: `localhost:8529` → `smartran-studio-arangodb:8529`

## Data Flow

### Command Execution Flow:

1. **User** enters command in web CLI (e.g., `srs query cells`)
2. **Frontend** sends HTTP POST to `/api/command` on backend
3. **Backend** parses command and routes to appropriate command handler
4. **Command Handler** calls simulation engine API
5. **Sim Engine** processes request (query cells, update config, run compute)
6. **Response** flows back through backend to frontend
7. **Frontend** renders formatted response (table, JSON, text)

### Simulation Compute Flow:

1. **User** runs `srs sim compute --name="test"`
2. **Backend** POSTs to `/sim-compute` on sim engine
3. **Sim Engine**:
   - Validates simulation is initialized
   - Chunks cells and UEs for memory efficiency
   - Computes RSRP on GPU (TensorFlow + Sionna)
   - Saves snapshot to database
   - Returns metadata
4. **Backend** formats response
5. **Frontend** displays results

## Configuration Management

### Simulation State:
- **Transient**: Held in memory in sim engine
- **Persistent**: Saved to database via `config save`

### Saved Configuration Includes:
- Initialization parameters
- All cell configurations
- UE distribution
- Topology metadata

### Restore Process:
1. Load config from database
2. Recreate simulation from saved parameters
3. Restore all cell/UE state

## Technology Stack

### Backend Services:
- **FastAPI** - Modern async Python web framework
- **Pydantic** - Data validation
- **python-arango** - ArangoDB client
- **httpx** - Async HTTP client

### Simulation Engine:
- **Sionna 1.1.0** - NVIDIA's ray-tracing RF simulator
- **TensorFlow 2.19** - GPU computation backend
- **RAPIDS** - GPU-accelerated data processing
- **NumPy** - Numerical computing

### Frontend:
- **React 18** - UI framework
- **Vite** - Build tool
- **TailwindCSS** - Styling
- **Nginx** - Web server

### Infrastructure:
- **Docker** - Containerization
- **Docker Compose** - Orchestration
- **NVIDIA Container Toolkit** - GPU access

## Development Mode

Hot reload enabled for:
- **Backend**: Code changes reload automatically
- **Frontend**: Vite dev server (not used in Docker, but available)

Volume mounts:
- Backend: `backend.py` and `config.yaml` mounted for live editing
- Sim Engine: No mounts (rebuild required)

## Security Considerations

**Current State (Development)**:
- Default database password in plain text
- No authentication on APIs
- All services on same network
- Exposed ports for debugging

**Production Recommendations**:
- Change all default passwords
- Add API authentication (JWT/OAuth)
- Use secrets management
- Limit port exposure
- Enable HTTPS
- Network segmentation

