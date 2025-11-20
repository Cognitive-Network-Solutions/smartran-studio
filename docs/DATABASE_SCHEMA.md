# Database Schema Reference

SmartRAN Studio uses **ArangoDB** (multi-model NoSQL database) to persist simulation runs, UE measurement reports, and configuration snapshots. This document describes the complete schema and provides query examples for data extraction.

---

## 📊 Looking for Usage Examples?

**This document is a technical reference.** For practical workflow examples, see:

👉 **[Data Analysis Guide](DATA_ANALYSIS_GUIDE.md)** - Complete end-to-end guide:
- Running simulations and saving results
- Extracting UE reports (REST API, AQL, Python)
- Analysis examples (coverage, load balance, heatmaps)
- Comparison between simulation runs
- Ready-to-use Python scripts

**Use this document for:**
- Understanding the database structure
- Writing custom AQL queries
- Integrating with external tools
- Database administration

---

## Overview

### Database: `smartran-studio_db`

**Collections:**
1. **`sim_runs`** - Simulation run headers with metadata
2. **`sim_reports`** - Per-UE measurement reports (one document per UE per run)
3. **`saved_configs`** - Saved simulation configurations (snapshots)
4. **`session_cache`** - Temporary session state (init config cache)

**Storage Model:**
- Each simulation run creates **1 header document** in `sim_runs`
- Each run creates **N documents** in `sim_reports` (one per UE)
- Links via `run_id` field for efficient queries
- Sparse storage: only cells above threshold stored per UE

---

## Collection Schemas

### 1. `sim_runs` Collection

**Purpose:** Store simulation run metadata, configuration snapshots, and timestamps.

**Document Structure:**

```json
{
  "_key": "2025-01-15_12-30-45",           // Run ID (timestamp-based)
  "_id": "sim_runs/2025-01-15_12-30-45",
  "_rev": "_hZ8kXXq---",
  
  "created_at": "2025-01-15T12:30:45.123Z", // ISO timestamp
  "threshold_dbm": -120.0,                   // RSRP threshold used
  "label_mode": "name",                      // Cell label format ("name" or "bxy")
  "num_reports": 30000,                      // Total UE reports for this run
  
  "metadata": {
    // Run identification
    "timestamp": "2025-01-15_12-30-45",
    "name": "baseline",                      // User-provided run name
    "unix_timestamp": 1736943045.123,
    
    // Network topology summary
    "num_users": 30000,
    "num_bands": 2,
    "bands": ["H", "L"],
    "timestep": 0,
    "timestep_minutes": null,
    
    // Initial configuration used to create simulation
    "init_config": {
      "n_sites": 10,
      "spacing": 500.0,
      "seed": 7,
      "jitter": 0.06,
      "site_height_m": 20.0,
      "fc_hi_hz": 2500000000.0,
      "tilt_hi_deg": 9.0,
      "bs_rows_hi": 8,
      "bs_cols_hi": 1,
      "antenna_pattern_hi": "38.901",
      "fc_lo_hz": 600000000.0,
      "tilt_lo_deg": 9.0,
      "bs_rows_lo": 8,
      "bs_cols_lo": 1,
      "antenna_pattern_lo": "38.901",
      "num_ue": 30000,
      "box_pad_m": 250.0,
      "cells_chunk": 48,
      "ue_chunk": 500
    },
    
    // Configuration summary
    "init_config_summary": {
      "n_sites": 10,
      "spacing_m": 500.0,
      "seed": 7,
      "site_height_m": 20.0,
      "high_band": {
        "fc_hz": 2500000000.0,
        "fc_ghz": 2.5,
        "tilt_deg": 9.0,
        "antenna": "8x1",
        "pattern": "38.901"
      },
      "low_band": {
        "fc_hz": 600000000.0,
        "fc_ghz": 0.6,
        "tilt_deg": 9.0,
        "antenna": "8x1",
        "pattern": "38.901"
      },
      "ues": {
        "num_ue": 30000,
        "box_pad_m": 250.0
      },
      "chunking": {
        "cells_chunk": 48,
        "ue_chunk": 500
      }
    },
    
    // COMPLETE CELL STATE SNAPSHOT at time of run
    "cell_states_at_run": [
      {
        "cell_idx": 0,
        "cell_name": "HSITE0001A1",
        "band": "H",
        "site_name": "SITE0001A",
        "site_uid": "SITE0001A",
        "site_idx": 0,
        "x": 159.15,
        "y": 0.0,
        "sector_id": 0,
        "sector_label": "1",
        "sector_az_deg": 180.0,
        "fc_hz": 2500000000.0,
        "fc_MHz": 2500.0,
        "fc_GHz": 2.5,
        "tx_rs_power_dbm": 0.0,
        "tilt_deg": 9.0,
        "roll_deg": 0.0,
        "height_m_effective": 20.0,
        "bs_rows": 8,
        "bs_cols": 1,
        "bs_pol": "dual",
        "bs_pol_type": "VH",
        "elem_v_spacing": 0.5,
        "elem_h_spacing": 0.5,
        "antenna_pattern": "38.901"
      },
      // ... (59 more cells)
    ]
  }
}
```

