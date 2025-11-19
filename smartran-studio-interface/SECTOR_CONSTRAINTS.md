# Sector and Cell Constraints

## Overview

The system now enforces strict rules about sectors, bands, and azimuths to maintain network integrity and prevent configuration errors.

## The 5 Core Rules

### 1. **Cells Must Belong to Sites**
- **Rule**: Every cell must be associated with an existing site
- **Enforcement**: API returns 404 if site doesn't exist
- **Why**: No orphan cells - every cell has a physical location
- **Example**:
  ```bash
  # This fails if CNS0001A doesn't exist
  cns cell add --site=CNS0001A --sector=0 --band=H --freq=2500e6
  
  # Create site first
  cns site add --x=1000 --y=500
  # Now this works
  cns cell add --site=CNS0001A --sector=0 --band=H --freq=2500e6
  ```

### 2. **Max 3 Sectors Per Site**
- **Rule**: Sector IDs must be 0, 1, or 2
- **Enforcement**: Validated in Pydantic model (ge=0, le=2)
- **Why**: Standard tri-sector site convention
- **Example**:
  ```bash
  cns cell add --site=CNS0001A --sector=0 --band=H --freq=2500e6  # ✓ Valid
  cns cell add --site=CNS0001A --sector=1 --band=H --freq=2500e6  # ✓ Valid
  cns cell add --site=CNS0001A --sector=2 --band=H --freq=2500e6  # ✓ Valid
  cns cell add --site=CNS0001A --sector=3 --band=H --freq=2500e6  # ✗ Invalid
  ```

### 3. **Unique Bands Per Sector**
- **Rule**: Each band identifier must be unique within a sector
- **Enforcement**: API checks existing cells before adding
- **Why**: Prevents duplicate/conflicting RF configurations
- **Example**:
  ```bash
  # First H band cell on sector 0 - OK
  cns cell add --site=CNS0001A --sector=0 --band=H --freq=2500e6
  
  # L band on same sector - OK (different band)
  cns cell add --site=CNS0001A --sector=0 --band=L --freq=600e6
  
  # Another H band on same sector - ERROR (duplicate band)
  cns cell add --site=CNS0001A --sector=0 --band=H --freq=3500e6
  # Error: Band 'H' already exists on CNS0001A sector 0
  ```

### 4. **Sector Azimuth Set on First Cell**
- **Rule**: Sector azimuth can only be specified when adding the FIRST cell to that sector
- **Enforcement**: API tracks which sectors have cells
- **Why**: All cells on a sector must point in the same direction
- **Example**:
  ```bash
  # First cell on sector 0 - can set azimuth
  cns cell add --site=CNS0001A --sector=0 --band=H --freq=2500e6 --azimuth=45
  
  # Second cell on sector 0 - inherits 45° automatically
  cns cell add --site=CNS0001A --sector=0 --band=L --freq=600e6
  # Any --azimuth flag here is ignored (with warning)
  ```

### 5. **Subsequent Cells Inherit Azimuth**
- **Rule**: Once a sector has cells, all new cells inherit that sector's azimuth
- **Enforcement**: API uses existing azimuth, ignores any new azimuth value
- **Why**: Ensures geometric consistency of sector coverage
- **Example**:
  ```bash
  # Sector 0 already has cells at 45°
  # This cell will also point at 45° regardless of --azimuth
  cns cell add --site=CNS0001A --sector=0 --band=M --freq=1800e6
  ```

## Sector Lifecycle

### Phase 1: Site Creation
```bash
cns site add --x=1000 --y=500 --azimuth=0
```
Creates site CNS0001A with 3 empty sectors:
- Sector 0: 0° (default)
- Sector 1: 120° (default)  
- Sector 2: 240° (default)

### Phase 2: First Cell on Sector
```bash
cns cell add --site=CNS0001A --sector=0 --band=H --freq=2500e6 --azimuth=45
```
- ✓ First cell on sector 0
- ✓ Azimuth accepted and set to 45°
- ✓ Sector 0 now "defined" (has cells)
- Sector 0: 45° (overridden)
- Sector 1: 120° (still default)
- Sector 2: 240° (still default)

### Phase 3: Additional Cells on Same Sector
```bash
cns cell add --site=CNS0001A --sector=0 --band=L --freq=600e6
```
- ✓ Second cell on sector 0
- ✓ Inherits 45° azimuth automatically
- ✓ Both H and L bands coexist on sector 0
- Band H at 45°
- Band L at 45°

### Phase 4: First Cell on Different Sector
```bash
cns cell add --site=CNS0001A --sector=1 --band=H --freq=2500e6 --azimuth=165
```
- ✓ First cell on sector 1
- ✓ Azimuth accepted and set to 165°
- ✓ Sector 1 now "defined"
- Sector 0: 45° (defined)
- Sector 1: 165° (overridden)
- Sector 2: 240° (still default)

