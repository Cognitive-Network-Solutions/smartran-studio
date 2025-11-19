"""
Site and Cell Management Commands

Commands for dynamically adding sites and cells to the simulation
after initialization.
"""
import sys
from pathlib import Path
from typing import List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from api_client import api_request
from framework import command, CommandResponse, ResponseType, ArgumentParser


@command(
    name="site add",
    description="Add a new site to the simulation",
    usage="site add --x=<x> --y=<y> [options]",
    long_description="""Add a new site to the simulation

Creates a site at a specific location. A site is just a physical location (x, y, height).
Sectors don't actually exist until you add cells to them.

Usage: site add --x=<x> --y=<y> [options]

Required:
  --x=<meters>        X coordinate in meters
  --y=<meters>        Y coordinate in meters

Options:
  --height=<meters>   Site height (default: 20.0)
  --azimuth=<degrees> Default azimuth for sector 0 (default: 0.0)

Description:
  Creates a new site at the specified location.
  The site name is automatically assigned as the next available SITE####A number.
  
  IMPORTANT: This only creates the site location, not the sectors/cells.
  Sectors become "real" when you add the first cell to them.
  
  AZIMUTH PARAMETER:
  - Sets DEFAULT azimuths for sectors (if not overridden when adding cells)
  - Sector 0: your value (default 0°)
  - Sector 1: your value + 120°
  - Sector 2: your value + 240°
  - When adding the FIRST cell to a sector, you can override its azimuth
  
  Think of --azimuth as "rotation offset" for the tri-sector pattern.

Examples:
  # Basic site at origin with default azimuths (0°, 120°, 240°)
  site add --x=0 --y=0
  
  # Site with rotated sector pattern (45°, 165°, 285°)
  site add --x=1000 --y=500 --azimuth=45
  
  # Tall site
  site add --x=-500 --y=1200 --height=30

See also: cell add, query sites
""",
    response_type=ResponseType.SUCCESS
)
async def cmd_add_site(args: List[str]) -> CommandResponse:
    """Add a new site to the simulation"""
    
    # Parse arguments
    parser = ArgumentParser(valid_flags={
        'x': float,
        'y': float,
        'height': float,
        'azimuth': float
    })
    parsed_args, positional_args = parser.parse_arguments(args)
    
    # Handle --help
    if parsed_args.help:
        return CommandResponse(
            content=cmd_add_site.metadata['long_description'],
            response_type=ResponseType.TEXT
        )
    
    # Check for unexpected positional args
    if positional_args:
        return CommandResponse(
            content=f"❌ Error: Unexpected positional arguments: {', '.join(positional_args)}\n\nUse --help for more information.",
            response_type=ResponseType.ERROR,
            exit_code=1
        )
    
    # Validate required parameters
    if parsed_args.x is None:
        return CommandResponse(
            content="❌ Error: X coordinate is required\n\nUsage: site add --x=<meters> --y=<meters>\n\nExample: site add --x=1000 --y=500",
            response_type=ResponseType.ERROR,
            exit_code=1
        )
    
    if parsed_args.y is None:
        return CommandResponse(
            content="❌ Error: Y coordinate is required\n\nUsage: site add --x=<meters> --y=<meters>\n\nExample: site add --x=1000 --y=500",
            response_type=ResponseType.ERROR,
            exit_code=1
        )
    
    try:
        request_data = {
            "x": parsed_args.x,
            "y": parsed_args.y,
            "height_m": parsed_args.height or 20.0,
            "az0_deg": parsed_args.azimuth or 0.0,
            "cells": []  # No cells by default
        }
        
        result = await api_request("POST", "/add-site", data=request_data)
        
        az0 = request_data["az0_deg"]
        
        # Build azimuth info message
        if parsed_args.azimuth is not None:
            azimuth_info = f"""
Default Sector Azimuths (if not specified when adding cells):
  • Sector 0: {az0:.1f}°
  • Sector 1: {(az0 + 120) % 360:.1f}°
  • Sector 2: {(az0 + 240) % 360:.1f}°
"""
        else:
            azimuth_info = """
Default Sector Azimuths (if not specified when adding cells):
  • Sector 0: 0.0°
  • Sector 1: 120.0°
  • Sector 2: 240.0°
"""
        
        content = f"""✓ Site Added Successfully

Site Name:       {result['site_name']}
Site Number:     {result['site_number']:04d}
Site Index:      {result['site_idx']}
Location:        ({parsed_args.x:.1f}, {parsed_args.y:.1f}) meters
Height:          {request_data['height_m']:.1f} meters

{azimuth_info}
Note: Sectors don't exist until you add cells to them.
      When adding the first cell to a sector, you can override its azimuth.

Next Steps:
  • Add first cell:  cell add --site={result['site_name']} --sector=0 --band=H --freq=2500e6
  • Set azimuth:     cell add --site={result['site_name']} --sector=0 --band=H --freq=2500e6 --azimuth=45
  • View site:       query sites
"""
        
        return CommandResponse(
            content=content,
            response_type=ResponseType.SUCCESS
        )
        
    except Exception as e:
        return CommandResponse(
            content=f"❌ Error adding site: {str(e)}",
            response_type=ResponseType.ERROR,
            exit_code=1
        )


