# CNS Sionna Simulation API

FastAPI service providing a REST interface for multi-cell wireless network simulation using Sionna.

## 🎯 Overview

This FastAPI application wraps the CNS Sionna multi-cell simulation (`MultiCellSim`) with a RESTful API, enabling:
- **Dynamic initialization** with custom network topologies
- **Cell and site queries** with flexible filtering
- **Configuration updates** (tilts, power, antenna arrays)
- **UE management** with dynamic drops and layouts
- **GPU-accelerated compute** for RSRP calculations and measurement reports

## 🚀 Quick Start

### Run with Docker

```bash
# Start the API
docker compose up --build -d

# Access the API
curl http://localhost:8000/

# View interactive docs
open http://localhost:8000/docs
```

### Run Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Start the server
python main.py
```

The server runs on `http://localhost:8000`

## 📋 API Workflow

### 1. Initialize Simulation

**Required first step** - must be called before using other endpoints:

```bash
# Use all defaults
curl -X POST http://localhost:8000/initialize \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Custom configuration:**
```bash
curl -X POST http://localhost:8000/initialize \
  -H "Content-Type: application/json" \
  -d '{
    "n_sites": 15,
    "spacing": 600.0,
    "seed": 42,
    "fc_hi_hz": 3500000000,
    "fc_lo_hz": 700000000,
    "num_ue": 50000
  }'
```

**Configuration Parameters:**
- **Site Layout:** `n_sites` (default: 10), `spacing` (default: 500m), `seed`, `jitter`, `site_height_m`
- **High Band:** `fc_hi_hz` (default: 2.5GHz), `tilt_hi_deg`, `bs_rows_hi`, `bs_cols_hi`, `antenna_pattern_hi`
- **Low Band:** `fc_lo_hz` (default: 600MHz), `tilt_lo_deg`, `bs_rows_lo`, `bs_cols_lo`, `antenna_pattern_lo`
- **UEs:** `num_ue` (default: 30,000), `box_pad_m`
- **Performance:** `cells_chunk`, `ue_chunk`

### 2. Query Topology

```bash
# Get all sites
curl http://localhost:8000/sites

# Get all cells
curl http://localhost:8000/cells

# Query cells with filters
curl -X POST http://localhost:8000/query-cells \
  -H "Content-Type: application/json" \
  -d '{"band": "H", "site_name": "CNS000*"}'
```

### 3. Update Configuration

```bash
# Update single cell
curl -X POST http://localhost:8000/update-cell \
  -H "Content-Type: application/json" \
  -d '{
    "cell_id": 0,
    "tilt_deg": 12.0,
    "tx_rs_power_dbm": 5.0
  }'

# Update multiple cells by query
curl -X POST http://localhost:8000/update-cells-by-query \
  -H "Content-Type: application/json" \
  -d '{
    "band": "H",
    "site_name": "CNS000*",
    "update_tilt_deg": 11.0
  }'
```

### 4. Run Simulation

```bash
# Compute RSRP and get measurement reports
curl -X POST http://localhost:8000/measurement-reports \
  -H "Content-Type: application/json" \
  -d '{
    "threshold_dbm": -120.0,
    "label_mode": "name"
  }'
