# Dynamic Site and Cell Management

This guide covers the new capabilities for dynamically adding sites and cells to your simulation after initialization.

## Overview

You can now:
- ✅ Initialize with random seed placement (existing capability)
- ✅ Initialize with zero sites and manually place everything
- ✅ Add new sites post-initialization at any coordinates
- ✅ Add cells to existing sites at any time
- ✅ Maintain strict naming convention enforcement (CNS####A)

## Naming Convention Rules

**ENFORCED RULES:**
1. Site names follow: `CNS####A` where #### is a 4-digit number (e.g., CNS0001A, CNS0002A)
2. Site numbers are auto-assigned as next available (you cannot skip numbers)
3. Every cell MUST belong to a site (no orphan cells)
4. You can add cells to existing sites, but cannot create cells without a site

## Initialization Options

### Option 1: Standard Random Initialization (Existing)
```bash
# Initialize with 10 sites using seed placement
cns init --default

# Or custom configuration
cns init --config '{"n_sites": 20, "spacing": 600, "seed": 42}'
```

### Option 2: Empty Initialization (Start from Scratch)
```bash
# Initialize with zero sites - manual placement mode
cns init --config '{"n_sites": 0, "num_ue": 10000}'
```

Now you have an empty simulation with just UEs, and you can place sites wherever you want.

## Adding Sites

### Add Site with No Cells
```bash
cns site add --x=1000 --y=500
```

This creates:
- Site name: CNS0001A (automatically assigned)
- 3 sectors at azimuths: 0°, 120°, 240°
- Height: 20m (default)
- No cells yet

### Add Site with Custom Parameters
```bash
cns site add --x=1000 --y=500 --height=25 --azimuth=45
```

This creates:
- Site name: CNS0002A (next available)
- 3 sectors at azimuths: 45°, 165°, 285°
- Height: 25m
- No cells yet

### Add Multiple Sites
```bash
# Add site 1
cns site add --x=0 --y=0

# Add site 2
cns site add --x=500 --y=0

# Add site 3  
cns site add --x=1000 --y=0

# Add site 4
cns site add --x=-500 --y=866
```

Sites will be named: CNS0001A, CNS0002A, CNS0003A, CNS0004A

## Adding Cells

### Add Single Cell to Existing Site
```bash
# Add high band cell
cns cell add --site=CNS0001A --sector=0 --band=H --freq=2500e6

# Add low band cell
cns cell add --site=CNS0001A --sector=0 --band=L --freq=600e6
```

### Add Cell with Custom Parameters
```bash
cns cell add --site=CNS0001A --sector=1 --band=H --freq=3500e6 \
  --tilt=12 --power=3 --rows=4 --cols=2
```

Parameters:
- `--site`: Site name (must exist)
- `--sector`: 0, 1, or 2
- `--band`: Band identifier (H, L, M, etc.)
- `--freq`: Frequency in Hz
- `--tilt`: Antenna tilt in degrees (default: 9.0)
- `--power`: TX power in dBm (default: 0.0)
- `--rows`: Antenna rows (default: 8)
- `--cols`: Antenna columns (default: 1)

### Add Dual-Band Cells to All Sectors
```bash
# Site CNS0001A - Add H and L bands to all 3 sectors
cns cell add --site=CNS0001A --sector=0 --band=H --freq=2500e6
cns cell add --site=CNS0001A --sector=0 --band=L --freq=600e6
cns cell add --site=CNS0001A --sector=1 --band=H --freq=2500e6
cns cell add --site=CNS0001A --sector=1 --band=L --freq=600e6
cns cell add --site=CNS0001A --sector=2 --band=H --freq=2500e6
cns cell add --site=CNS0001A --sector=2 --band=L --freq=600e6
```

## Complete Workflows

### Workflow 1: Manual Network from Scratch
```bash
# 1. Initialize empty
cns init --config '{"n_sites": 0, "num_ue": 30000}'

# 2. Add sites where you want them
cns site add --x=0 --y=0
cns site add --x=500 --y=0
cns site add --x=1000 --y=0

# 3. Add cells to each site
cns cell add --site=CNS0001A --sector=0 --band=H --freq=2500e6
cns cell add --site=CNS0001A --sector=0 --band=L --freq=600e6
# ... repeat for other sites/sectors

# 4. Verify
cns query sites
cns query cells

# 5. Run compute
cns sim compute --name="manual-network-baseline"
```

### Workflow 2: Augment Random Network
```bash
# 1. Initialize with random placement
cns init --default

# 2. Check what you have
cns query sites
cns query cells

# 3. Add strategic sites
cns site add --x=2000 --y=1500 --height=30
cns site add --x=-1000 --y=-1000

# 4. Add cells to new sites
cns cell add --site=CNS0011A --sector=0 --band=H --freq=2500e6 --tilt=15
cns cell add --site=CNS0011A --sector=0 --band=L --freq=600e6 --tilt=12

# 5. Run compute
cns sim compute --name="augmented-network"
```

### Workflow 3: Add Coverage to Specific Area
```bash
# 1. You have existing network
cns status

# 2. Identify gap - need coverage at (1500, 1200)
cns site add --x=1500 --y=1200

# 3. Add cells pointing towards coverage area
cns cell add --site=CNS0011A --sector=0 --band=H --freq=2500e6 --tilt=9

# 4. Test
cns sim compute --name="coverage-fill"
```

## Querying and Verification

### View All Sites
```bash
cns query sites
# or
cns site list
```

### View All Cells
```bash
cns query cells
```

### View Cells from Specific Site
```bash
cns query cells --site-name=CNS0001A
```

### View Cells by Band
```bash
cns query cells --band=H
```

## Common Patterns

### Pattern: Three-Site Triangle
```bash
# Create equilateral triangle with 500m sides
cns site add --x=0 --y=0
cns site add --x=500 --y=0  
cns site add --x=250 --y=433

# Add dual-band to each
for site in CNS0001A CNS0002A CNS0003A; do
  for sector in 0 1 2; do
    cns cell add --site=$site --sector=$sector --band=H --freq=2500e6
    cns cell add --site=$site --sector=$sector --band=L --freq=600e6
  done
done
```

### Pattern: Linear Road Coverage
```bash
# Sites every 500m along road
cns site add --x=0 --y=0
cns site add --x=500 --y=0
cns site add --x=1000 --y=0
cns site add --x=1500 --y=0

# Add cells pointing along road (sectors 0 and 1 only)
for site in CNS0001A CNS0002A CNS0003A CNS0004A; do
  cns cell add --site=$site --sector=0 --band=H --freq=2500e6
  cns cell add --site=$site --sector=1 --band=H --freq=2500e6
done
```

### Pattern: Dense Urban Area
```bash
# Grid of sites with 300m spacing
for x in 0 300 600 900; do
  for y in 0 300 600 900; do
    cns site add --x=$x --y=$y --height=25
  done
done

# Result: 16 sites in 4x4 grid (CNS0001A through CNS0016A)
```

## Error Handling

### Site Not Found
```bash
cns cell add --site=CNS9999A --sector=0 --band=H --freq=2500e6
# ❌ Error: Site 'CNS9999A' not found. Create site first with /add-site
```

Solution: Create the site first with `cns site add`

### Duplicate Cell
```bash
# First cell succeeds
cns cell add --site=CNS0001A --sector=0 --band=H --freq=2500e6
# ✓ Success

# Second cell with same band/sector fails
cns cell add --site=CNS0001A --sector=0 --band=H --freq=3500e6
# ❌ Error: Duplicate cell name. Cell names must be unique.
```

Solution: Use a different band identifier or different sector

## API Usage

If you're calling the API directly (not through CLI):

### Add Site via API
```python
import requests

response = requests.post("http://localhost:8000/add-site", json={
    "x": 1000.0,
    "y": 500.0,
    "height_m": 25.0,
    "az0_deg": 45.0,
    "cells": []
})

result = response.json()
site_name = result['site_name']  # e.g., "CNS0001A"
```

### Add Cell via API
```python
import requests

response = requests.post("http://localhost:8000/add-cell", json={
    "site_name": "CNS0001A",
    "sector_id": 0,
    "band": "H",
    "fc_hz": 2500e6,
    "tilt_deg": 9.0,
    "tx_rs_power_dbm": 0.0,
    "bs_rows": 8,
    "bs_cols": 1
})

result = response.json()
cell_name = result['cell_name']  # e.g., "HCNS0001A1"
```

## Integration with Existing Features

### With Tilt Optimization
```bash
# 1. Add sites/cells manually
cns site add --x=1000 --y=500
cns cell add --site=CNS0001A --sector=0 --band=H --freq=2500e6

# 2. Run baseline compute
cns sim compute --name="before-optimization"

# 3. Update tilts
cns update cell 0 --tilt=12

# 4. Run optimized compute
cns sim compute --name="after-optimization"

# 5. Compare snapshots
cns snapshot list
```

### With Config Management
```bash
# 1. Build custom network
cns init --config '{"n_sites": 0, "num_ue": 50000}'
cns site add --x=0 --y=0
# ... add more sites/cells

# 2. Save configuration
cns config save my-custom-network

# 3. Later, reload
cns config load my-custom-network
```

### With Map Visualization
The React frontend map will automatically show your dynamically added sites and cells. Just refresh the map view after adding sites/cells.

## Tips and Best Practices

1. **Plan your network layout first** - Draw it out or calculate coordinates before adding sites
2. **Use consistent spacing** - For uniform coverage, keep inter-site distance consistent
3. **Name your computes** - Use descriptive names when running `cns sim compute --name=...`
4. **Check before adding** - Use `cns query sites` to see what's already there
5. **Test incrementally** - Add a few sites, run compute, verify, then add more
6. **Save configurations** - Use `cns config save` to preserve successful network layouts
7. **Follow band conventions** - Stick to H (high band) and L (low band) for consistency

## Troubleshooting

### Q: Can I change a site's coordinates after creation?
A: Not directly. You'd need to delete and recreate (deletion not implemented yet).

### Q: Can I skip site numbers (e.g., go from CNS0001A to CNS0010A)?
A: No, site numbers are sequential and auto-assigned.

### Q: What happens if I add sites with seed=0 during init?
A: If n_sites=0, the seed doesn't matter. If n_sites>0, seed affects the random placement of those sites.

### Q: Can I add a cell without a site?
A: No, every cell must belong to a site. Create the site first.

### Q: How do I know what site number will be assigned?
A: The API returns this info. In CLI, it's shown in the success message.

## Next Steps

Now that you can dynamically manage sites and cells:

1. Experiment with different network topologies
2. Test coverage patterns for specific use cases
3. Build optimization workflows that add/remove cells
4. Create scripts for common network patterns
5. Integrate with your tilt optimization agent

Happy network building! 🚀

