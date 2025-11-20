"""
Configuration management commands for saving/loading simulation states.

Commands:
- config save <name> - Snapshot current sim state
- config load <name> - Restore saved state
- config list - List all saved configs
- config delete <name> - Delete a saved config
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import List
from api_client import api_request
from arango_client import get_state_manager
from framework import command, CommandResponse, ResponseType, ArgumentParser


@command(
    name="config save",
    description="Save current simulation state as named configuration",
    usage="srs config save <name> [--description '...']",
    long_description="""Save current simulation state as named configuration

Usage: srs config save <name> [--description "description"]

Arguments:
  <name>                Configuration name (required)
  --description="..."   Optional description

This command:
1. Queries Sionna API for current state (all cells, UEs)
2. Retrieves init config from session cache
3. Saves complete snapshot to ArangoDB

Example:
  srs config save baseline --description="Baseline configuration"
  srs config save optimized-tilts --description="High band at 12°"
""",
    response_type=ResponseType.SUCCESS
)
async def cmd_config_save(args: List[str]) -> CommandResponse:
    """Save current simulation state as named configuration"""
    # Parse arguments
    parser = ArgumentParser(valid_flags={
        'description': str
    })
    parsed_args, positional_args = parser.parse_arguments(args)
    
    # Handle --help
    if parsed_args.help:
        return CommandResponse(
            content=cmd_config_save.metadata['long_description'],
            response_type=ResponseType.TEXT
        )
    
    # Validate config name
    if not positional_args:
        return CommandResponse(
            content="❌ Error: Configuration name required\n\nUsage: cns config save <name> [--description '...']\n\nUse --help for more information.",
            response_type=ResponseType.ERROR,
            exit_code=1
        )
    
    config_name = positional_args[0]
    description = parsed_args.description or ""
    
    # Get state manager
    state_mgr = get_state_manager()
    if not state_mgr:
        return CommandResponse(
            content="❌ Error: ArangoDB not available\nConfig save/load features disabled.",
            response_type=ResponseType.ERROR,
            exit_code=1
        )
    
    try:
        # 1. Get init config from session cache
        init_config = state_mgr.get_init_config()
        if not init_config:
            return CommandResponse(
                content="❌ Error: No initialization config found in session\n\nYou must initialize the simulation first:\n  cns init --default",
                response_type=ResponseType.ERROR,
                exit_code=1
            )
        
        # 2. Query Sionna API for current state
        # Get all cells
        cells_response = await api_request("GET", "/cells")
        all_cells = cells_response.get('cells', [])
        
        # Extract cell parameters (mutable + reference data for analysis)
        cells_state = []
        for cell in all_cells:
            cell_params = {
                'cell_id': cell['cell_idx'],  # Identifier
                'cell_name': cell.get('cell_name'),  # Reference
                'site_name': cell.get('site_name'),  # Reference
                'band': cell.get('band'),  # Reference (important for filtering/querying)
                'x': cell.get('x'),  # Reference (for plotting)
                'y': cell.get('y'),  # Reference (for plotting)
                'sector_id': cell.get('sector_id'),  # Reference
                'sector_az_deg': cell.get('sector_az_deg'),  # Reference
                # Mutable parameters (restored on load)
                'fc_hz': cell.get('fc_hz'),
                'tx_rs_power_dbm': cell.get('tx_rs_power_dbm'),
                'tilt_deg': cell.get('tilt_deg'),
                'roll_deg': cell.get('roll_deg'),
                'height_m': cell.get('height_m_effective'),
                'bs_rows': cell.get('bs_rows'),
                'bs_cols': cell.get('bs_cols'),
                'bs_pol': cell.get('bs_pol'),
                'bs_pol_type': cell.get('bs_pol_type'),
                'elem_v_spacing': cell.get('elem_v_spacing'),
                'elem_h_spacing': cell.get('elem_h_spacing'),
                'antenna_pattern': cell.get('antenna_pattern'),
            }
            cells_state.append(cell_params)
        
        # Get UE count (for display only, not restored on load)
        ues_response = await api_request("GET", "/ues")
        ues_state = {
            'num_ues': ues_response.get('num_ues', 0)
        }
        
        # Get topology info
        status_response = await api_request("GET", "/status")
        topology = {
            'num_sites': status_response.get('num_sites', 0),
            'num_cells': status_response.get('num_cells', 0),
            'num_bands': status_response.get('num_bands', 0),
            'bands': status_response.get('bands', [])
        }
        
        # 3. Save to ArangoDB
        saved_config = state_mgr.save_config(
            name=config_name,
            init_config=init_config,
            cells_state=cells_state,
            ues_state=ues_state,
            topology=topology,
            description=description
        )
        
        # 4. Return success message
        content = f"""✓ Configuration Saved: {config_name}

  Sites:  {topology['num_sites']}
  Cells:  {topology['num_cells']} (mutable params: tilt, power, antenna config)
  UEs:    {ues_state['num_ues']:,}
  Bands:  {', '.join(topology['bands'])}
  