**Key Fields:**
- `_key`: Timestamp-based run ID (unique identifier)
- `created_at`: When the run was executed
- `threshold_dbm`: RSRP threshold used for filtering
- `num_reports`: Count of UE reports (for verification)
- `metadata.init_config`: **Full initial configuration** (reproducibility)
- `metadata.cell_states_at_run`: **Complete cell snapshot** at run time
  - Captures tilts, power, frequencies, antenna configs
  - Essential for understanding results context

**Indexes:** Primary key on `_key` (run_id)

---

### 2. `sim_reports` Collection

**Purpose:** Store per-UE RSRP measurement reports (sparse storage).

**Document Structure:**

```json
{
  "_key": "2025-01-15_12-30-45:user_000042",  // Composite: {run_id}:{user_id}
  "_id": "sim_reports/2025-01-15_12-30-45:user_000042",
  "_rev": "_hZ8kYYq---",
  
  "run_id": "2025-01-15_12-30-45",     // Links to sim_runs document
  "user_id": "user_000042",             // UE identifier
  
  "x": 123.45,                          // UE X coordinate (meters)
  "y": 678.90,                          // UE Y coordinate (meters)
  
  "readings": {                         // RSRP measurements (sparse)
    "HSITE0001A1": -82.5,               // Cell name: RSRP in dBm
    "LSITE0001A1": -88.2,
    "HSITE0002A2": -95.7,
    "LSITE0003A3": -105.3,
    "HSITE0004A1": -112.8
    // Only cells with RSRP >= threshold_dbm are stored
  }
}
```

**Key Fields:**
- `_key`: Composite key `{run_id}:{user_id}` for uniqueness
- `run_id`: Foreign key to `sim_runs._key`
- `user_id`: UE identifier (e.g., "user_000000", "user_029999")
- `x`, `y`: UE position in Cartesian coordinates (meters)
- `readings`: **Sparse dictionary** of cell measurements
  - Key: Cell name (from `cell_states_at_run`)
  - Value: RSRP in dBm
  - Only includes cells with RSRP ≥ `threshold_dbm`

**Storage Efficiency:**
- Typical network: 60 cells, 30k UEs
- Full matrix: 60 × 30,000 = 1.8M values
- Sparse storage (threshold -120 dBm): ~5-8 readings per UE
- Reduction: **90-95% smaller** than full matrix

**Indexes:** 
- Primary key on `_key`
- Index on `run_id` for efficient run-level queries

---

### 3. `saved_configs` Collection

**Purpose:** Store user-saved simulation configurations (named snapshots).

**Document Structure:**

