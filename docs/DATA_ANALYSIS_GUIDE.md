# Data Analysis Guide

Complete guide to running simulations, extracting results, and analyzing RF propagation data in SmartRAN Studio.

---

## Table of Contents

1. [Overview](#overview)
2. [Complete Workflow](#complete-workflow)
3. [Running Simulations](#running-simulations)
4. [Extracting Results](#extracting-results)
5. [Analysis Examples](#analysis-examples)
6. [Troubleshooting](#troubleshooting)

---

## Overview

SmartRAN Studio workflow:

```
1. SETUP           2. CONFIGURE        3. COMPUTE         4. EXTRACT         5. ANALYZE
┌────────────┐    ┌────────────┐    ┌────────────┐    ┌────────────┐    ┌────────────┐
│ Initialize │ -> │ Update     │ -> │ Run        │ -> │ Query      │ -> │ Visualize  │
│ Simulation │    │ Parameters │    │ Compute    │    │ Database   │    │ Results    │
└────────────┘    └────────────┘    └────────────┘    └────────────┘    └────────────┘
                                           │
                                           ▼
                                    ┌──────────────┐
                                    │   ArangoDB   │
                                    │  sim_runs    │
                                    │ sim_reports  │
                                    └──────────────┘
```

**Key Concepts:**
- **Simulation Run**: One compute execution, stored with unique timestamp ID
- **Run Metadata**: Configuration snapshot, cell states, parameters (in `sim_runs`)
- **UE Reports**: Per-user RSRP measurements (in `sim_reports`)
- **Sparse Storage**: Only cells above threshold stored per UE (90% reduction)

---

## Complete Workflow

### Step 1: Initialize Simulation

```bash
# Open web CLI at http://localhost:8080

# Initialize with defaults (10 sites, 30k UEs)
srs init --default
```

**What this does:**
- Creates 10 tri-sector sites with dual-band cells (2.5 GHz + 600 MHz)
- Drops 30,000 UEs in box layout
- Configures simulation ready for compute

**Verify initialization:**
```bash
srs status
```

Output shows:
- Number of sites, cells, UEs
- Frequency bands
- Current configuration

### Step 2: Configure Network (Optional)

Update cell parameters before compute:

```bash
# Update specific cell tilt
srs update cell 0 --tilt=12.0

# Bulk update all high-band cells
srs update cells query --band=H --tilt=11.0

# Update power levels
srs update cells query --site=SITE0001A --power=3.0
```

**Query current configuration:**
```bash
srs query cells
srs query cells --band=H
srs query sites
```

### Step 3: Run Simulation Compute

```bash
# Run compute and save with descriptive name
srs sim compute --name="baseline"
```

**What this does:**
1. Computes RSRP for all 30k UEs × 60 cells on GPU
2. Applies -120 dBm threshold (only cells above this are stored)
3. Saves complete snapshot to database:
   - Run metadata (configuration, cell states, timestamp)
   - Per-UE measurements (sparse RSRP matrix)

**Typical performance:** 5-10 seconds on RTX 4060 Laptop GPU

**Output shows:**
- Run ID (timestamp): `2025-01-20_14-30-45`
- Number of reports stored
- Storage location in database

### Step 4: Verify Data in Database

#### Option A: Web CLI
```bash
srs snapshot list
```

Shows all saved runs with metadata.

#### Option B: ArangoDB Web UI

1. Open http://localhost:8529
2. Login:
   - Username: `root`
   - Password: (from your `compose.yaml`)
3. Select database: `smartran-studio_db`
4. Navigate to Collections:
   - `sim_runs` - Run headers
   - `sim_reports` - UE measurements

**View a run:**
```aql
RETURN DOCUMENT("sim_runs/2025-01-20_14-30-45")
```

**Count UE reports:**
```aql
RETURN LENGTH(
  FOR report IN sim_reports
    FILTER report.run_id == "2025-01-20_14-30-45"
    RETURN 1
)
```

### Step 5: Extract Results

Now you have three options for data extraction.

---

## Extracting Results

### Method 1: REST API (Programmatic Access)

#### Get Run Metadata
```bash
curl http://localhost:8000/runs/2025-01-20_14-30-45 | jq .
```

Response includes:
- Complete initialization configuration
- Cell states snapshot at run time
- Run timestamp and parameters

#### Get UE Reports (Paginated)
```bash
# First 1000 reports
curl "http://localhost:8000/runs/2025-01-20_14-30-45/reports?limit=1000&offset=0" | jq .

# Next 1000 reports
curl "http://localhost:8000/runs/2025-01-20_14-30-45/reports?limit=1000&offset=1000" | jq .
```

#### Filter by UE Range
```bash
# Get reports for UEs 0-999 only
curl "http://localhost:8000/runs/2025-01-20_14-30-45/reports?user_id_min=0&user_id_max=999" | jq .
```

### Method 2: ArangoDB AQL Queries

#### List All Runs
```aql
FOR run IN sim_runs
  SORT run.created_at DESC
  RETURN {
    run_id: run._key,
    name: run.metadata.name,
    created_at: run.created_at,
    num_ues: run.metadata.num_users,
    num_sites: run.metadata.init_config_summary.n_sites
  }
```

#### Get All Reports for a Run
```aql
FOR report IN sim_reports
  FILTER report.run_id == "2025-01-20_14-30-45"
  SORT report.user_id ASC
  RETURN report
```

Download as JSON from Web UI.

#### Get UEs in Geographic Area
```aql
FOR report IN sim_reports
  FILTER report.run_id == "2025-01-20_14-30-45"
  FILTER report.x >= -200 AND report.x <= 200
  FILTER report.y >= -200 AND report.y <= 200
  RETURN {
    user_id: report.user_id,
    x: report.x,
    y: report.y,
    num_cells_detected: LENGTH(ATTRIBUTES(report.readings)),
    best_cell: (
      FOR cell IN ATTRIBUTES(report.readings)
        SORT report.readings[cell] DESC
        LIMIT 1
        RETURN cell
    )[0],
    best_rsrp: MAX(VALUES(report.readings))
  }
```

### Method 3: Python with pandas

Create `extract_data.py`:

```python
#!/usr/bin/env python3
"""
Extract and analyze SmartRAN Studio simulation results
"""
import os
import pandas as pd
from arango import ArangoClient

# Connect to database (reads from environment)
client = ArangoClient(hosts=os.getenv('ARANGO_HOST', 'http://localhost:8529'))
db = client.db(
    os.getenv('ARANGO_DATABASE', 'smartran-studio_db'),
    username=os.getenv('ARANGO_USERNAME', 'root'),
    password=os.getenv('ARANGO_PASSWORD', 'smartran-studio_dev_password')
)

def get_run_metadata(run_id):
    """Get complete run metadata"""
    run = db.collection('sim_runs').get(run_id)
    if not run:
        raise ValueError(f"Run {run_id} not found")
    return run

def get_all_reports(run_id):
    """Get all UE reports as DataFrame"""
    query = """
    FOR report IN sim_reports
      FILTER report.run_id == @run_id
      SORT report.user_id ASC
      RETURN report
    """
    
    cursor = db.aql.execute(query, bind_vars={'run_id': run_id})
    reports = list(cursor)
    
    # Convert to DataFrame
    df = pd.DataFrame(reports)
    print(f"Loaded {len(df)} UE reports")
    return df

def expand_rsrp_matrix(df):
    """
    Expand sparse readings into wide format (one column per cell)
    
    Input:  DataFrame with 'readings' column containing {cell: rsrp} dicts
    Output: DataFrame with separate column for each cell
    """
    # Extract readings into separate columns
    readings_df = pd.DataFrame(df['readings'].tolist())
    
    # Combine with UE metadata
    result = pd.concat([
        df[['user_id', 'x', 'y']].reset_index(drop=True),
        readings_df
    ], axis=1)
    
    print(f"Expanded to {len(readings_df.columns)} cell columns")
    return result

def get_cell_states(run_id):
    """Get cell configuration snapshot at run time"""
    run = get_run_metadata(run_id)
    cells = run['metadata']['cell_states_at_run']
    return pd.DataFrame(cells)

def analyze_serving_cells(df):
    """
    Compute best-serving cell per UE
    
    Args:
        df: DataFrame with expanded RSRP matrix (from expand_rsrp_matrix)
    
    Returns:
        DataFrame with user_id, x, y, best_cell, best_rsrp
    """
    # Get cell columns (exclude metadata)
    cell_cols = [c for c in df.columns if c not in ['user_id', 'x', 'y', '_key', '_id', '_rev', 'run_id']]
    
    # Find best cell and RSRP per UE
    result = df[['user_id', 'x', 'y']].copy()
    result['best_cell'] = df[cell_cols].idxmax(axis=1)
    result['best_rsrp'] = df[cell_cols].max(axis=1)
    
    return result

# Example usage
if __name__ == '__main__':
    run_id = '2025-01-20_14-30-45'  # Replace with your run ID
    
    print(f"Extracting data for run: {run_id}")
    print("=" * 60)
    
    # Get run metadata
    metadata = get_run_metadata(run_id)
    print(f"Run: {metadata['metadata']['name']}")
    print(f"Created: {metadata['created_at']}")
    print(f"UEs: {metadata['metadata']['num_users']}")
    print(f"Sites: {metadata['metadata']['init_config_summary']['n_sites']}")
    print()
    
    # Get cell states
    cells_df = get_cell_states(run_id)
    print(f"Loaded {len(cells_df)} cells")
    print(cells_df[['cell_name', 'band', 'tilt_deg', 'tx_rs_power_dbm']].head())
    print()
    
    # Get UE reports
    reports_df = get_all_reports(run_id)
    print()
    
    # Expand to wide format
    rsrp_matrix = expand_rsrp_matrix(reports_df)
    print()
    
    # Analyze serving cells
    serving = analyze_serving_cells(rsrp_matrix)
    print("Best-serving cell statistics:")
    print(serving['best_cell'].value_counts().head(10))
    print()
    
    # Save to CSV
    rsrp_matrix.to_csv(f'{run_id}_rsrp_matrix.csv', index=False)
    serving.to_csv(f'{run_id}_serving_cells.csv', index=False)
    cells_df.to_csv(f'{run_id}_cell_config.csv', index=False)
    
    print(f"✅ Saved files:")
    print(f"  - {run_id}_rsrp_matrix.csv (full RSRP matrix)")
    print(f"  - {run_id}_serving_cells.csv (serving cell per UE)")
    print(f"  - {run_id}_cell_config.csv (cell configuration)")
```

**Run the script:**
```bash
# Set credentials
export ARANGO_HOST=http://localhost:8529
export ARANGO_USERNAME=root
export ARANGO_PASSWORD=smartran-studio_dev_password
export ARANGO_DATABASE=smartran-studio_db

# Run extraction
python extract_data.py
```

---

## Analysis Examples

### Example 1: Coverage Analysis

**Question:** What percentage of UEs have RSRP ≥ -100 dBm from their best cell?

```python
import pandas as pd

# Load serving cells data
serving = pd.read_csv('2025-01-20_14-30-45_serving_cells.csv')

# Coverage thresholds
excellent = (serving['best_rsrp'] >= -80).sum()
good = (serving['best_rsrp'] >= -100).sum()
fair = (serving['best_rsrp'] >= -110).sum()
poor = (serving['best_rsrp'] >= -120).sum()

total = len(serving)

print("Coverage Statistics:")
print(f"Excellent (≥-80 dBm):  {excellent:5d} ({excellent/total*100:.1f}%)")
print(f"Good (≥-100 dBm):      {good:5d} ({good/total*100:.1f}%)")
print(f"Fair (≥-110 dBm):      {fair:5d} ({fair/total*100:.1f}%)")
print(f"Poor (≥-120 dBm):      {poor:5d} ({poor/total*100:.1f}%)")
```

### Example 2: Cell Load Distribution

**Question:** How many UEs is each cell serving?

```python
import pandas as pd
import matplotlib.pyplot as plt

serving = pd.read_csv('2025-01-20_14-30-45_serving_cells.csv')
cells = pd.read_csv('2025-01-20_14-30-45_cell_config.csv')

# Count UEs per cell
load = serving['best_cell'].value_counts().reset_index()
load.columns = ['cell_name', 'num_ues']

# Merge with cell configuration
load = load.merge(cells[['cell_name', 'band', 'tilt_deg', 'site_name']], on='cell_name')

# Statistics
print("Load Distribution:")
print(f"Mean UEs/cell: {load['num_ues'].mean():.0f}")
print(f"Max UEs/cell:  {load['num_ues'].max()}")
print(f"Min UEs/cell:  {load['num_ues'].min()}")
print(f"Std dev:       {load['num_ues'].std():.1f}")

# Top 10 loaded cells
print("\nTop 10 loaded cells:")
print(load.nlargest(10, 'num_ues')[['cell_name', 'num_ues', 'band', 'tilt_deg', 'site_name']])

# Plot histogram
plt.figure(figsize=(10, 6))
plt.hist(load['num_ues'], bins=30, edgecolor='black')
plt.xlabel('Number of UEs Served')
plt.ylabel('Number of Cells')
plt.title('Cell Load Distribution')
plt.grid(True, alpha=0.3)
plt.savefig('cell_load_distribution.png', dpi=150, bbox_inches='tight')
print("\n✅ Saved: cell_load_distribution.png")
```

### Example 3: Geographic Coverage Heatmap

**Question:** Visualize RSRP across the simulation area

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

serving = pd.read_csv('2025-01-20_14-30-45_serving_cells.csv')

# Create 2D heatmap
plt.figure(figsize=(12, 10))

# Scatter plot colored by RSRP
scatter = plt.scatter(
    serving['x'], 
    serving['y'], 
    c=serving['best_rsrp'],
    cmap='RdYlGn',  # Red (poor) to Green (good)
    s=2,
    vmin=-120,
    vmax=-60,
    alpha=0.6
)

plt.colorbar(scatter, label='RSRP (dBm)')
plt.xlabel('X Position (m)')
plt.ylabel('Y Position (m)')
plt.title('Best-Cell RSRP Coverage Map')
plt.grid(True, alpha=0.3)
plt.axis('equal')
plt.savefig('coverage_heatmap.png', dpi=150, bbox_inches='tight')
print("✅ Saved: coverage_heatmap.png")
```

### Example 4: Band Comparison

**Question:** Are high-band or low-band cells serving more UEs?

```python
import pandas as pd

serving = pd.read_csv('2025-01-20_14-30-45_serving_cells.csv')
cells = pd.read_csv('2025-01-20_14-30-45_cell_config.csv')

# Get band for each UE's serving cell
serving_with_band = serving.merge(
    cells[['cell_name', 'band', 'fc_GHz']], 
    left_on='best_cell', 
    right_on='cell_name',
    how='left'
)

# Count by band
band_counts = serving_with_band['band'].value_counts()
print("UEs Served by Band:")
print(band_counts)
print(f"\nHigh band: {band_counts.get('H', 0)} ({band_counts.get('H', 0)/len(serving)*100:.1f}%)")
print(f"Low band:  {band_counts.get('L', 0)} ({band_counts.get('L', 0)/len(serving)*100:.1f}%)")

# Average RSRP by band
rsrp_by_band = serving_with_band.groupby('band')['best_rsrp'].agg(['mean', 'std', 'min', 'max'])
print("\nRSRP by Band:")
print(rsrp_by_band)
```

### Example 5: Site Coverage Comparison

**Question:** Which sites are covering the most area/UEs?

```python
import pandas as pd

serving = pd.read_csv('2025-01-20_14-30-45_serving_cells.csv')
cells = pd.read_csv('2025-01-20_14-30-45_cell_config.csv')

# Get site for each serving cell
serving_with_site = serving.merge(
    cells[['cell_name', 'site_name']], 
    left_on='best_cell', 
    right_on='cell_name'
)

# Count UEs per site
site_load = serving_with_site['site_name'].value_counts().reset_index()
site_load.columns = ['site_name', 'num_ues']

# Merge with site positions
site_info = cells.groupby('site_name')[['x', 'y']].first().reset_index()
site_load = site_load.merge(site_info, on='site_name')

print("Site Coverage (Top 10):")
print(site_load.nlargest(10, 'num_ues'))

# Average RSRP per site
site_rsrp = serving_with_site.groupby('site_name')['best_rsrp'].mean().reset_index()
site_rsrp.columns = ['site_name', 'avg_rsrp']
site_load = site_load.merge(site_rsrp, on='site_name')

print("\nSite Performance Summary:")
print(site_load[['site_name', 'num_ues', 'avg_rsrp']].to_string(index=False))
```

### Example 6: Tilt Optimization Analysis

**Scenario:** Compare two runs with different tilt settings

```python
import pandas as pd

# Load baseline
baseline_serving = pd.read_csv('2025-01-20_14-30-45_serving_cells.csv')
baseline_cells = pd.read_csv('2025-01-20_14-30-45_cell_config.csv')

# Load optimized (after changing tilts)
optimized_serving = pd.read_csv('2025-01-20_15-00-00_serving_cells.csv')
optimized_cells = pd.read_csv('2025-01-20_15-00-00_cell_config.csv')

# Compare cell configurations
tilt_changes = baseline_cells[['cell_name', 'tilt_deg']].merge(
    optimized_cells[['cell_name', 'tilt_deg']], 
    on='cell_name', 
    suffixes=('_baseline', '_optimized')
)
tilt_changes['delta'] = tilt_changes['tilt_deg_optimized'] - tilt_changes['tilt_deg_baseline']

print("Cells with Changed Tilts:")
print(tilt_changes[tilt_changes['delta'] != 0])

# Compare coverage performance
baseline_good = (baseline_serving['best_rsrp'] >= -100).sum()
optimized_good = (optimized_serving['best_rsrp'] >= -100).sum()

print("\nCoverage Comparison (≥-100 dBm):")
print(f"Baseline:  {baseline_good} ({baseline_good/len(baseline_serving)*100:.1f}%)")
print(f"Optimized: {optimized_good} ({optimized_good/len(optimized_serving)*100:.1f}%)")
print(f"Change:    {optimized_good - baseline_good} UEs ({(optimized_good - baseline_good)/len(baseline_serving)*100:.2f}%)")

# Compare load distribution
baseline_load_std = baseline_serving['best_cell'].value_counts().std()
optimized_load_std = optimized_serving['best_cell'].value_counts().std()

print("\nLoad Balance (lower std = better balance):")
print(f"Baseline std:  {baseline_load_std:.1f}")
print(f"Optimized std: {optimized_load_std:.1f}")
print(f"Improvement:   {baseline_load_std - optimized_load_std:.1f}")
```

---

## Complete Analysis Script Template

Save as `analyze_simulation.py`:

```python
#!/usr/bin/env python3
"""
Complete SmartRAN Studio simulation analysis pipeline
"""
import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from arango import ArangoClient

# ============================================================================
# Configuration
# ============================================================================
RUN_ID = sys.argv[1] if len(sys.argv) > 1 else '2025-01-20_14-30-45'

# Database connection
client = ArangoClient(hosts=os.getenv('ARANGO_HOST', 'http://localhost:8529'))
db = client.db(
    os.getenv('ARANGO_DATABASE', 'smartran-studio_db'),
    username=os.getenv('ARANGO_USERNAME', 'root'),
    password=os.getenv('ARANGO_PASSWORD')
)

# ============================================================================
# Data Extraction
# ============================================================================
def extract_all_data(run_id):
    """Extract complete dataset for analysis"""
    print(f"Extracting data for run: {run_id}")
    
    # Run metadata
    run = db.collection('sim_runs').get(run_id)
    if not run:
        raise ValueError(f"Run {run_id} not found")
    
    # UE reports
    query = """
    FOR report IN sim_reports
      FILTER report.run_id == @run_id
      RETURN report
    """
    reports = list(db.aql.execute(query, bind_vars={'run_id': run_id}))
    
    # Cell states
    cells = pd.DataFrame(run['metadata']['cell_states_at_run'])
    
    # Process UE data
    ue_data = []
    for report in reports:
        if not report['readings']:
            continue
        
        best_cell = max(report['readings'].items(), key=lambda x: x[1])
        
        ue_data.append({
            'user_id': report['user_id'],
            'x': report['x'],
            'y': report['y'],
            'best_cell': best_cell[0],
            'best_rsrp': best_cell[1],
            'num_cells': len(report['readings'])
        })
    
    ues = pd.DataFrame(ue_data)
    
    return run, cells, ues

# ============================================================================
# Analysis Functions
# ============================================================================
def analyze_coverage(ues):
    """Coverage statistics"""
    thresholds = [-80, -90, -100, -110, -120]
    results = {}
    
    for thresh in thresholds:
        count = (ues['best_rsrp'] >= thresh).sum()
        pct = count / len(ues) * 100
        results[thresh] = {'count': count, 'percentage': pct}
    
    return results

def analyze_load_balance(ues):
    """Cell load distribution"""
    load = ues['best_cell'].value_counts()
    return {
        'mean': load.mean(),
        'std': load.std(),
        'min': load.min(),
        'max': load.max(),
        'cv': load.std() / load.mean()  # Coefficient of variation
    }

def analyze_band_performance(ues, cells):
    """Performance by frequency band"""
    ues_with_band = ues.merge(
        cells[['cell_name', 'band', 'fc_GHz']], 
        left_on='best_cell', 
        right_on='cell_name'
    )
    
    return ues_with_band.groupby('band').agg({
        'user_id': 'count',
        'best_rsrp': ['mean', 'std', 'min', 'max']
    })

# ============================================================================
# Visualization
# ============================================================================
def plot_coverage_map(ues, cells, output_file):
    """Coverage heatmap"""
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # UEs colored by RSRP
    scatter = ax.scatter(
        ues['x'], ues['y'],
        c=ues['best_rsrp'],
        cmap='RdYlGn',
        s=2,
        vmin=-120,
        vmax=-60,
        alpha=0.6
    )
    
    # Sites as triangles
    sites = cells.groupby('site_name')[['x', 'y']].first()
    ax.scatter(sites['x'], sites['y'], marker='^', s=200, 
               c='black', edgecolors='white', linewidths=2, zorder=10)
    
    plt.colorbar(scatter, label='RSRP (dBm)', ax=ax)
    ax.set_xlabel('X Position (m)')
    ax.set_ylabel('Y Position (m)')
    ax.set_title(f'Coverage Map - Run {RUN_ID}')
    ax.grid(True, alpha=0.3)
    ax.axis('equal')
    
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✅ Saved: {output_file}")

def plot_load_distribution(ues, output_file):
    """Cell load histogram"""
    load = ues['best_cell'].value_counts()
    
    plt.figure(figsize=(10, 6))
    plt.hist(load.values, bins=30, edgecolor='black', alpha=0.7)
    plt.xlabel('UEs Served per Cell')
    plt.ylabel('Number of Cells')
    plt.title(f'Cell Load Distribution - Run {RUN_ID}')
    plt.axvline(load.mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {load.mean():.0f}')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✅ Saved: {output_file}")

# ============================================================================
# Main Analysis Pipeline
# ============================================================================
def main():
    print("=" * 80)
    print(f"SmartRAN Studio Simulation Analysis - Run {RUN_ID}")
    print("=" * 80)
    
    # Extract data
    run, cells, ues = extract_all_data(RUN_ID)
    
    print(f"\nDataset Summary:")
    print(f"  Sites: {run['metadata']['init_config_summary']['n_sites']}")
    print(f"  Cells: {len(cells)}")
    print(f"  UEs:   {len(ues)}")
    
    # Coverage analysis
    print("\n" + "=" * 80)
    print("COVERAGE ANALYSIS")
    print("=" * 80)
    coverage = analyze_coverage(ues)
    for thresh, stats in sorted(coverage.items(), reverse=True):
        print(f"RSRP ≥ {thresh:4d} dBm: {stats['count']:5d} UEs ({stats['percentage']:5.1f}%)")
    
    # Load balance
    print("\n" + "=" * 80)
    print("LOAD BALANCE")
    print("=" * 80)
    load = analyze_load_balance(ues)
    print(f"Mean UEs/cell:  {load['mean']:.1f}")
    print(f"Std deviation:  {load['std']:.1f}")
    print(f"Min/Max:        {load['min']} / {load['max']}")
    print(f"CV (std/mean):  {load['cv']:.3f}")
    
    # Band performance
    print("\n" + "=" * 80)
    print("BAND PERFORMANCE")
    print("=" * 80)
    band_perf = analyze_band_performance(ues, cells)
    print(band_perf)
    
    # Generate plots
    print("\n" + "=" * 80)
    print("GENERATING PLOTS")
    print("=" * 80)
    plot_coverage_map(ues, cells, f'{RUN_ID}_coverage_map.png')
    plot_load_distribution(ues, f'{RUN_ID}_load_dist.png')
    
    # Save CSV exports
    print("\n" + "=" * 80)
    print("EXPORTING DATA")
    print("=" * 80)
    ues.to_csv(f'{RUN_ID}_ue_data.csv', index=False)
    cells.to_csv(f'{RUN_ID}_cell_config.csv', index=False)
    print(f"✅ Saved: {RUN_ID}_ue_data.csv")
    print(f"✅ Saved: {RUN_ID}_cell_config.csv")
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    main()
```

**Run complete analysis:**
```bash
export ARANGO_PASSWORD=your_password
python analyze_simulation.py 2025-01-20_14-30-45
```

---

## Troubleshooting

### Issue: "Run not found"

**Check run exists:**
```bash
curl http://localhost:8000/runs | jq '.runs[].run_id'
```

Or in ArangoDB:
```aql
FOR run IN sim_runs
  RETURN run._key
```

### Issue: Empty readings in reports

**Cause:** Threshold too high, no cells above threshold for that UE

**Check threshold used:**
```aql
FOR run IN sim_runs
  FILTER run._key == "2025-01-20_14-30-45"
  RETURN run.threshold_dbm
```

**Solution:** Run compute again with lower threshold:
```bash
# Currently threshold is fixed at -120 dBm in code
# Future: make threshold configurable
```

### Issue: Python script connection error

**Verify environment variables:**
```bash
echo $ARANGO_HOST
echo $ARANGO_USERNAME
echo $ARANGO_PASSWORD
echo $ARANGO_DATABASE
```

**Test connection:**
```bash
cd smartran-studio-interface/interface_db
python test_connection.py
```

### Issue: Large CSV files

**Solution:** Process in chunks

```python
# Read in chunks
chunk_size = 10000
for chunk in pd.read_csv('large_file.csv', chunksize=chunk_size):
    process(chunk)
```

---

## See Also

- **[Database Schema Reference](DATABASE_SCHEMA.md)** - Complete schema documentation
- **[CLI Reference](CLI_REFERENCE.md)** - All CLI commands
- **[Getting Started Guide](GETTING_STARTED.md)** - Basic setup
- **[Configuration Guide](CONFIGURATION.md)** - Credential management

---

**Last Updated:** November 2025  
**Version:** 1.0

