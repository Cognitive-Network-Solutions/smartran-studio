"""
Simulation operation commands (compute, drop UEs)
"""
import sys
from pathlib import Path
from typing import List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from api_client import api_request
from framework import command, CommandResponse, ResponseType, ArgumentParser, CommandArgument, ArgumentType, registry


@command(
    name="sim compute",
    description="Run simulation compute to generate RSRP measurements",
    usage="srs sim compute --name=<name> [options]",
    long_description="""Run simulation compute to generate RSRP measurements

Usage: srs sim compute --name=<name> [options]

Required:
  --name=<name>           Snapshot name (required, for easy identification)

Options:
  --threshold=<dbm>       RSRP threshold in dBm (default: -120.0)
  --label-mode=<mode>     Label mode: 'name' or 'idx' (default: name)

Description:
  Computes RSRP (Reference Signal Received Power) for all UEs from all cells.
  This is the main simulation operation that generates measurement reports.
  
  Each snapshot gets:
  - A unique ID (timestamp) used as database key
  - A name (your label) for easy identification
  
  Note: This operation can take time depending on UE count and complexity.
  The command will wait for completion before returning results.

Output:
  - Number of measurement reports generated
  - UEs processed
  - Bands computed
  - Completion timestamp

Examples:
  srs sim compute --name="baseline-run"
  srs sim compute --name="optimized-tilts" --threshold=-110
  srs sim compute --name="test-v2" --label-mode=idx
""",
    response_type=ResponseType.SUCCESS
)
async def cmd_compute(args: List[str]) -> CommandResponse:
    """Run simulation compute"""
    # Parse arguments
    parser = ArgumentParser(valid_flags={
        'name': str,
        'threshold': float,
        'label_mode': str
    })
    parsed_args, positional_args = parser.parse_arguments(args)
    
    # Handle --help
    if parsed_args.help:
        return CommandResponse(
            content=cmd_compute.metadata['long_description'],
            response_type=ResponseType.TEXT
        )
    
    # Check for unexpected positional args
    if positional_args:
        return CommandResponse(
            content=f"❌ Error: Unexpected positional arguments: {', '.join(positional_args)}\n\nUse --help for more information.",
            response_type=ResponseType.ERROR,
            exit_code=1
        )
    
    # Validate required name parameter
    if not parsed_args.name:
        return CommandResponse(
            content="❌ Error: Snapshot name is required\n\nUsage: srs sim compute --name=<name>\n\nExample: srs sim compute --name=\"baseline-run\"",
            response_type=ResponseType.ERROR,
            exit_code=1
        )
    
    snapshot_name = parsed_args.name
    
    # Set defaults
    threshold_dbm = parsed_args.threshold if parsed_args.threshold is not None else -120.0
    label_mode = parsed_args.label_mode or "name"
    
    # Validate label_mode
    if label_mode not in ["name", "idx"]:
        return CommandResponse(
            content=f"❌ Error: Invalid label-mode '{label_mode}'\n\nMust be: 'name' or 'idx'",
            response_type=ResponseType.ERROR,
            exit_code=1
        )
    
    try:
        params = {
            "name": snapshot_name,
            "threshold_dbm": threshold_dbm,
            "label_mode": label_mode
        }
        result = await api_request("POST", "/measurement-reports", params=params)
        
        # Extract new response format
        run_id = result.get('run_id', 'N/A')
        num_reports = result.get('num_reports', 0)
        metadata = result.get('metadata', {})
        access = result.get('access', {})
        
        bands_str = ', '.join(metadata.get('bands', []))
        
        # Get init config summary
        init_summary = metadata.get('init_config_summary', {})
        num_sites = init_summary.get('n_sites', metadata.get('num_sites', 0))
        
        # Get cell count from captured states
        cell_states = metadata.get('cell_states_at_run', [])
        num_cells = len(cell_states)
        
        content = f"""
╔════════════════════════════════════════════════════════════╗
║          ✓ SIMULATION COMPUTE COMPLETED                    ║
╚════════════════════════════════════════════════════════════╝

  Snapshot Name:           {snapshot_name}
  Snapshot ID:             {run_id}
  
  UEs:                     {metadata.get('num_users', 0):,}
  Sites:                   {num_sites}
  Cells:                   {num_cells}
  Bands:                   {bands_str}
  Reports Generated:       {num_reports:,}

View Snapshot:
  • srs snapshot get {run_id}
  • srs snapshot list

✓ Measurement data stored in ArangoDB
"""
        return CommandResponse(
            content=content,
            response_type=ResponseType.SUCCESS
        )
        
    except Exception as e:
        return CommandResponse(
            content=f"❌ Error running compute: {str(e)}",
            response_type=ResponseType.ERROR,
            exit_code=1
        )


