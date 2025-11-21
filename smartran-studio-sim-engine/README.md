# SmartRAN Studio - Simulation Engine

GPU-accelerated RF propagation simulation engine powered by NVIDIA Sionna.

## Overview

The simulation engine is the core component that performs radio frequency (RF) propagation calculations using GPU acceleration. It provides a REST API for simulation control, cell/site management, and RSRP computation.

## Features

- **GPU-Accelerated**: TensorFlow + CUDA for fast computation
- **Multi-Cell Simulation**: Support for thousands of cells
- **Flexible Antenna Arrays**: Per-cell antenna configuration
- **UE Management**: Dynamic UE distribution
- **Chunked Computation**: Memory-efficient processing for large-scale networks
- **REST API**: Easy integration via FastAPI

## Architecture

```
smartran-studio-sim-engine/
├── api/                    # REST API endpoints
│   ├── main.py            # FastAPI application
│   ├── cell_query.py      # Cell querying logic
│   ├── cell_update.py     # Cell configuration updates
│   └── ue_management.py   # UE distribution management
├── simulation/            # Core simulation engine
│   ├── engine.py          # MultiCellSim class
│   ├── helpers.py         # Site/cell creation utilities
│   └── initialization.py  # Simulation initialization
├── analysis/              # Analysis tools
│   ├── beampattern_analysis.py
│   └── beampattern_generation.py
└── db/                    # Database persistence
    ├── arango_client.py   # ArangoDB client
    └── persist_run.py     # Snapshot storage
```

## Requirements

- **NVIDIA GPU** with CUDA support (8+ GB VRAM recommended)
- **NVIDIA Container Toolkit** installed
- **Docker** & **Docker Compose**

## Running

The simulation engine runs as part of the main Docker Compose stack. From the repository root:

```bash
docker compose up -d smartran-studio-sim-engine
```

Access the API at: **http://localhost:8000**

### API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Key Endpoints

### Initialization

```bash
POST /initialize
Content-Type: application/json

{
  "n_sites": 10,
  "num_ue": 30000,
  "fc_hi_hz": 2500000000,
  "fc_lo_hz": 600000000
}
```

### Query Cells

```bash
POST /query-cells
Content-Type: application/json

{
  "band": "H",
  "tilt_min": 8.0,
  "tilt_max": 12.0
}
```

### Update Cell

```bash
POST /update-cell
Content-Type: application/json

{
  "cell_id": 0,
  "tilt_deg": 12.0,
  "tx_rs_power_dbm": 3.0
}
```

### Run Simulation

```bash
POST /sim-compute
Content-Type: application/json

{
  "name": "baseline"
}
```

### Add Site

```bash
POST /add-site
Content-Type: application/json

{
  "x": 1000.0,
  "y": 500.0,
  "height_m": 20.0,
  "az0_deg": 0.0
}
```

### Add Cell

```bash
POST /add-cell
Content-Type: application/json

{
  "site_name": "SITE0001A",
  "sector_id": 0,
  "band": "H",
  "fc_hz": 2500000000,
  "tilt_deg": 9.0
}
```

## Core Simulation Class

### `MultiCellSim`

The heart of the simulation engine. Located in `simulation/engine.py`.

**Key Methods**:
- `add_site()` - Add a new site
- `add_cell()` - Add a cell to a site
- `drop_ues()` - Distribute UEs
- `compute()` - Run RF propagation computation
- `update_cell_config()` - Modify cell parameters

**Channel Model**: 3GPP TR 38.901 Urban Macro (UMa)

## Configuration

Environment variables (set via Docker Compose):
- `ARANGO_HOST` - Database hostname
- `ARANGO_USERNAME` - Database username
- `ARANGO_PASSWORD` - Database password
- `ARANGO_DATABASE` - Database name
- `CUDA_VISIBLE_DEVICES` - GPU selection

## Development

### ⚠️ Important: Docker is Required

**Local development without Docker is NOT recommended** for the simulation engine due to complex dependencies:
- CUDA 12.x + cuDNN
- TensorFlow 2.19 with CUDA support
- RAPIDS libraries (cuDF, cuML, cuGraph)
- Sionna 1.1.0
- Proper GPU driver configuration

**This is why we use the RAPIDS container** - it includes all these dependencies pre-configured.

### Development Workflow

**Option 1: Rebuild Container** (for code changes)
```bash
# From repository root
docker compose up --build -d smartran-studio-sim-engine
docker compose logs -f smartran-studio-sim-engine
```

**Option 2: Interactive Development** (attach to running container)
```bash
# Start container
docker compose up -d smartran-studio-sim-engine

# Attach to container
docker exec -it smartran-studio-sim-engine bash

# Edit code inside container or use volume mounts
# Restart uvicorn manually for changes
```

### Running Tests

```bash
# From repository root
docker exec -it smartran-studio-sim-engine pytest tests/
```

## Technology Stack

- **FastAPI** - Web framework
- **Sionna 1.1.0** - RF simulation library (NVIDIA)
- **TensorFlow 2.19** - GPU computation
- **RAPIDS** - GPU-accelerated data processing
- **NumPy** - Numerical computing
- **Pydantic** - Data validation

## Performance

**Typical Performance** (RTX 4060 Laptop GPU):
- 10 sites, 60 cells, 30,000 UEs
- Compute time: ~5-10 seconds
- Memory: ~4-5 GB GPU RAM

**Chunking**: Automatic chunking allows large-scale simulations on consumer GPUs.

## License

See main repository LICENSE file.

## Documentation

For complete documentation, see the `docs/` directory in the repository root:
- [Getting Started](../docs/GETTING_STARTED.md)
- [Architecture](../docs/ARCHITECTURE.md)
- [CLI Reference](../docs/CLI_REFERENCE.md)
