# Quick Start: Dynamic Site & Cell Management

## 🚀 New Commands

```bash
# Add a new site
cns site add --x=<meters> --y=<meters> [--height=<m>] [--azimuth=<deg>]

# Add a cell to existing site
cns cell add --site=<name> --sector=<0-2> --band=<H/L> --freq=<hz> [options]

# List all sites
cns site list
```

## 📋 Quick Examples

### Empty Init + Manual Placement
```bash
# Start with empty simulation
cns init --config '{"n_sites": 0, "num_ue": 30000}'

# Add site at origin
cns site add --x=0 --y=0

# Add high band cell
cns cell add --site=CNS0001A --sector=0 --band=H --freq=2500e6

# Verify
cns query sites
cns query cells

# Run compute
cns sim compute --name="manual-test"
```

### Add to Existing Network
```bash
# You already have network from cns init --default

# Add strategic site
cns site add --x=1500 --y=1200

# Add cells to new site
cns cell add --site=CNS0011A --sector=0 --band=H --freq=2500e6
cns cell add --site=CNS0011A --sector=0 --band=L --freq=600e6

# Run compute
cns sim compute --name="augmented"
```

### Three-Site Triangle
```bash
# Equilateral triangle, 500m sides
cns site add --x=0 --y=0
cns site add --x=500 --y=0
cns site add --x=250 --y=433

# Add dual-band to each site, all sectors
cns cell add --site=CNS0001A --sector=0 --band=H --freq=2500e6
cns cell add --site=CNS0001A --sector=0 --band=L --freq=600e6
cns cell add --site=CNS0001A --sector=1 --band=H --freq=2500e6
cns cell add --site=CNS0001A --sector=1 --band=L --freq=600e6
cns cell add --site=CNS0001A --sector=2 --band=H --freq=2500e6
cns cell add --site=CNS0001A --sector=2 --band=L --freq=600e6
# Repeat for CNS0002A and CNS0003A...
```

## 🎯 Key Rules

1. **Site names auto-assigned**: CNS0001A, CNS0002A, etc.
2. **Cells need sites**: Always create site first
3. **No duplicate cells**: Same site/sector/band = error
4. **3 sectors per site**: Always 0, 1, 2 (at 0°, 120°, 240° from azimuth)

## 🔧 Common Parameters

### Site Add
- `--x`, `--y`: Coordinates (required)
- `--height`: Site height in meters (default: 20)
- `--azimuth`: Sector 0 direction (default: 0)

### Cell Add
- `--site`: Site name like CNS0001A (required)
- `--sector`: 0, 1, or 2 (required)
- `--band`: H, L, M, etc. (required)
- `--freq`: Frequency in Hz, e.g., 2500e6 (required)
- `--tilt`: Antenna tilt (default: 9.0)
- `--power`: TX power dBm (default: 0.0)
- `--rows`: Antenna rows (default: 8)
- `--cols`: Antenna cols (default: 1)

## 📊 Verification Commands

```bash
# View all sites
cns query sites

# View all cells  
cns query cells

# View specific site's cells
cns query cells --site-name=CNS0001A

# View by band
cns query cells --band=H

# Check status
cns status
```

## ⚡ Power User Tips

**Script a network:**
```bash
#!/bin/bash
# 5-site linear deployment
for i in {0..4}; do
  x=$((i * 500))
  cns site add --x=$x --y=0
done
```

**Dual-band helper function:**
```bash
add_dualband() {
  site=$1
  sector=$2
  cns cell add --site=$site --sector=$sector --band=H --freq=2500e6
  cns cell add --site=$site --sector=$sector --band=L --freq=600e6
}

add_dualband CNS0001A 0
add_dualband CNS0001A 1
add_dualband CNS0001A 2
```

## 🐛 Troubleshooting

**Error: Site not found**
→ Create site first: `cns site add --x=<x> --y=<y>`

**Error: Duplicate cell name**  
→ Cell with that band already exists at site/sector. Use different band or sector.

**Error: Sector must be 0, 1, or 2**
→ Check your --sector parameter

## 📚 Full Documentation

See `SITE_CELL_MANAGEMENT.md` for complete guide with:
- All workflows
- API usage
- Advanced patterns
- Integration examples

## 🎬 Video Tutorial Commands

```bash
# 1. Empty start
cns init --config '{"n_sites": 0, "num_ue": 10000}'

# 2. Add 3 sites in line
cns site add --x=0 --y=0
cns site add --x=500 --y=0
cns site add --x=1000 --y=0

# 3. Add cells to first site
cns cell add --site=CNS0001A --sector=0 --band=H --freq=2500e6
cns cell add --site=CNS0001A --sector=0 --band=L --freq=600e6

# 4. Verify
cns query sites
cns query cells

# 5. Run
cns sim compute --name="demo"

# 6. Check results
cns snapshot list
cns snapshot get <snapshot_id>
```

That's it! You're ready to build custom networks. 🎉