@command(
    name="drop ues",
    description="Drop or redrop User Equipment (UEs) in simulation",
    usage="srs drop ues <count> [options]",
    long_description="""Drop or redrop User Equipment (UEs) in the simulation

Usage: srs drop ues <count> [options]

Arguments:
  <count>                Number of UEs to drop (required)

Options:
  --layout=<box|disk>    Layout type (default: box)
  --box-pad=<m>          Box padding in meters (default: 500.0)
  --radius=<m>           Disk radius in meters (default: 500.0)
  --height=<m>           UE height in meters (default: 1.5)
  --seed=<n>             Random seed (default: 7)

Description:
  Drops UEs in the simulation area using either box or disk layout.
  
  Box layout: UEs distributed in rectangular area with padding around sites
  Disk layout: UEs distributed in circular area with specified radius
  
  Note: Dropping UEs invalidates previous compute results.

Examples:
  srs drop ues 50000                        # Drop 50K UEs with defaults
  srs drop ues 50000 --layout=box --box-pad=300  # Custom box padding
  srs drop ues 20000 --layout=disk --radius=1000 # Disk layout
  srs drop ues 30000 --height=1.8 --seed=42      # Custom height and seed
""",
    response_type=ResponseType.SUCCESS
)
async def cmd_drop_ues(args: List[str]) -> CommandResponse:
    """Drop/redrop UEs in simulation"""
    # Parse arguments
    parser = ArgumentParser(valid_flags={
        'layout': str,
        'box_pad': float,
        'radius': float,
        'height': float,
        'seed': int
    })
    parsed_args, positional_args = parser.parse_arguments(args)
    
    # Handle --help
    if parsed_args.help:
        return CommandResponse(
            content=cmd_drop_ues.metadata['long_description'],
            response_type=ResponseType.TEXT
        )
    
    # Validate UE count
    if not positional_args:
        return CommandResponse(
            content="❌ Error: Number of UEs required\n\nUsage: srs drop ues <count> [params]\n\nUse --help for more information.",
            response_type=ResponseType.ERROR,
            exit_code=1
        )
    
    try:
        num_ue = int(positional_args[0])
    except ValueError:
        return CommandResponse(
            content=f"❌ Error: Invalid UE count '{positional_args[0]}' - must be an integer",
            response_type=ResponseType.ERROR,
            exit_code=1
        )
    
    # Build params
    params = {"num_ue": num_ue}
    
    if parsed_args.layout:
        if parsed_args.layout not in ["box", "disk"]:
            return CommandResponse(
                content=f"❌ Error: Invalid layout '{parsed_args.layout}'\n\nMust be: 'box' or 'disk'",
                response_type=ResponseType.ERROR,
                exit_code=1
            )
        params["layout"] = parsed_args.layout
    
    if parsed_args.box_pad is not None:
        params["box_pad_m"] = parsed_args.box_pad
    if parsed_args.radius is not None:
        params["radius_m"] = parsed_args.radius
    if parsed_args.height is not None:
        params["height_m"] = parsed_args.height
    if parsed_args.seed is not None:
        params["seed"] = parsed_args.seed
    
    try:
        result = await api_request("POST", "/drop-ues", data=params)
        
        content = f"""✓ UEs Dropped Successfully

  Count:        {result.get('num_ues', 0):,}
  Layout:       {result.get('drop_params', {}).get('layout', 'N/A')}
  
Drop Parameters:
"""
        for key, value in result.get('drop_params', {}).items():
            content += f"  {key:<15} {value}\n"
        
        content += "\n⚠️ Note: Previous compute results are now invalid."
        content += "\nRun 'srs sim compute' to generate new RSRP data."
        
        return CommandResponse(
            content=content,
            response_type=ResponseType.SUCCESS
        )
        
    except Exception as e:
        return CommandResponse(
            content=f"❌ Error dropping UEs: {str(e)}",
            response_type=ResponseType.ERROR,
            exit_code=1
        )