```json
{
  "_key": "baseline",                   // Configuration name (user-provided)
  "_id": "saved_configs/baseline",
  "_rev": "_hZ8kZZq---",
  
  "config_name": "baseline",
  "description": "Initial baseline configuration before optimization",
  
  // Initial parameters used to create simulation
  "init_config": {
    "n_sites": 10,
    "spacing": 500.0,
    "seed": 7,
    // ... (same structure as sim_runs.metadata.init_config)
  },
  
  // Current cell states when config was saved
  "cells_state": [
    {
      "cell_idx": 0,
      "cell_name": "HSITE0001A1",
      "band": "H",
      "tilt_deg": 12.0,          // May differ from init_config if cells were updated
      "tx_rs_power_dbm": 3.0,    // May have been modified
      // ... (full cell state)
    }
    // ... (all cells)
  ],
  
  // Current UE configuration
  "ues_state": {
    "num_ues": 30000,
    "layout": "box",
    "drop_params": {
      "num_ue": 30000,
      "layout": "box",
      "center": [0.0, 0.0],
      "box_pad_m": 250.0,
      "box_bounds": [-475.0, 475.0, -475.0, 475.0],
      "height_m": 1.5,
      "seed": 7
    },
    "has_results": false
  },
  
  // Topology summary
  "topology": {
    "num_sites": 10,
    "num_cells": 60
  },
  
  // Metadata
  "metadata": {
    "created_at": "2025-01-15T14:20:30.456Z",
    "num_cells": 60,
    "num_sites": 10,
    "num_ues": 30000
  }
}
```

**Key Fields:**
- `_key`: Configuration name (user-provided, must be unique)
- `init_config`: **Original initialization parameters**
- `cells_state`: **Current cell configurations** (may differ from init)
- `ues_state`: UE drop configuration
- `metadata`: Summary and timestamp

**Use Cases:**
- Save configuration before making changes
- Compare different optimization scenarios
- Restore previous configurations
- Share configurations between sessions

**Indexes:** Primary key on `_key` (config_name)

---

### 4. `session_cache` Collection

**Purpose:** Temporary storage for current session state.

**Document Structure:**

```json
{
  "_key": "current_init",
  "_id": "session_cache/current_init",
  "_rev": "_hZ8k___---",
  
  "init_config": {
    "n_sites": 10,
    "spacing": 500.0,
    // ... (initialization parameters)
  },
  
  "saved_at": "2025-01-15T12:00:00.000Z"
}
```

**Key Fields:**
- `_key`: Fixed value "current_init"
- `init_config`: Most recent initialization parameters
- `saved_at`: Timestamp of last save

**Notes:**
- Overwritten on each new initialization
- Used by CLI backend for session continuity
- Not intended for long-term storage

---

## Data Relationships

```
sim_runs (1)
    ├── run_id = "_key"
    ├── metadata.cell_states_at_run[] (embedded)
    ├── metadata.init_config (embedded)
    └── (linked to) →
    
sim_reports (N)
    ├── run_id = sim_runs._key  (foreign key)
    ├── user_id
    ├── x, y
    └── readings{cell_name: rsrp_dbm}

saved_configs (independent)
    ├── config_name = "_key"
    ├── init_config (embedded)
    ├── cells_state[] (embedded)
    └── ues_state (embedded)
```

**Relationship Summary:**
- **sim_runs** ↔ **sim_reports**: One-to-many via `run_id`
- **saved_configs**: Independent (no foreign keys)
- All collections use document embedding (denormalized) for performance

---

## Query Examples

### Access ArangoDB Web UI

```bash
# Open in browser
http://localhost:8529

# Login credentials (default dev environment)
Username: root
Password: smartran-studio_dev_password
Database: smartran-studio_db
```

### AQL Query Examples

#### 1. List All Simulation Runs