@command(
    name="cell add",
    description="Add a cell to an existing site",
    usage="cell add --site=<name> --sector=<0-2> --band=<H/L> --freq=<hz> [options]",
    long_description="""Add a cell to an existing site

Adds a single cell to an existing site's sector. The cell must be associated
with an existing site - use 'site add' first if you need a new site.

Usage: cell add --site=<name> --sector=<0-2> --band=<H/L> --freq=<hz> [options]

Required:
  --site=<name>       Existing site name (e.g., SITE0001A)
  --sector=<0-2>      Sector ID (0, 1, or 2)
  --band=<band>       Band identifier (e.g., H, L, M)
  --freq=<hz>         Frequency in Hz (e.g., 2500e6 for 2.5 GHz)

Options:
  --azimuth=<deg>     Sector azimuth (ONLY for first cell on sector)
  --tilt=<degrees>    Antenna tilt (default: 9.0)
  --power=<dbm>       TX power in dBm (default: 0.0)
  --rows=<n>          Antenna array rows (default: 8)
  --cols=<n>          Antenna array columns (default: 1)

Description:
  Adds a cell with the specified RF parameters to an existing site.
  The cell name is automatically generated following the naming convention.
  
  IMPORTANT RULES:
  1. Cells MUST belong to existing sites - create site first with 'site add'
  2. Max 3 sectors per site (IDs: 0, 1, 2)
  3. Each BAND must be unique per sector (no duplicate H+H on same sector)
  4. Sector azimuth can ONLY be set when adding the FIRST cell to that sector
  5. Subsequent cells on the same sector inherit the sector's azimuth
  
  SECTOR AZIMUTH:
  - When adding the FIRST cell to a sector, you can specify --azimuth
  - If not specified, uses the default from site creation (0°, 120°, 240°)
  - When adding ADDITIONAL cells to the same sector, azimuth is fixed
  - This ensures all cells on a sector point in the same direction

Examples:
  # First cell on sector 0 - set azimuth to 45°
  cell add --site=SITE0001A --sector=0 --band=H --freq=2500e6 --azimuth=45
  
  # Second cell on same sector - inherits 45° azimuth automatically
  cell add --site=SITE0001A --sector=0 --band=L --freq=600e6
  
  # First cell on sector 1 - set azimuth to 165°
  cell add --site=SITE0001A --sector=1 --band=H --freq=2500e6 --azimuth=165
  
  # Custom tilt and power
  cell add --site=SITE0001A --sector=2 --band=H --freq=2500e6 --tilt=12 --power=3

See also: site add, query cells, update cell
""",
    response_type=ResponseType.SUCCESS
)
async def cmd_add_cell(args: List[str]) -> CommandResponse:
    """Add a cell to an existing site"""
    
    # Parse arguments
    parser = ArgumentParser(valid_flags={
        'site': str,
        'sector': int,
        'band': str,
        'freq': float,
        'azimuth': float,
        'tilt': float,
        'power': float,
        'rows': int,
        'cols': int
    })
    parsed_args, positional_args = parser.parse_arguments(args)
    
    # Handle --help
    if parsed_args.help:
        return CommandResponse(
            content=cmd_add_cell.metadata['long_description'],
            response_type=ResponseType.TEXT
        )
    
    # Check for unexpected positional args
    if positional_args:
        return CommandResponse(
            content=f"❌ Error: Unexpected positional arguments: {', '.join(positional_args)}\n\nUse --help for more information.",
            response_type=ResponseType.ERROR,
            exit_code=1
        )
    
    # Validate required parameters
    if not parsed_args.site:
        return CommandResponse(
            content="❌ Error: Site name is required\n\nUsage: cell add --site=<name> --sector=<0-2> --band=<H/L> --freq=<hz>\n\nExample: cell add --site=SITE0001A --sector=0 --band=H --freq=2500e6",
            response_type=ResponseType.ERROR,
            exit_code=1
        )
    
    if parsed_args.sector is None:
        return CommandResponse(
            content="❌ Error: Sector ID is required (0, 1, or 2)\n\nUsage: cell add --site=<name> --sector=<0-2> --band=<H/L> --freq=<hz>\n\nExample: cell add --site=SITE0001A --sector=0 --band=H --freq=2500e6",
            response_type=ResponseType.ERROR,
            exit_code=1
        )
    
    if not parsed_args.band:
        return CommandResponse(
            content="❌ Error: Band identifier is required\n\nUsage: cell add --site=<name> --sector=<0-2> --band=<H/L> --freq=<hz>\n\nExample: cell add --site=SITE0001A --sector=0 --band=H --freq=2500e6",
            response_type=ResponseType.ERROR,
            exit_code=1
        )
    
    if parsed_args.freq is None:
        return CommandResponse(
            content="❌ Error: Frequency is required\n\nUsage: cell add --site=<name> --sector=<0-2> --band=<H/L> --freq=<hz>\n\nExample: cell add --site=SITE0001A --sector=0 --band=H --freq=2500e6",
            response_type=ResponseType.ERROR,
            exit_code=1
        )
    
    # Validate sector range
    if parsed_args.sector not in [0, 1, 2]:
        return CommandResponse(
            content=f"❌ Error: Invalid sector ID '{parsed_args.sector}'\n\nSector must be 0, 1, or 2",
            response_type=ResponseType.ERROR,
            exit_code=1
        )
    
    try:
        request_data = {
            "site_name": parsed_args.site,
            "sector_id": parsed_args.sector,
            "band": parsed_args.band,
            "fc_hz": parsed_args.freq,
            "tilt_deg": parsed_args.tilt or 9.0,
            "tx_rs_power_dbm": parsed_args.power or 0.0,
        }
        
        # Add optional azimuth if provided
        if parsed_args.azimuth is not None:
            request_data["sector_azimuth"] = parsed_args.azimuth
        
        # Add optional antenna config if provided
        if parsed_args.rows is not None:
            request_data["bs_rows"] = parsed_args.rows
        if parsed_args.cols is not None:
            request_data["bs_cols"] = parsed_args.cols
        
        result = await api_request("POST", "/add-cell", data=request_data)
        
        freq_ghz = parsed_args.freq / 1e9
        antenna_str = f"{parsed_args.rows or 8}x{parsed_args.cols or 1}"
        
        # Build sector info message
        is_first = result.get('is_first_cell_on_sector', False)
        sector_az = result.get('sector_azimuth', 0)
        existing_bands = result.get('existing_bands_on_sector', [])
        
        sector_status = "✓ First cell on this sector" if is_first else f"✓ Sector already has: {', '.join(existing_bands[:-1])}"
        azimuth_note = f" (azimuth set to {sector_az:.1f}°)" if is_first and parsed_args.azimuth is not None else f" (azimuth: {sector_az:.1f}°)"
        
        content = f"""✓ Cell Added Successfully

Cell Name:       {result['cell_name']}
Cell Index:      {result['cell_idx']}

Site:            {result['site_name']}
Sector:          {result['sector_id']}{azimuth_note}
Band:            {result['band']}

RF Configuration:
  Frequency:     {freq_ghz:.2f} GHz ({parsed_args.freq/1e6:.1f} MHz)
  Tilt:          {request_data['tilt_deg']:.1f}°
  Power:         {request_data['tx_rs_power_dbm']:.1f} dBm
  Antenna:       {antenna_str}

{sector_status}
All bands on sector {result['sector_id']}: {', '.join(existing_bands)}

✓ Cell is now active and will be included in compute operations

Next Steps:
  • View cells:   query cells --site-name={result['site_name']}
  • Add more:     cell add --site={result['site_name']} --sector=<n> --band=<X> --freq=<hz>
  • Run compute:  sim compute --name="test-run"
"""
        
        return CommandResponse(
            content=content,
            response_type=ResponseType.SUCCESS
        )
        
    except Exception as e:
        error_msg = str(e)
        # Provide helpful error messages for common issues
        if "not found" in error_msg.lower():
            error_msg += f"\n\nAvailable sites: Run 'query sites' to see existing sites"
            error_msg += f"\nCreate site: site add --x=<x> --y=<y>"
        elif "already exists on" in error_msg.lower():
            # Duplicate band error - message already contains good info from API
            pass
        elif "duplicate" in error_msg.lower() or "unique" in error_msg.lower():
            error_msg += f"\n\nTip: Check existing cells with 'query cells --site-name={parsed_args.site}'"
        
        return CommandResponse(
            content=f"❌ Error adding cell: {error_msg}",
            response_type=ResponseType.ERROR,
            exit_code=1
        )


@command(
    name="site list",
    description="List all sites (alias for 'query sites')",
    usage="site list",
    long_description="""List all sites in the simulation

This is an alias for 'query sites'.

Usage: site list

Shows a table of all sites with their positions and cell counts.

Example:
  site list

See also: query sites, query cells
""",
    response_type=ResponseType.TEXT
)
async def cmd_list_sites(args: List[str]) -> CommandResponse:
    """List all sites (alias for query sites)"""
    
    # Just redirect to query sites
    from commands.query import cmd_query_sites
    return await cmd_query_sites({})

