# SmartRAN Studio CLI Reference

Complete command reference for the SmartRAN Studio (`srs`) command-line interface.

## Command Prefix

All commands use the `srs` prefix:

```bash
srs <command> [arguments]
```

**Legacy Support**: Commands with `cns` or `smartran` prefix also work.

## General Commands

### `srs help`

Show help message with all available commands.

```bash
srs help
```

### `srs status`

Show simulation status and connection information.

```bash
srs status
```

**Output**:
- Network connection status
- Number of sites, cells, UEs
- Configured bands
- Chunk sizes

---

## Initialization Commands

### `srs init`

Initialize simulation (interactive wizard).

```bash
# Interactive mode - step-by-step prompts
srs init

# Quick start with all defaults
srs init --default

# Custom configuration via JSON
srs init --config '{"n_sites": 20, "num_ue": 50000}'
```

**Interactive Wizard** prompts for:
- Number of sites
- Site spacing
- High band frequency & antenna config
- Low band frequency & antenna config
- Number of UEs
- Random seed

**Default Values**:
- 10 sites, 500m spacing
- High band: 2.5 GHz, 8x1 array, 9° tilt
- Low band: 600 MHz, 8x1 array, 9° tilt
- 30,000 UEs in box layout

**Custom Config Parameters**:
```json
{
  "n_sites": 10,              // Number of sites
  "spacing": 500.0,           // Inter-site spacing (meters)
  "seed": 7,                  // Random seed
  "jitter": 0.06,             // Site position jitter
  "site_height_m": 20.0,      // Site height (meters)
  "fc_hi_hz": 2500000000,     // High band frequency (Hz)
  "tilt_hi_deg": 9.0,         // High band tilt (degrees)
  "bs_rows_hi": 8,            // High band antenna rows
  "bs_cols_hi": 1,            // High band antenna columns
  "fc_lo_hz": 600000000,      // Low band frequency (Hz)
  "tilt_lo_deg": 9.0,         // Low band tilt (degrees)
  "bs_rows_lo": 8,            // Low band antenna rows
  "bs_cols_lo": 1,            // Low band antenna columns
  "num_ue": 30000,            // Number of UEs
  "box_pad_m": 250.0,         // Box padding (meters)
  "cells_chunk": 48,          // Cell chunk size
  "ue_chunk": 500             // UE chunk size
}
```

---

## Query Commands

### `srs query cells`

List and filter cells.

```bash
# List all cells
srs query cells

# Filter by band
srs query cells --band=H           # High band only
srs query cells --band=L           # Low band only

# Filter by site (supports wildcards)
srs query cells --site-name=SITE0001A
srs query cells --site-name=SITE000*

# Filter by tilt range
srs query cells --tilt-min=8 --tilt-max=10

# Filter by power range
srs query cells --power-min=-3 --power-max=3

# Filter by sector
srs query cells --sector-id=0

# Combine filters
srs query cells --band=H --tilt-min=10 --sector-id=0

# Limit results
srs query cells --limit=20
```

**Query Parameters**:
- `--band=<H|L|M>` - Band identifier
- `--site-name=<pattern>` - Site name (wildcards supported)
- `--sector-id=<0-2>` - Sector ID
- `--tilt-min=<degrees>` - Minimum tilt
- `--tilt-max=<degrees>` - Maximum tilt
- `--power-min=<dBm>` - Minimum TX power
- `--power-max=<dBm>` - Maximum TX power
- `--freq-min=<Hz>` - Minimum frequency
- `--freq-max=<Hz>` - Maximum frequency
- `--rows=<count>` - Antenna rows
- `--cols=<count>` - Antenna columns
- `--limit=<n>` - Limit results

### `srs query sites`

List all sites in the simulation.

```bash
srs query sites
```

**Output**: Table with site names, positions, sector azimuths, cell counts

### `srs query ues`

Show UE (User Equipment) information.

```bash
srs query ues
```

**Output**: Number of UEs, layout type, coordinate ranges

---

## Update Commands

### `srs update cell`

Update a single cell's configuration.

```bash
# Update by cell ID
srs update cell 0 --tilt=12.0

# Update multiple parameters
srs update cell 5 --tilt=11.0 --power=3.0

# Update antenna configuration
srs update cell 10 --rows=4 --cols=2
```

**Update Parameters**:
- `--tilt=<degrees>` - Antenna tilt (electrical downtilt)
- `--power=<dBm>` - TX power (RS power)
- `--rows=<count>` - Antenna array rows
- `--cols=<count>` - Antenna array columns
- `--v-spacing=<wavelengths>` - Vertical element spacing
- `--h-spacing=<wavelengths>` - Horizontal element spacing
- `--polarization=<single|dual>` - Polarization
- `--pol-type=<V|VH|cross>` - Polarization type

### `srs update cells query`

Update multiple cells matching query criteria.

```bash
# Update all high-band cells
srs update cells query --band=H --update-tilt-deg=12.0

# Update all mid-band cells
srs update cells query --band=M --update-tilt-deg=11.0

# Update cells at specific sites
srs update cells query --site-name=SITE000* --update-tilt-deg=11.0

# Update sector 0 cells
srs update cells query --sector-id=0 --update-tilt-deg=10.0 --update-tx-rs-power-dbm=3.0
```

**Update Parameters** (prefix with `--update-`):
- `--update-tilt-deg=<degrees>`
- `--update-tx-rs-power-dbm=<dBm>`
- `--update-bs-rows=<count>`
- `--update-bs-cols=<count>`
- `--update-elem-v-spacing=<wavelengths>`
- `--update-elem-h-spacing=<wavelengths>`

---

## Site Management Commands

### `srs site add`

Add a new site to the simulation.