{f'  Description: {description}' if description else ''}

Saved: Init config + cell parameters (tilt, power, etc.)

Use 'cns config load {config_name}' to restore this configuration.
Use 'cns config list' to see all saved configurations.
"""
        return CommandResponse(
            content=content,
            response_type=ResponseType.SUCCESS
        )
    
    except Exception as e:
        return CommandResponse(
            content=f"❌ Error saving configuration: {str(e)}",
            response_type=ResponseType.ERROR,
            exit_code=1
        )


@command(
    name="config load",
    description="Load saved configuration and restore simulation state",
    usage="cns config load <name>",
    long_description="""Load saved configuration and restore simulation state

Usage: cns config load <name>

This command:
1. Loads saved config from ArangoDB
2. Re-initializes simulation with saved init params (includes default UE drop)
3. Applies all cell parameter updates from saved state (tilts, power, etc.)

Example:
  cns config load baseline
  cns config load optimized-tilts
""",
    response_type=ResponseType.SUCCESS
)
async def cmd_config_load(args: List[str]) -> CommandResponse:
    """Load saved configuration and restore simulation state"""
    # Parse arguments
    parser = ArgumentParser()
    parsed_args, positional_args = parser.parse_arguments(args)
    
    # Handle --help
    if parsed_args.help:
        return CommandResponse(
            content=cmd_config_load.metadata['long_description'],
            response_type=ResponseType.TEXT
        )
    
    # Validate config name
    if not positional_args:
        return CommandResponse(
            content="❌ Error: Configuration name required\n\nUsage: cns config load <name>\n\nUse 'cns config list' to see available configurations.",
            response_type=ResponseType.ERROR,
            exit_code=1
        )
    
    config_name = positional_args[0]
    
    # Get state manager
    state_mgr = get_state_manager()
    if not state_mgr:
        return CommandResponse(
            content="❌ Error: ArangoDB not available\nConfig save/load features disabled.",
            response_type=ResponseType.ERROR,
            exit_code=1
        )
    
    try:
        # 1. Load config from ArangoDB
        config = state_mgr.load_config(config_name)
        
        if not config:
            return CommandResponse(
                content=f"❌ Error: Configuration '{config_name}' not found\n\nUse 'cns config list' to see available configurations.",
                response_type=ResponseType.ERROR,
                exit_code=1
            )
        
        # 2. Re-initialize simulation with saved init config
        init_result = await api_request("POST", "/initialize", data=config['init_config'])
        
        # 3. Apply all cell updates from saved state
        # cells_state already contains only mutable params in correct format
        cells_to_update = config['cells_state']
        
        # Apply all updates in bulk
        if cells_to_update:
            await api_request("POST", "/update-cells-bulk", data={
                'updates': cells_to_update,
                'stop_on_error': False
            })
        
        # 4. Update session cache with loaded init config
        state_mgr.save_init_config(config['init_config'])
        
        # 5. Return success message
        # Note: UEs already dropped during init, config focuses on cell parameters only
        content = f"""✓ Configuration Loaded: {config_name}

  Sites:  {config['topology']['num_sites']}
  Cells:  {config['topology']['num_cells']}
  Cell parameters restored: {len(cells_to_update)} (tilts, power, antenna config)
  
{f"  Description: {config['description']}" if config.get('description') else ''}

Simulation restored to saved state.
Use 'cns query cells' to verify cell parameters.
"""
        return CommandResponse(
            content=content,
            response_type=ResponseType.SUCCESS
        )
    
    except Exception as e:
        return CommandResponse(
            content=f"❌ Error loading configuration: {str(e)}",
            response_type=ResponseType.ERROR,
            exit_code=1
        )


@command(
    name="config list",
    description="List all saved configurations",
    usage="cns config list",
    long_description="""List all saved configurations

Usage: cns config list

Shows all saved simulation configurations with metadata.

Example:
  cns config list
