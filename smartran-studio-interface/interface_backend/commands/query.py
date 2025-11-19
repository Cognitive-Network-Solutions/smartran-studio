"""
Query commands for cells, sites, and UEs - Framework version
"""
import sys
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from api_client import api_request
from framework import command, CommandResponse, ResponseType, TableData, CommandArgument, ArgumentType


@command(
    name="query_cells",
    description="Query cells with optional filter criteria",
    usage="cns query cells [options]",
    examples=[
        "cns query cells",
        "cns query cells --band=H",
        "cns query cells --site-name=CNS000*",
        "cns query cells --tilt-min=8 --tilt-max=10",
        "cns query cells --band=H --limit=20"
    ],
    arguments=[
        CommandArgument("band", ArgumentType.STRING,
                       help_text="Filter by band identifier (e.g., H, L, M, X)"),
        CommandArgument("site_name", ArgumentType.STRING,
                       help_text="Filter by site name (supports wildcards *)"),
        CommandArgument("sector_id", ArgumentType.INTEGER,
                       help_text="Filter by sector (0, 1, or 2)"),
        CommandArgument("site_idx", ArgumentType.INTEGER,
                       help_text="Filter by site index"),
        CommandArgument("tilt_min", ArgumentType.FLOAT,
                       help_text="Minimum tilt angle"),
        CommandArgument("tilt_max", ArgumentType.FLOAT,
                       help_text="Maximum tilt angle"),
        CommandArgument("fc_ghz_min", ArgumentType.FLOAT,
                       help_text="Minimum frequency (GHz)"),
        CommandArgument("fc_ghz_max", ArgumentType.FLOAT,
                       help_text="Maximum frequency (GHz)"),
        CommandArgument("bs_rows", ArgumentType.INTEGER,
                       help_text="Antenna rows"),
        CommandArgument("bs_cols", ArgumentType.INTEGER,
                       help_text="Antenna columns"),
        CommandArgument("limit", ArgumentType.INTEGER,
                       help_text="Max results to return"),
        CommandArgument("offset", ArgumentType.INTEGER,
                       help_text="Skip first n results"),
    ],
    response_type=ResponseType.TABLE,
    category="Query"
)
async def cmd_query_cells(args: Dict[str, Any]) -> CommandResponse:
    """Query cells with optional filter criteria"""
    
    try:
        # Send query to API
        if args:
            result = await api_request("POST", "/query-cells", data=args)
        else:
            result = await api_request("GET", "/cells")
            result = {"cells": result["cells"], "num_results": len(result["cells"]), "total_matches": len(result["cells"])}
        
        cells = result.get("cells", [])
        
        if not cells:
            query_info = ", ".join([f"{k}={v}" for k, v in args.items()]) if args else "none"
            return CommandResponse(
                content=f"No cells found matching criteria\n\nQuery: {query_info}\nTotal matches: {result.get('total_matches', 0)}",
                response_type=ResponseType.INFO
            )
        
        # Prepare table data (max 100 rows)
        display_cells = cells[:100]
        table_rows = []
        
        for cell in display_cells:
            table_rows.append([
                cell.get('cell_idx', 'N/A'),
                cell.get('site_name', 'N/A'),
                cell.get('cell_name', 'N/A'),
                cell.get('band', 'N/A'),
                f"({cell.get('x', 0):.1f}, {cell.get('y', 0):.1f})",
                f"{cell.get('sector_az_deg', 0):.1f}°",
                f"{cell.get('fc_MHz', 0):.1f}",
                f"{cell.get('tilt_deg', 0):.1f}°" if cell.get('tilt_deg') is not None else 'N/A',
                f"{cell.get('bs_rows', 0)}x{cell.get('bs_cols', 0)}",
                cell.get('antenna_pattern', 'N/A')
            ])
        
        headers = ["Idx", "Site ID", "Cell ID", "Band", "Position (X, Y)", "Azimuth", "Freq(MHz)", "Tilt", "Antenna Array", "Pattern"]
        
        # Format header message
        header_msg = f"Found {result.get('total_matches', len(cells))} cells"
        if args:
            query_str = ", ".join([f"{k}={v}" for k, v in args.items()])
            header_msg += f" (filter: {query_str})"
        if len(cells) > 100:
            header_msg += f" - showing first 100"
        
        footer_msg = None
        if len(cells) > 100:
            footer_msg = f"... and {len(cells) - 100} more cells"
        
        return CommandResponse(
            content=TableData(
                headers=headers,
                rows=table_rows,
                title=header_msg
            ),
            response_type=ResponseType.TABLE,
            header=header_msg,
            footer=footer_msg
        )
        
    except Exception as e:
        return CommandResponse(
            content=f"Error querying cells: {str(e)}",
            response_type=ResponseType.ERROR
        )


@command(
    name="query_sites",
    description="Query all sites in the simulation",
    usage="cns query sites",
    examples=["cns query sites"],
    response_type=ResponseType.TABLE,
    category="Query"
)
async def cmd_query_sites(args: Dict[str, Any]) -> CommandResponse:
    """Query all sites"""
    
    try:
        result = await api_request("GET", "/sites")
        sites = result.get("sites", [])
        
        if not sites:
            return CommandResponse(
                content="No sites found",
                response_type=ResponseType.INFO
            )
        
        # Prepare table data
        table_rows = []
        for site in sites:
            table_rows.append([
                site.get('idx', 'N/A'),
                site.get('name', 'N/A'),
                f"({site.get('x', 0):.1f}, {site.get('y', 0):.1f})",
                f"{site.get('height_m', 0):.1f}m",
                site.get('n_cells', 0)
            ])
        
        headers = ["Idx", "Site ID", "Position (X, Y)", "Height", "Cells"]
        
        return CommandResponse(
            content=TableData(
                headers=headers,
                rows=table_rows,
                title=f"Found {len(sites)} sites"
            ),
            response_type=ResponseType.TABLE,
            header=f"Found {len(sites)} sites"
        )
        
    except Exception as e:
        return CommandResponse(
            content=f"Error querying sites: {str(e)}",
            response_type=ResponseType.ERROR
        )


@command(
    name="query_ues",
    description="Query User Equipment (UE) information",
    usage="cns query ues",
    examples=["cns query ues"],
    response_type=ResponseType.TEXT,
    category="Query"
)
async def cmd_query_ues(args: Dict[str, Any]) -> CommandResponse:
    """Query UE information"""
    
    try:
        result = await api_request("GET", "/ues")
        
        output = f"""UE Information:

  Count:        {result.get('num_ues', 0):,}
  Layout:       {result.get('layout', 'N/A')}
  Height:       {result.get('drop_params', {}).get('height_m', 'N/A')}m
  
Drop Parameters:
"""
        
        drop_params = result.get('drop_params', {})
        for key, value in drop_params.items():
            if key != 'num_ue':
                output += f"  {key:<15} {value}\n"
        
        if result.get('has_results', False):
            results = result.get('results', {})
            output += f"""
Compute Results Available:
  Cells Computed:       {results.get('num_cells_computed', 0)}
  RSRP Matrix Shape:    {results.get('rsrp_shape', 'N/A')}
  UEs with Assignment:  {results.get('num_ues_with_assignment', 0):,}
"""
        else:
            output += "\nNo compute results yet. Run 'cns sim compute' to generate RSRP data."
        
        return CommandResponse(
            content=output,
            response_type=ResponseType.TEXT
        )
        
    except Exception as e:
        return CommandResponse(
            content=f"Error querying UEs: {str(e)}",
            response_type=ResponseType.ERROR
        )