@command(
    name="snapshot list",
    description="List all measurement snapshots stored in ArangoDB",
    usage="srs snapshot list [options]",
    long_description="""List all measurement snapshots stored in ArangoDB

A snapshot is a saved set of measurement reports from a compute operation.
Each snapshot captures the complete network state at that point in time.

Usage: srs snapshot list [options]

Options:
  --limit=<n>         Maximum number of snapshots to show (default: 20)
  --offset=<n>        Number of snapshots to skip (default: 0)
  --sort=<field>      Field to sort by (default: created_at)
  --order=<asc|desc>  Sort order (default: desc)

Examples:
  srs snapshot list                        # Show 20 most recent snapshots
  srs snapshot list --limit=50             # Show 50 most recent snapshots
  srs snapshot list --offset=20            # Skip first 20, show next batch
""",
    arguments=[
        CommandArgument("limit", ArgumentType.INTEGER, 
                       help_text="Maximum number of snapshots to return (default: 20)"),
        CommandArgument("offset", ArgumentType.INTEGER,
                       help_text="Number of snapshots to skip (default: 0)"),
        CommandArgument("sort", ArgumentType.STRING,
                       help_text="Field to sort by (default: created_at)"),
        CommandArgument("order", ArgumentType.STRING,
                       help_text="Sort order: asc or desc (default: desc)")
    ]
)
async def cmd_snapshot_list(args: List[str]) -> CommandResponse:
    """List all measurement snapshots"""
    from framework import FrameworkArgumentParser
    parsed_args = FrameworkArgumentParser.parse(args, registry.get_command("snapshot list")['metadata'].arguments)
    
    # parsed_args is a dict, use dict access
    limit = parsed_args.get('limit', 20)
    offset = parsed_args.get('offset', 0)
    sort_by = parsed_args.get('sort', 'created_at')
    sort_order = parsed_args.get('order', 'desc')
    
    try:
        params = {
            "limit": limit,
            "offset": offset,
            "sort_by": sort_by,
            "sort_order": sort_order
        }
        result = await api_request("GET", "/runs", params=params)
        
        runs = result.get('runs', [])
        total = result.get('total', 0)
        
        if not runs:
            return CommandResponse(
                content="No measurement snapshots found.\n\nRun 'srs sim compute' to create your first snapshot.",
                response_type=ResponseType.TEXT
            )
        
        # Build table
        from framework import TableData
        
        headers = ["Snapshot ID", "Name", "Created", "UEs", "Sites", "Cells", "Bands", "Reports"]
        rows = []
        
        for run in runs:
            bands = ', '.join(run.get('bands', []))
            rows.append([
                run.get('run_id', 'N/A'),
                run.get('name', 'N/A'),
                run.get('created_at', 'N/A')[:19].replace('T', ' '),  # Trim timestamp
                f"{run.get('num_ues', 0):,}",
                str(run.get('num_sites', 'N/A')),
                str(run.get('num_cells', 'N/A')),
                bands,
                f"{run.get('num_reports', 0):,}"
            ])
        
        table = TableData(
            headers=headers,
            rows=rows,
            title=f"Measurement Snapshots ({len(runs)} of {total} total)"
        )
        
        footer = f"\nShowing {offset+1} to {offset+len(runs)} of {total} snapshots"
        footer += f"\n\nUse 'srs snapshot get <snapshot_id>' to see details"
        
        return CommandResponse(
            content=table,
            response_type=ResponseType.TABLE,
            footer=footer
        )
        
    except Exception as e:
        return CommandResponse(
            content=f"❌ Error listing snapshots: {str(e)}",
            response_type=ResponseType.ERROR,
            exit_code=1
        )