```aql
FOR run IN sim_runs
  SORT run.created_at DESC
  RETURN {
    run_id: run._key,
    name: run.metadata.name,
    created_at: run.created_at,
    num_ues: run.metadata.num_users,
    num_sites: run.metadata.init_config_summary.n_sites,
    high_band_ghz: run.metadata.init_config_summary.high_band.fc_ghz,
    low_band_ghz: run.metadata.init_config_summary.low_band.fc_ghz
  }
```

#### 2. Get Complete Run Metadata

```aql
// Get run header with full configuration
RETURN DOCUMENT("sim_runs/2025-01-15_12-30-45")
```

#### 3. Get All UE Reports for a Run

```aql
FOR report IN sim_reports
  FILTER report.run_id == "2025-01-15_12-30-45"
  SORT report.user_id ASC
  RETURN report
```

#### 4. Get Specific UE Report

```aql
RETURN DOCUMENT("sim_reports/2025-01-15_12-30-45:user_000042")
```

#### 5. Get UE Reports with Location Filter

```aql
// UEs within bounding box
FOR report IN sim_reports
  FILTER report.run_id == "2025-01-15_12-30-45"
  FILTER report.x >= -100 AND report.x <= 100
  FILTER report.y >= -100 AND report.y <= 100
  RETURN report
```

#### 6. Get Best-Serving Cell Statistics

```aql
// Count UEs served by each cell
FOR report IN sim_reports
  FILTER report.run_id == "2025-01-15_12-30-45"
  
  // Find best cell (max RSRP) for this UE
  LET best_cell = (
    FOR cell_name IN ATTRIBUTES(report.readings)
      SORT report.readings[cell_name] DESC
      LIMIT 1
      RETURN cell_name
  )[0]
  
  COLLECT cell = best_cell WITH COUNT INTO count
  SORT count DESC
  RETURN {
    cell_name: cell,
    num_ues_served: count
  }
```

#### 7. Extract RSRP Distribution for a Cell

```aql
// Get all RSRP values for a specific cell
FOR report IN sim_reports
  FILTER report.run_id == "2025-01-15_12-30-45"
  FILTER report.readings["HSITE0001A1"] != null
  
  RETURN {
    user_id: report.user_id,
    x: report.x,
    y: report.y,
    rsrp_dbm: report.readings["HSITE0001A1"]
  }
```

#### 8. Compare Two Runs (Cell Tilts)

```aql
// Compare cell configurations between two runs
LET run1 = DOCUMENT("sim_runs/2025-01-15_12-30-45")
LET run2 = DOCUMENT("sim_runs/2025-01-15_14-20-30")

FOR cell1 IN run1.metadata.cell_states_at_run
  LET cell2 = (
    FOR c IN run2.metadata.cell_states_at_run
      FILTER c.cell_name == cell1.cell_name
      RETURN c
  )[0]
  
  FILTER cell1.tilt_deg != cell2.tilt_deg
  
  RETURN {
    cell_name: cell1.cell_name,
    run1_tilt: cell1.tilt_deg,
    run2_tilt: cell2.tilt_deg,
    delta: cell2.tilt_deg - cell1.tilt_deg
  }
```

#### 9. Export UE Reports to JSON (via ArangoDB UI)

```aql
// Run in ArangoDB Web UI, then download results
FOR report IN sim_reports
  FILTER report.run_id == "2025-01-15_12-30-45"
  LIMIT 1000  // Adjust limit as needed
  RETURN report
```

Click "Download" button to save as JSON file.

#### 10. List Saved Configurations

```aql
FOR config IN saved_configs
  SORT config.metadata.created_at DESC
  RETURN {
    name: config.config_name,
    description: config.description,
    num_sites: config.metadata.num_sites,
    num_cells: config.metadata.num_cells,
    num_ues: config.metadata.num_ues,
    created_at: config.metadata.created_at
  }
```

---

## Python Access Examples

### Using python-arango Library