```

## 📖 API Reference

### Initialization

#### `POST /initialize`
Initialize or reinitialize simulation with custom configuration.

**Status:** ⚠️ **Required first call** before using other endpoints

**Request Body:** (all fields optional)
```json
{
  "n_sites": 10,
  "spacing": 500.0,
  "seed": 7,
  "jitter": 0.06,
  "site_height_m": 20.0,
  "fc_hi_hz": 2500000000,
  "tilt_hi_deg": 9.0,
  "bs_rows_hi": 8,
  "bs_cols_hi": 1,
  "antenna_pattern_hi": "38.901",
  "fc_lo_hz": 600000000,
  "tilt_lo_deg": 9.0,
  "bs_rows_lo": 8,
  "bs_cols_lo": 1,
  "antenna_pattern_lo": "38.901",
  "num_ue": 30000,
  "box_pad_m": 250.0,
  "cells_chunk": 48,
  "ue_chunk": 500
}
```

**Response:** Configuration summary with site/cell/UE counts

---

### Query Operations

#### `GET /status`
Get simulation status and configuration.

```json
{
  "simulation_status": "ready",
  "num_sites": 10,
  "num_cells": 60,
  "num_ues": 30000,
  "num_bands": 2,
  "bands": ["H", "L"],
  "metadata": { /* latest compute metadata */ }
}
```

#### `GET /sites`
List all sites with positions and configurations.

#### `GET /cells`
List all cells with full configuration details.

**Response includes:**
- Cell identifiers (idx, name, band)
- Site association (site_idx, site_name, sector_id)
- RF parameters (fc_hz, tx_rs_power_dbm, tilt_deg)
- Antenna config (bs_rows, bs_cols, antenna_pattern)

#### `POST /query-cells`
Query cells with flexible filtering and pagination.

**Request Body:**
```json
{
  "band": "H",
  "site_name": "CNS000*",
  "sector_id": 0,
  "tilt_min": 9.0,
  "tilt_max": 11.0,
  "fc_ghz_min": 2.0,
  "fc_ghz_max": 3.0,
  "bs_rows": 8,
  "limit": 50,
  "offset": 0,
  "sort_by": "fc_GHz"
}
```

**Wildcards:** Use `*` in `site_name` or `cell_name` for pattern matching

**Response:** Filtered cell list with query metadata

#### `GET /ues`
Get UE information and compute results.

```json
{
  "num_ues": 30000,
  "layout": "box",
  "drop_params": { /* parameters used for drop */ },
  "has_results": true,
  "results": { /* compute results if available */ }
}
```

---

### Update Operations

#### `POST /update-cell`
Update a single cell's configuration.

**Request Body:**
```json
{
  "cell_id": 0,
  "tilt_deg": 12.0,
  "tx_rs_power_dbm": 5.0,
  "bs_rows": 8,
  "bs_cols": 1
}
```

**Updatable Parameters:**
- RF: `fc_hz`, `tx_rs_power_dbm`, `tilt_deg`, `roll_deg`, `height_m`
- Antenna: `bs_rows`, `bs_cols`, `bs_pol`, `antenna_pattern`, `elem_v_spacing`, `elem_h_spacing`

**⚠️ Note:** `bs_rows` and `bs_cols` must be updated together

#### `POST /update-cells-bulk`
Update multiple cells in a single request.

**Request Body:**
```json
{
  "updates": [
    {"cell_id": 0, "tilt_deg": 12.0},
    {"cell_id": 1, "tilt_deg": 10.0},
    {"cell_name": "HCNS0003A1", "tx_rs_power_dbm": 3.0}
  ],
  "stop_on_error": false
}
```

#### `POST /update-cells-by-query` ⭐
Query and update cells in one atomic operation.

**Request Body:**
```json
{
  "site_name": "CNS000*",
  "band": "H",
  "sector_id": 0,
  "update_tilt_deg": 12.0,
  "update_tx_rs_power_dbm": 5.0
}
```

**Benefits:**
- Single API call for query + update
- Wildcard support
- Atomic operation
- Automatic error handling

---

### Simulation Operations

#### `POST /measurement-reports`
Run compute and generate measurement reports.

**Request Body:**
```json
{
  "threshold_dbm": -120.0,
  "label_mode": "name"
}
```

**Response:**
```json
{
  "measurement_reports": [
    {
      "user_id": "user_000000",
      "HCNS0001A1": -85.2,
      "LCNS0001A1": -92.1,
      ...
    }
  ],
  "num_reports": 30000,
  "threshold_dbm": -120.0,
  "label_mode": "name",
  "metadata": {
    "timestep": 0,
    "num_users": 30000,
    "num_bands": 2,
    "bands": ["H", "L"],
    "timestamp": "2025-11-03_10-30-45"
  },
  "status": "success"
}
```

**⚠️ Note:** This is a long-running operation (seconds to minutes depending on UE count)

#### `POST /drop-ues`
Drop or redrop UEs with custom count and layout.

**Request Body:**
```json
{
  "num_ue": 50000,
  "layout": "box",
  "box_pad_m": 300.0,
  "height_m": 1.5,
  "seed": 42
}
```

**Layouts:**
- **box** (recommended): Uniform distribution around sites with padding
- **disk**: Circular distribution with specified radius

**⚠️ Warning:** This replaces ALL existing UEs and invalidates compute results

---

## 🔐 Concurrency & State Management

### Endpoint Behavior

| Endpoint | During Compute | Lock Used | Returns |
|----------|---------------|-----------|---------|
| `/status`, `/sites`, `/cells`, `/ues` | ✅ Allowed | `config_lock` (read) | Current state |
| `/query-cells` | ✅ Allowed | `config_lock` (read) | Filtered results |
| `/update-*`, `/drop-ues` | ❌ **Blocked** | `config_lock` (write) | **409 Conflict** |
| `/initialize` | ❌ **Blocked** | `config_lock` (write) | **409 Conflict** |
| `/measurement-reports` | 🔒 Serialized | `compute_lock` | Compute results |

### HTTP Status Codes

- **503 Service Unavailable** - Simulation not initialized (call `/initialize`)
- **409 Conflict** - Configuration change attempted during compute (wait for completion)
- **400 Bad Request** - Invalid parameters or validation error
- **404 Not Found** - Cell name or ID not found
- **500 Internal Server Error** - Unexpected server error

---

## 🐳 Docker Deployment

### Docker Compose

```yaml
services:
  cns-sionna-sim:
    build: .
    ports:
      - "8000:8000"
    networks:
      - cns-network
    environment:
      - CUDA_VISIBLE_DEVICES=0
      - TF_GPU_ALLOCATOR=cuda_malloc_async
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

networks:
  cns-network:
    driver: bridge
    name: cns-network