@command(
    name="snapshot get",
    description="Get detailed metadata for a specific measurement snapshot",
    usage="srs snapshot get <snapshot_id>",
    long_description="""Get detailed metadata for a specific measurement snapshot

A snapshot contains all measurement reports and network configuration
from a compute operation, including cell tilts and init settings.

Usage: srs snapshot get <snapshot_id>

Arguments:
  <snapshot_id>    The snapshot ID (timestamp format like "2025-11-06_00-05-22")

Examples:
  srs snapshot get 2025-11-06_00-05-22    # Get snapshot details
"""
)
async def cmd_snapshot_get(args: List[str]) -> CommandResponse:
    """Get detailed metadata for a specific snapshot"""
    # Handle positional argument directly
    if not args or len(args) == 0:
        return CommandResponse(
            content="❌ Error: snapshot_id required\n\nUsage: srs snapshot get <snapshot_id>\n\nExample: srs snapshot get 2025-11-06_04-47-22",
            response_type=ResponseType.ERROR,
            exit_code=1
        )
    
    snapshot_id = args[0]
    
    try:
        result = await api_request("GET", f"/runs/{snapshot_id}")
        
        metadata = result.get('metadata', {})
        init_summary = metadata.get('init_config_summary', {})
        
        # Get cell count from captured states
        cell_states = metadata.get('cell_states_at_run', [])
        num_cells = len(cell_states)
        
        # Build output
        snapshot_name = metadata.get('name', 'N/A')
        content = f"""Snapshot Details: {snapshot_id}
{'=' * 60}

Name:                 {snapshot_name}
Created:              {result.get('created_at', 'N/A')}
Measurement Reports:  {result.get('num_reports', 0):,}

Network State (at snapshot time):
  UEs:                {metadata.get('num_users', 0):,}
  Sites:              {init_summary.get('n_sites', 'N/A')}
  Cells:              {num_cells}
  Bands:              {', '.join(metadata.get('bands', []))}

"""
        
        # Add init config summary if available
        if init_summary:
            high_band = init_summary.get('high_band', {})
            low_band = init_summary.get('low_band', {})
            
            content += f"""Initial Configuration:
  Spacing:            {init_summary.get('spacing_m', 0)} m
  Seed:               {init_summary.get('seed', 0)}
  Site Height:        {init_summary.get('site_height_m', 0)} m
  
  High Band:
    Frequency:        {high_band.get('fc_ghz', 0):.2f} GHz
    Initial Tilt:     {high_band.get('tilt_deg', 0)}°
    Antenna:          {high_band.get('antenna', 'N/A')}
  
  Low Band:
    Frequency:        {low_band.get('fc_ghz', 0):.2f} GHz
    Initial Tilt:     {low_band.get('tilt_deg', 0)}°
    Antenna:          {low_band.get('antenna', 'N/A')}

"""
        
        content += f"""Cell States (Captured at Snapshot):
  {len(cell_states)} cells with full configuration

This snapshot preserves the exact cell tilts and settings used.
"""
        
        return CommandResponse(
            content=content,
            response_type=ResponseType.TEXT
        )
        
    except Exception as e:
        return CommandResponse(
            content=f"❌ Error getting snapshot: {str(e)}",
            response_type=ResponseType.ERROR,
            exit_code=1
        )


@command(
    name="snapshot delete",
    description="Delete a measurement snapshot and all its reports",
    usage="srs snapshot delete <snapshot_id>",
    long_description="""Delete a measurement snapshot and all its associated reports from ArangoDB

Permanently removes a snapshot and all measurement reports stored with it.

Usage: srs snapshot delete <snapshot_id>

Arguments:
  <snapshot_id>    The snapshot ID to delete

Examples:
  srs snapshot delete 2025-11-06_00-05-22    # Delete snapshot and all reports

⚠️ WARNING: This action cannot be undone!
"""
)
async def cmd_snapshot_delete(args: List[str]) -> CommandResponse:
    """Delete a measurement snapshot and all its reports"""
    # Handle positional argument directly
    if not args or len(args) == 0:
        return CommandResponse(
            content="❌ Error: snapshot_id required\n\nUsage: srs snapshot delete <snapshot_id>\n\nExample: srs snapshot delete 2025-11-06_04-47-22\n\n⚠️ WARNING: This action cannot be undone!",
            response_type=ResponseType.ERROR,
            exit_code=1
        )
    
    snapshot_id = args[0]
    
    try:
        result = await api_request("DELETE", f"/runs/{snapshot_id}")
        
        content = f"""✓ Snapshot Deleted Successfully

  Snapshot ID:          {result.get('run_id', snapshot_id)}
  Reports Deleted:      {result.get('num_reports_deleted', 0):,}
  
{result.get('message', 'Snapshot deleted')}
"""
        
        return CommandResponse(
            content=content,
            response_type=ResponseType.SUCCESS
        )
        
    except Exception as e:
        return CommandResponse(
            content=f"❌ Error deleting snapshot: {str(e)}",
            response_type=ResponseType.ERROR,
            exit_code=1
        )