```python
from arango import ArangoClient
import pandas as pd

# Connect
client = ArangoClient(hosts='http://localhost:8529')
db = client.db('smartran-studio_db', username='root', password='smartran-studio_dev_password')

# Get run metadata
run = db.collection('sim_runs').get('2025-01-15_12-30-45')
print(f"Run: {run['metadata']['name']}")
print(f"Sites: {run['metadata']['init_config_summary']['n_sites']}")
print(f"UEs: {run['metadata']['num_users']}")

# Get all UE reports for a run
query = """
FOR report IN sim_reports
  FILTER report.run_id == @run_id
  RETURN report
"""
reports = db.aql.execute(query, bind_vars={'run_id': '2025-01-15_12-30-45'})

# Convert to DataFrame
df = pd.DataFrame(list(reports))
print(df.head())

# Access cell states snapshot
cells = run['metadata']['cell_states_at_run']
cells_df = pd.DataFrame(cells)
print(cells_df[['cell_name', 'band', 'tilt_deg', 'tx_rs_power_dbm']])
```

### Extract Specific UE Report

```python
# Get report for specific UE
report = db.collection('sim_reports').get('2025-01-15_12-30-45:user_000042')

print(f"UE Position: ({report['x']:.2f}, {report['y']:.2f})")
print(f"Number of cells detected: {len(report['readings'])}")

# Sort cells by RSRP
sorted_cells = sorted(report['readings'].items(), key=lambda x: x[1], reverse=True)
print("\nTop 5 cells:")
for cell_name, rsrp in sorted_cells[:5]:
    print(f"  {cell_name}: {rsrp:.2f} dBm")
```

---

## REST API Access

### Via SmartRAN Studio API

```bash
# List all runs
curl http://localhost:8000/runs

# Get run metadata
curl http://localhost:8000/runs/2025-01-15_12-30-45

# Get UE reports (paginated)
curl "http://localhost:8000/runs/2025-01-15_12-30-45/reports?limit=1000&offset=0"

# Get reports for specific UE range
curl "http://localhost:8000/runs/2025-01-15_12-30-45/reports?user_id_min=0&user_id_max=1000"
```

### Response Format

```json
{
  "run_id": "2025-01-15_12-30-45",
  "reports": [
    {
      "user_id": "user_000042",
      "x": 123.45,
      "y": 678.90,
      "readings": {
        "HSITE0001A1": -82.5,
        "LSITE0001A1": -88.2
      }
    }
  ],
  "total": 30000,
  "limit": 1000,
  "offset": 0,
  "status": "success"
}
```

---

## Data Export Strategies

### Strategy 1: ArangoDB Web UI Export

1. Open http://localhost:8529
2. Navigate to "Queries"
3. Run AQL query (see examples above)
4. Click "Download" → Choose JSON or CSV

**Best for:** Small to medium datasets (< 100k records)

### Strategy 2: Python Batch Export

```python
import json
from arango import ArangoClient

client = ArangoClient(hosts='http://localhost:8529')
db = client.db('smartran-studio_db', username='root', password='smartran-studio_dev_password')

run_id = '2025-01-15_12-30-45'
batch_size = 5000

# Export in batches
with open(f'{run_id}_reports.jsonl', 'w') as f:
    offset = 0
    while True:
        query = f"""
        FOR report IN sim_reports
          FILTER report.run_id == @run_id
          SORT report.user_id ASC
          LIMIT @offset, @batch_size
          RETURN report
        """
        
        batch = db.aql.execute(
            query, 
            bind_vars={'run_id': run_id, 'offset': offset, 'batch_size': batch_size}
        )
        batch_list = list(batch)
        
        if not batch_list:
            break
        
        for doc in batch_list:
            f.write(json.dumps(doc) + '\n')
        
        offset += batch_size
        print(f"Exported {offset} reports...")

print("Export complete!")
```

**Best for:** Large datasets (100k+ records)

### Strategy 3: Direct CSV Export