```

### Commands

```bash
# Start services
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down
```

---

## ☸️ Kubernetes Deployment

For Kubernetes deployment with Helm, see:
[cns-sionna-sim-chart/README.md](cns-sionna-sim-chart/README.md)

**Features:**
- GPU support (L4, T4, V100, A100)
- Scalable deployment
- Ingress configuration
- Resource management
- Health checks

---

## 🔧 Configuration Tips

### Site & Spacing
- **Small network:** 5-7 sites, 400-500m spacing
- **Medium network:** 10-15 sites, 500-600m spacing  
- **Large network:** 20-30 sites, 600-800m spacing

### UE Count
- **Light load:** 5,000-10,000 UEs
- **Medium load:** 30,000 UEs (default)
- **Heavy load:** 50,000-100,000 UEs

### Antenna Arrays
- **8x1:** Standard narrow beam (16 antennas with dual-pol)
- **4x2:** Balanced beam (16 antennas)
- **4x4:** Wide beam (32 antennas - may hit memory limits)

**⚠️ Memory Warning:** Total antennas per cell affects GPU memory. Keep ≤16 antennas.

### Performance Tuning

**Chunking:** Adjust if memory issues occur
```json
{
  "cells_chunk": 32,
  "ue_chunk": 500
}
```

---

## 📊 Example Workflows

### Workflow 1: Initialize and Query

```bash
# 1. Initialize
curl -X POST http://localhost:8000/initialize -d '{}'

# 2. Check status
curl http://localhost:8000/status

# 3. View topology
curl http://localhost:8000/sites
curl http://localhost:8000/cells
```

### Workflow 2: Configuration Study

```bash
# 1. Query high-band cells
curl -X POST http://localhost:8000/query-cells -d '{"band": "H"}'

# 2. Update all high-band tilts
curl -X POST http://localhost:8000/update-cells-by-query -d '{
  "band": "H",
  "update_tilt_deg": 12.0
}'

# 3. Run compute
curl -X POST http://localhost:8000/measurement-reports -d '{}'

# 4. Try different tilt
curl -X POST http://localhost:8000/update-cells-by-query -d '{
  "band": "H",
  "update_tilt_deg": 10.0
}'

# 5. Recompute
curl -X POST http://localhost:8000/measurement-reports -d '{}'
```

### Workflow 3: UE Scaling

```bash
# 1. Start with 10k UEs
curl -X POST http://localhost:8000/drop-ues -d '{"num_ue": 10000}'
curl -X POST http://localhost:8000/measurement-reports -d '{}'

# 2. Scale to 50k
curl -X POST http://localhost:8000/drop-ues -d '{"num_ue": 50000}'
curl -X POST http://localhost:8000/measurement-reports -d '{}'

# 3. Compare results
curl http://localhost:8000/ues
```

---

## 🧪 Development

### Project Structure

```
cns-meets-sionna/
├── main.py                      # FastAPI app & endpoints
├── cns_sionna_sim.py            # MultiCellSim class
├── sionna_sim_helpers.py        # Helper functions
├── cell_query.py                # Query logic
├── cell_update.py               # Update logic
├── sim_initialization.py        # Init models & logic
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Container definition
├── compose.yaml                 # Docker Compose config
└── cns-sionna-sim-chart/        # Helm chart for K8s
```

### Adding New Endpoints

1. Define Pydantic models for request/response
2. Add endpoint to `main.py`:
   ```python
   @app.post("/my-endpoint")
   async def my_endpoint(req: MyRequest):
       check_sim_initialized()
       # Your logic here
       return MyResponse(...)
   ```
3. Add concurrency control if needed:
   ```python
   check_config_changes_allowed()  # For config changes
   async with config_lock:         # For state access
       # Your logic
   ```

### Testing

```bash
# Run simulation API
python main.py

# Test endpoints
curl -X POST http://localhost:8000/initialize -d '{}'
curl http://localhost:8000/status
```

---

## 🐛 Troubleshooting

### "Simulation not initialized"
- **Error:** 503 Service Unavailable
- **Fix:** Call `POST /initialize` first

### "Cannot modify configuration while compute is in progress"
- **Error:** 409 Conflict
- **Fix:** Wait for `/measurement-reports` to complete, then retry

### Out of Memory
- **Symptoms:** Compute fails or API crashes
- **Fix:** Reduce `num_ue`, `cells_chunk`, or `ue_chunk`

### Slow Compute
- **Cause:** Large UE count or insufficient GPU
- **Fix:** Reduce UE count or upgrade GPU

---

## 📝 Notes

- **GPU Recommended:** CPU-only mode works but is significantly slower
- **State is Per-Instance:** Each API instance has its own simulation state
- **No Persistence:** State is lost on restart (use `/initialize` to restore)
- **Thread-Safe:** Concurrent requests are properly handled with locks
- **Query During Compute:** Read-only queries work during long compute operations

---

## 📚 Related Documentation

- [CNS Protostack Interface](../cns-protostack-interface/README.md) - CLI for interacting with this API
- [Kubernetes Deployment](cns-sionna-sim-chart/README.md) - Helm chart for K8s

---

Built with **Sionna 1.1.0** • **FastAPI** • **TensorFlow** • **NVIDIA CUDA**