```bash
# Basic site at coordinates
srs site add --x=1000 --y=500

# Site with custom height
srs site add --x=0 --y=0 --height=30

# Site with rotated sector pattern
srs site add --x=-500 --y=1200 --azimuth=45
```

**Parameters**:
- `--x=<meters>` - X coordinate (required)
- `--y=<meters>` - Y coordinate (required)
- `--height=<meters>` - Site height (default: 20)
- `--azimuth=<degrees>` - Sector 0 azimuth (default: 0)

**Site Naming**: Auto-assigned as `SITE####A` (e.g., SITE0001A, SITE0002A)

### `srs cell add`

Add a cell to an existing site.

```bash
# Add high-band cell to sector 0
srs cell add --site=SITE0001A --sector=0 --band=H --freq=2500e6

# Add with custom tilt and power
srs cell add --site=SITE0001A --sector=1 --band=H --freq=2500e6 --tilt=12 --power=3

# Add low-band cell
srs cell add --site=SITE0001A --sector=2 --band=L --freq=600e6

# First cell on sector - set azimuth
srs cell add --site=SITE0001A --sector=0 --band=H --freq=2500e6 --azimuth=45

# Custom antenna array
srs cell add --site=SITE0001A --sector=1 --band=H --freq=3500e6 --rows=4 --cols=2
```

**Parameters**:
- `--site=<name>` - Existing site name (required)
- `--sector=<0-2>` - Sector ID (required)
- `--band=<H|L|M>` - Band identifier (required)
- `--freq=<Hz>` - Frequency in Hz (required)
- `--tilt=<degrees>` - Antenna tilt (default: 9.0)
- `--power=<dBm>` - TX power (default: 0.0)
- `--azimuth=<degrees>` - Sector azimuth (only for first cell on sector)
- `--rows=<count>` - Antenna rows
- `--cols=<count>` - Antenna columns
- `--pattern=<model>` - Antenna pattern

**Rules**:
1. Site must exist (create with `srs site add` first)
2. Max 3 sectors per site (0, 1, 2)
3. First cell on a sector sets the azimuth
4. Subsequent cells on same sector inherit azimuth

### `srs site list`

List all sites (alias for `srs query sites`).

```bash
srs site list
```

---

## Simulation Commands

### `srs sim compute`

Run RF propagation simulation and generate measurement snapshot.

```bash
# Run simulation with name
srs sim compute --name="baseline"

# Results saved as snapshot with timestamp
```

**What it does**:
1. Validates simulation is initialized
2. Chunks cells and UEs for GPU memory
3. Computes RSRP for all UE-cell pairs
4. Saves results to database as snapshot
5. Returns snapshot ID and statistics

**Performance**: Chunked computation allows large-scale simulations (tens of thousands of UEs) on consumer GPUs.

### `srs drop ues`

Drop/redrop User Equipment in the simulation.

```bash
# Drop 50,000 UEs
srs drop ues 50000

# Drop with custom box padding
srs drop ues 30000 --layout=box --box-pad=300

# Drop with custom seed
srs drop ues 50000 --seed=42
```

**Parameters**:
- `<count>` - Number of UEs (required)
- `--layout=box` - Distribution layout
- `--box-pad=<meters>` - Padding around sites
- `--seed=<n>` - Random seed

---

## Configuration Management

### `srs config save`

Save current simulation state to database.

```bash
# Save with name
srs config save baseline

# Save with description
srs config save optimized --description="High band tilted to 12°"
```

**What is saved**:
- Initialization parameters
- All cell configurations
- UE distribution
- Topology metadata

### `srs config load`

Restore a saved configuration.

```bash
srs config load baseline
```

**What happens**:
- Simulation is reinitialized
- All cell configs restored
- UEs redeployed
- Ready to use immediately

### `srs config list`

List all saved configurations.

```bash
srs config list
```

**Output**: Table with config names, descriptions, stats, creation dates

### `srs config delete`

Delete a saved configuration.

```bash
srs config delete old-config
```

---

## Snapshot Management

Snapshots are **measurement data** from compute runs (read-only).

### `srs snapshot list`

List all saved measurement snapshots.

```bash
# List all snapshots
srs snapshot list

# Limit results
srs snapshot list --limit=20
```

**Output**: Table with snapshot IDs, names, stats, timestamps

### `srs snapshot get`

View detailed snapshot metadata.

```bash
srs snapshot get 2025-11-18_14-30-15
```

**Output**: Full snapshot details including run parameters, statistics, RSRP ranges

### `srs snapshot delete`

Delete a measurement snapshot.

```bash
srs snapshot delete 2025-11-18_14-30-15
```

---

## Connection Management

### `srs connect`

Connect to a network.

```bash
srs connect sim
```

### `srs disconnect`

Disconnect from current network.

```bash
srs disconnect
```

### `srs networks`

List available networks.

```bash
srs networks
```

---

## Other Commands

### `clear`

Clear the CLI output display.

```bash
clear
```

---

## Cell Naming Convention

Cells are named: `{band}{site}{sector}`

**Examples**:
- `HSITE0001A1` - High band, site 1, sector 1
- `LSITE0001A1` - Low band, site 1, sector 1
- `MSITE0005A2` - Mid band, site 5, sector 2

**Bands**:
- `H` - High band (typically 2.5+ GHz)
- `L` - Low band (typically <1 GHz)
- `M` - Mid band (typically 1-2.5 GHz)

---

## Tips

1. **Wildcards**: Use `*` in site names (e.g., `SITE000*`)
2. **Tab Completion**: Available in the frontend (work in progress)
3. **Command History**: Use up/down arrows to recall commands
4. **Help**: Add `--help` to any command for detailed info
5. **Clear Output**: Use `clear` command to reset display