```python
import csv
import pandas as pd

# Get reports
reports = list(db.aql.execute("""
FOR report IN sim_reports
  FILTER report.run_id == @run_id
  RETURN report
""", bind_vars={'run_id': '2025-01-15_12-30-45'}))

# Flatten readings into columns
rows = []
for report in reports:
    row = {
        'user_id': report['user_id'],
        'x': report['x'],
        'y': report['y']
    }
    row.update(report['readings'])  # Add all cell readings as columns
    rows.append(row)

# Convert to DataFrame and export
df = pd.DataFrame(rows)
df.to_csv('ue_reports.csv', index=False)
```

**Best for:** Analysis in Excel, MATLAB, R

---

## Storage Estimates

### Typical Simulation Run
- **Configuration:** 10 sites, 60 cells, 30,000 UEs
- **Threshold:** -120 dBm

**Storage Breakdown:**

| Component | Document Count | Size per Doc | Total Size |
|-----------|---------------|--------------|------------|
| Run header (`sim_runs`) | 1 | ~50 KB | 50 KB |
| UE reports (`sim_reports`) | 30,000 | ~200 bytes | ~6 MB |
| **Total per run** | **30,001** | - | **~6 MB** |

**Scaling:**
- 100 runs: ~600 MB
- 1,000 runs: ~6 GB
- 10,000 runs: ~60 GB

**Notes:**
- Cell states snapshot adds ~1 KB per cell to run header
- Sparse storage crucial for efficiency (5-10 cells per UE vs 60 full matrix)
- Indexes add ~10% overhead

---

## Best Practices

### 1. Data Retention
```aql
// Delete old runs (keep last 30 days)
FOR run IN sim_runs
  FILTER DATE_DIFF(run.created_at, DATE_NOW(), 'd') > 30
  
  // Delete associated reports
  FOR report IN sim_reports
    FILTER report.run_id == run._key
    REMOVE report IN sim_reports
  
  // Delete run header
  REMOVE run IN sim_runs
```

### 2. Query Performance
- Always filter by `run_id` first
- Use LIMIT for large result sets
- Create indexes on frequently queried fields
- Consider aggregations over full scans

### 3. Data Integrity
- Always save run metadata with results
- Include complete cell states snapshot in run header
- Use descriptive run names in metadata
- Document threshold_dbm and label_mode used

### 4. Backup Strategy
```bash
# Backup entire database
docker exec smartran-studio-arangodb arangodump \
  --server.database smartran-studio_db \
  --output-directory /var/lib/arangodb3/backups/backup-$(date +%Y%m%d)

# Restore from backup
docker exec smartran-studio-arangodb arangorestore \
  --server.database smartran-studio_db \
  --input-directory /var/lib/arangodb3/backups/backup-20250115
```

---

## Troubleshooting

### Connection Issues

```python
# Test connection
from arango import ArangoClient

try:
    client = ArangoClient(hosts='http://localhost:8529')
    db = client.db('smartran-studio_db', username='root', password='smartran-studio_dev_password')
    print(f"✓ Connected to database: {db.name}")
    print(f"✓ Collections: {[c['name'] for c in db.collections()]}")
except Exception as e:
    print(f"✗ Connection failed: {e}")
```

### Missing Data

```aql
// Check if run exists
RETURN DOCUMENT("sim_runs/2025-01-15_12-30-45")

// Count reports for run
RETURN LENGTH(
  FOR report IN sim_reports
    FILTER report.run_id == "2025-01-15_12-30-45"
    RETURN 1
)
```

### Performance Issues

```aql
// Check collection sizes
FOR c IN COLLECTIONS()
  RETURN {
    name: c.name,
    count: LENGTH(c),
    type: c.type
  }
```

---

## See Also

- [SmartRAN Studio Architecture](ARCHITECTURE.md)
- [API Reference](../smartran-studio-sim-engine/README.md)
- [ArangoDB Documentation](https://www.arangodb.com/docs/)
- [Python-Arango Documentation](https://docs.python-arango.com/)

---

**Last Updated:** November 2024  
**Database Version:** ArangoDB 3.11+  
**Schema Version:** 1.0

