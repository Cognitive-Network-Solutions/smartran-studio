"""
Cell update commands
"""
import sys
from pathlib import Path
from typing import List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from api_client import api_request
from framework import command, CommandResponse, ResponseType, ArgumentParser


@command(
    name="update cell",
    description="Update single cell configuration",
    usage="cns update cell <id> [params]",
    long_description="""Update single cell configuration

Usage: cns update cell <id> [params]

Parameters:
  --tilt=<deg>          Tilt angle in degrees
  --power=<dbm>         TX power in dBm
  --rows=<n>            Antenna rows
  --cols=<n>            Antenna columns
  --freq=<hz>           Frequency in Hz
  
Examples:
  cns update cell 0 --tilt=12.0
  cns update cell 5 --tilt=11.0 --power=3.0
  cns update cell 10 --rows=8 --cols=1
""",
    response_type=ResponseType.SUCCESS
)
async def cmd_update_cell(args: List[str]) -> CommandResponse:
    """Update single cell configuration"""
    # Parse arguments
    parser = ArgumentParser(valid_flags={
        'tilt': float,
        'power': float,
        'rows': int,
        'cols': int,
        'freq': float,
        'roll': float,
        'height': float
    })
    parsed_args, positional_args = parser.parse_arguments(args)
    
    # Handle --help
    if parsed_args.help:
        return CommandResponse(
            content=cmd_update_cell.metadata['long_description'],
            response_type=ResponseType.TEXT
        )
    
    # Validate cell ID
    if not positional_args:
        return CommandResponse(
            content="❌ Error: Cell ID required\n\nUsage: cns update cell <id> [params]\n\nUse --help for more information.",
            response_type=ResponseType.ERROR,
            exit_code=1
        )
    
    try:
        cell_id = int(positional_args[0])
    except ValueError:
        return CommandResponse(
            content=f"❌ Error: Invalid cell ID '{positional_args[0]}' - must be an integer",
            response_type=ResponseType.ERROR,
            exit_code=1
        )
    
    # Map parsed args to API parameters
    param_map = {
        "tilt": "tilt_deg",
        "power": "tx_rs_power_dbm",
        "rows": "bs_rows",
        "cols": "bs_cols",
        "freq": "fc_hz",
        "roll": "roll_deg",
        "height": "height_m",
    }
    
    update_params = {"cell_id": cell_id}
    for key, api_key in param_map.items():
        value = getattr(parsed_args, key, None)
        if value is not None:
            update_params[api_key] = value
    
    if len(update_params) == 1:
        return CommandResponse(
            content="❌ Error: No update parameters provided\n\nUse --help to see available parameters.",
            response_type=ResponseType.ERROR,
            exit_code=1
        )
    
    try:
        result = await api_request("POST", "/update-cell", data=update_params)
        
        content = f"""✓ Updated cell {result.get('cell_id')}

  Cell Name:       {result.get('cell_name')}
  Original Name:   {result.get('original_name')}
  Fields Updated:  {', '.join(result.get('updated_fields', []))}
  
Updated Configuration:
"""
        cell = result.get('cell', {})
        for field in result.get('updated_fields', []):
            if field in ['tilt_deg', 'roll_deg', 'tx_rs_power_dbm', 'height_m', 'fc_hz', 'bs_rows', 'bs_cols']:
                content += f"  {field:<20} {cell.get(field, 'N/A')}\n"
        
        return CommandResponse(
            content=content,
            response_type=ResponseType.SUCCESS
        )
        
    except Exception as e:
        return CommandResponse(
            content=f"❌ Error updating cell: {str(e)}",
            response_type=ResponseType.ERROR,
            exit_code=1
        )