## Common Scenarios

### Scenario: Standard Tri-Sector Dual-Band Site

```bash
# Create site
cns site add --x=0 --y=0

# Sector 0 (default 0°)
cns cell add --site=CNS0001A --sector=0 --band=H --freq=2500e6
cns cell add --site=CNS0001A --sector=0 --band=L --freq=600e6

# Sector 1 (default 120°)
cns cell add --site=CNS0001A --sector=1 --band=H --freq=2500e6
cns cell add --site=CNS0001A --sector=1 --band=L --freq=600e6

# Sector 2 (default 240°)
cns cell add --site=CNS0001A --sector=2 --band=H --freq=2500e6
cns cell add --site=CNS0001A --sector=2 --band=L --freq=600e6
```

Result: 3 sectors, 6 cells total (H+L on each sector)

### Scenario: Custom Azimuth for Coverage Optimization

```bash
# Create site
cns site add --x=1000 --y=500

# Point sector 0 northeast (45°)
cns cell add --site=CNS0001A --sector=0 --band=H --freq=2500e6 --azimuth=45
cns cell add --site=CNS0001A --sector=0 --band=L --freq=600e6

# Point sector 1 southeast (135°)
cns cell add --site=CNS0001A --sector=1 --band=H --freq=2500e6 --azimuth=135
cns cell add --site=CNS0001A --sector=1 --band=L --freq=600e6

# Point sector 2 west (270°)
cns cell add --site=CNS0001A --sector=2 --band=H --freq=2500e6 --azimuth=270
cns cell add --site=CNS0001A --sector=2 --band=L --freq=600e6
```

Result: Custom directional coverage pattern

### Scenario: Single-Sector Site

```bash
# Create site
cns site add --x=500 --y=500

# Only use sector 0 (omnidirectional or specific direction)
cns cell add --site=CNS0001A --sector=0 --band=H --freq=2500e6 --azimuth=0
cns cell add --site=CNS0001A --sector=0 --band=L --freq=600e6
```

Result: 1 sector, 2 cells (sectors 1 and 2 remain empty but available)

## Error Messages

### Duplicate Band Error
```bash
cns cell add --site=CNS0001A --sector=0 --band=H --freq=3500e6
```
```
❌ Error: Band 'H' already exists on CNS0001A sector 0. 
Each band must be unique per sector. Existing bands: H, L
```

### Site Not Found Error
```bash
cns cell add --site=CNS9999A --sector=0 --band=H --freq=2500e6
```
```
❌ Error: Site 'CNS9999A' not found. Create site first with /add-site

Available sites: Run 'cns query sites' to see existing sites
Create site: cns site add --x=<x> --y=<y>
```

### Invalid Sector Error
```bash
cns cell add --site=CNS0001A --sector=5 --band=H --freq=2500e6
```
```
❌ Error: Invalid sector ID '5'

Sector must be 0, 1, or 2
```

## Verification Commands

```bash
# See which sectors have cells
cns query cells --site-name=CNS0001A

# See all bands on a site
cns query cells --site-name=CNS0001A

# See specific band
cns query cells --site-name=CNS0001A --band=H

# Check site info (includes default azimuths)
cns query sites
```

## API Response Fields

When adding a cell, the API returns:
```json
{
  "status": "success",
  "cell_idx": 0,
  "cell_name": "HCNS0001A1",
  "site_name": "CNS0001A",
  "sector_id": 0,
  "band": "H",
  "fc_hz": 2500000000,
  "tilt_deg": 9.0,
  "sector_azimuth": 45.0,
  "is_first_cell_on_sector": true,
  "existing_bands_on_sector": ["H"]
}
```

Key fields:
- `is_first_cell_on_sector`: Whether this was the first cell added to this sector
- `sector_azimuth`: The azimuth being used (either new or inherited)
- `existing_bands_on_sector`: All bands now present on this sector (including the one just added)

## Design Rationale

### Why Unique Bands Per Sector?
- Prevents accidental duplicate configurations
- Simplifies network planning and visualization
- Makes it clear when you're adding coverage vs. replacing it
- Avoids ambiguity in which cell serves which purpose

### Why Fixed Azimuth After First Cell?
- Ensures geometric consistency
- All cells on a sector point the same direction (physically realistic)
- Prevents configuration drift
- Makes sector planning explicit and intentional

### Why Max 3 Sectors?
- Industry standard tri-sector site pattern
- Can be relaxed later if needed
- Currently simplifies validation and UI
- Most real-world deployments use ≤3 sectors per site

## Future Enhancements

Potential relaxations (not implemented):
1. Allow more than 3 sectors per site
2. Allow multiple cells per band (with different frequencies)
3. Allow azimuth adjustment after cells exist (with warnings)
4. Support for special omnidirectional sectors

For now, these constraints ensure network integrity and prevent common configuration errors.