""",
    response_type=ResponseType.TABLE
)
async def cmd_config_list(args: List[str]) -> CommandResponse:
    """List all saved configurations"""
    # Parse arguments
    parser = ArgumentParser()
    parsed_args, positional_args = parser.parse_arguments(args)
    
    # Handle --help
    if parsed_args.help:
        return CommandResponse(
            content=cmd_config_list.metadata['long_description'],
            response_type=ResponseType.TEXT
        )
    
    # Reject any positional arguments
    if positional_args:
        return CommandResponse(
            content=f"❌ Error: 'config list' does not accept arguments: {' '.join(positional_args)}\n\nUsage: cns config list",
            response_type=ResponseType.ERROR,
            exit_code=1
        )
    
    # Get state manager
    state_mgr = get_state_manager()
    if not state_mgr:
        return CommandResponse(
            content="❌ Error: ArangoDB not available\nConfig save/load features disabled.",
            response_type=ResponseType.ERROR,
            exit_code=1
        )
    
    try:
        # Get all configs
        configs = state_mgr.list_configs()
        
        if not configs:
            return CommandResponse(
                content="No saved configurations found.\n\nUse 'cns config save <name>' to save current simulation state.",
                response_type=ResponseType.TEXT
            )
        
        # Build table
        from framework import TableData
        
        headers = ["Config ID", "Created", "Sites", "Cells", "UEs", "Bands", "Description"]
        rows = []
        
        for cfg in configs:
            # Format timestamp
            created = cfg['created_at']
            if 'T' in created:
                created = created[:19].replace('T', ' ')  # Trim timestamp like snapshot list
            
            # Format bands
            bands = ', '.join(cfg.get('bands', []))
            if not bands:
                bands = 'N/A'
            
            description = cfg.get('description', '')
            if description and len(description) > 40:
                description = description[:37] + '...'
            
            rows.append([
                cfg['name'],
                created,
                str(cfg['num_sites']),
                str(cfg['num_cells']),
                f"{cfg['num_ues']:,}",
                bands,
                description
            ])
        
        table = TableData(
            headers=headers,
            rows=rows,
            title=f"Found {len(configs)} saved configuration(s)"
        )
        
        footer = "Use 'cns config load <name>' to restore a configuration."
        
        return CommandResponse(
            content=table,
            response_type=ResponseType.TABLE,
            footer=footer
        )
    
    except Exception as e:
        return CommandResponse(
            content=f"❌ Error listing configurations: {str(e)}",
            response_type=ResponseType.ERROR,
            exit_code=1
        )


@command(
    name="config delete",
    description="Delete a saved configuration",
    usage="cns config delete <name>",
    long_description="""Delete a saved configuration

Usage: cns config delete <name>

Permanently removes a saved configuration from storage.

Example:
  cns config delete old-test
""",
    response_type=ResponseType.SUCCESS
)
async def cmd_config_delete(args: List[str]) -> CommandResponse:
    """Delete a saved configuration"""
    # Parse arguments
    parser = ArgumentParser()
    parsed_args, positional_args = parser.parse_arguments(args)
    
    # Handle --help
    if parsed_args.help:
        return CommandResponse(
            content=cmd_config_delete.metadata['long_description'],
            response_type=ResponseType.TEXT
        )
    
    # Validate config name
    if not positional_args:
        return CommandResponse(
            content="❌ Error: Configuration name required\n\nUsage: cns config delete <name>\n\nUse 'cns config list' to see available configurations.",
            response_type=ResponseType.ERROR,
            exit_code=1
        )
    
    config_name = positional_args[0]
    
    # Get state manager
    state_mgr = get_state_manager()
    if not state_mgr:
        return CommandResponse(
            content="❌ Error: ArangoDB not available\nConfig save/load features disabled.",
            response_type=ResponseType.ERROR,
            exit_code=1
        )
    
    try:
        # Check if exists
        if not state_mgr.config_exists(config_name):
            return CommandResponse(
                content=f"❌ Error: Configuration '{config_name}' not found\n\nUse 'cns config list' to see available configurations.",
                response_type=ResponseType.ERROR,
                exit_code=1
            )
        
        # Delete
        success = state_mgr.delete_config(config_name)
        
        if success:
            return CommandResponse(
                content=f"✓ Configuration deleted: {config_name}",
                response_type=ResponseType.SUCCESS
            )
        else:
            return CommandResponse(
                content=f"❌ Error: Failed to delete configuration '{config_name}'",
                response_type=ResponseType.ERROR,
                exit_code=1
            )
    
    except Exception as e:
        return CommandResponse(
            content=f"❌ Error deleting configuration: {str(e)}",
            response_type=ResponseType.ERROR,
            exit_code=1
        )