@command(
    name="update cells query",
    description="Update cells matching query criteria",
    usage="cns update cells query [query-criteria] [update-params]",
    long_description="""Update multiple cells matching query criteria

Usage: cns update cells query [query-criteria] [update-params]

Query Criteria (filter which cells to update):
  --band=<id>               Filter by band identifier (e.g., H, L, M, X)
  --site-name=<name>        Filter by site name (supports wildcards *)
  --sector-id=<0-2>         Filter by sector ID
  --tilt-min=<deg>          Minimum tilt
  --tilt-max=<deg>          Maximum tilt

Update Parameters (what to change):
  --update-tilt-deg=<deg>           New tilt angle
  --update-tx-rs-power-dbm=<dbm>    New TX power
  --update-bs-rows=<n>              New antenna rows
  --update-bs-cols=<n>              New antenna columns

Examples:
  cns update cells query --band=H --update-tilt-deg=12.0
  cns update cells query --band=M --update-tilt-deg=11.0
  cns update cells query --site-name=CNS000* --update-tilt-deg=11.0
  cns update cells query --sector-id=0 --update-tilt-deg=10.0 --update-tx-rs-power-dbm=3.0

Note: All matching cells will be updated with the same values.
""",
    response_type=ResponseType.SUCCESS
)
async def cmd_update_cells_query(args: List[str]) -> CommandResponse:
    """Update cells matching query criteria"""
    # Parse arguments
    parser = ArgumentParser(valid_flags={
        'band': str,
        'site_name': str,
        'sector_id': int,
        'tilt_min': float,
        'tilt_max': float,
        'update_tilt_deg': float,
        'update_tx_rs_power_dbm': float,
        'update_bs_rows': int,
        'update_bs_cols': int
    })
    parsed_args, positional_args = parser.parse_arguments(args)
    
    # Handle --help
    if parsed_args.help:
        return CommandResponse(
            content=cmd_update_cells_query.metadata['long_description'],
            response_type=ResponseType.TEXT
        )
    
    # Check for unexpected positional args
    if positional_args:
        return CommandResponse(
            content=f"❌ Error: Unexpected positional arguments: {', '.join(positional_args)}\n\nUse --help for more information.",
            response_type=ResponseType.ERROR,
            exit_code=1
        )
    
    # Separate query params from update params
    query_params = {}
    update_params = {}
    
    # Query parameters
    if parsed_args.band:
        query_params['band'] = parsed_args.band
    if parsed_args.site_name:
        query_params['site_name'] = parsed_args.site_name
    if parsed_args.sector_id is not None:
        query_params['sector_id'] = parsed_args.sector_id
    if parsed_args.tilt_min is not None:
        query_params['tilt_min'] = parsed_args.tilt_min
    if parsed_args.tilt_max is not None:
        query_params['tilt_max'] = parsed_args.tilt_max
    
    # Update parameters
    if parsed_args.update_tilt_deg is not None:
        update_params['update_tilt_deg'] = parsed_args.update_tilt_deg
    if parsed_args.update_tx_rs_power_dbm is not None:
        update_params['update_tx_rs_power_dbm'] = parsed_args.update_tx_rs_power_dbm
    if parsed_args.update_bs_rows is not None:
        update_params['update_bs_rows'] = parsed_args.update_bs_rows
    if parsed_args.update_bs_cols is not None:
        update_params['update_bs_cols'] = parsed_args.update_bs_cols
    
    if not update_params:
        return CommandResponse(
            content="❌ Error: No update parameters provided\n\nUse --help to see available update parameters.",
            response_type=ResponseType.ERROR,
            exit_code=1
        )
    
    # Merge params
    request_data = {**query_params, **update_params}
    
    try:
        result = await api_request("POST", "/update-cells-by-query", data=request_data)
        
        content = f"""✓ Query-Based Cell Update

  Cells Matched:    {result.get('query_matched', 0)}
  Cells Updated:    {result.get('num_updated', 0)}
  Failed Updates:   {result.get('num_failed', 0)}

Query Criteria:
"""
        for key, value in result.get('query_criteria', {}).items():
            content += f"  {key:<20} {value}\n"
        
        content += "\nUpdate Values Applied:\n"
        for key, value in result.get('update_values', {}).items():
            content += f"  {key:<20} {value}\n"
        
        if result.get('num_failed', 0) > 0:
            content += "\n⚠️ Some updates failed. Check logs for details."
        
        return CommandResponse(
            content=content,
            response_type=ResponseType.SUCCESS
        )
        
    except Exception as e:
        return CommandResponse(
            content=f"❌ Error updating cells: {str(e)}",
            response_type=ResponseType.ERROR,
            exit_code=1
        )

