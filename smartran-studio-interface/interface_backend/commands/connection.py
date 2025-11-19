"""
Connection and network management commands - Framework version
"""
from typing import Dict, Any
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import CONFIG
from session import session
from api_client import api_request
from framework import command, CommandResponse, ResponseType, CommandArgument, ArgumentType


@command(
    name="help",
    description="Show help message with available commands",
    usage="help",
    examples=["help"],
    response_type=ResponseType.INFO,
    category="General",
    requires_connection=False
)
async def cmd_help(args: Dict[str, Any]) -> CommandResponse:
    """Show help message"""
    content = """SmartRAN Studio CLI - Radio Access Network Simulation Interface

USAGE:
  <command> [arguments]

CONNECTION MANAGEMENT:
  connect <network>         Connect to a network (sim, prod, etc.)
  disconnect                Disconnect from current network
  networks                  List available networks
  status                    Show connection status and network info

SIMULATION INITIALIZATION:
  init                      Initialize simulation with interactive wizard
  init --default            Initialize with ALL defaults (one command)
  init --config <json>      Initialize with custom JSON config
  reinit                    Reinitialize simulation with defaults

QUERY COMMANDS:
  query cells               List all cells
  query cells <criteria>    Query cells with filter criteria
                            Example: query cells --band=H --tilt-min=10
  query sites               List all sites
  query ues                 Show UE information

UPDATE COMMANDS:
  update cell <id> <params> Update single cell configuration
                            Example: update cell 0 --tilt=12.0
  update cells bulk <json>  Bulk update multiple cells
  update cells query <...>  Update cells matching query criteria
                            Example: update cells query --band=M --update-tilt-deg=11.0
  
SIMULATION OPERATIONS:
  sim compute --name=<name> Run fresh simulation compute (generates snapshot)
  drop ues <count>          Drop/redrop UEs in simulation
                            Example: drop ues 50000 --layout=box

SNAPSHOT MANAGEMENT:
  snapshot list             List all saved measurement snapshots
                            Example: snapshot list --limit=50
  snapshot get <id>         View detailed snapshot metadata
                            Example: snapshot get 2025-11-06_15-30-22
  snapshot delete <id>      Delete a snapshot and its reports
                            Example: snapshot delete 2025-11-06_15-30-22

CONFIGURATION MANAGEMENT:
  config save <name>        Save current simulation state
                            Example: config save baseline
  config load <name>        Restore saved configuration
                            Example: config load baseline
  config list               List all saved configurations
  config delete <name>      Delete a saved configuration

OTHER:
  help                      Show this help message
  clear                     Clear output display

EXAMPLES:
  cns connect sim           Connect to simulation
  cns status                Show current status
  cns init                  Initialize simulation (interactive)
  cns query cells --band=H  Query high-band cells
  cns update cell 0 --tilt=12.0  Update cell tilt
  cns sim compute --name="baseline"  Run simulation and create snapshot
  cns snapshot list         View all stored measurement snapshots
  cns config save test1     Save current configuration as "test1"
  
For detailed command help: cns <command> --help

NOTE:
  • Snapshots = Measurement data from compute runs (read-only)
  • Configs = Simulation configurations you can restore (save/load network state)
"""
    return CommandResponse(
        content=content,
        response_type=ResponseType.INFO
    )


@command(
    name="connect",
    description="Connect to a network",
    usage="cns connect <network>",
    examples=["cns connect sim"],
    arguments=[
        CommandArgument("network", ArgumentType.STRING, required=True, 
                       help_text="Network name to connect to")
    ],
    response_type=ResponseType.SUCCESS,
    category="Connection",
    requires_connection=False
)
async def cmd_connect(args: Dict[str, Any]) -> CommandResponse:
    """Connect to a network"""
    
    network_name = args.get("network")
    
    if not network_name:
        return CommandResponse(
            content="Error: Network name required\n\nAvailable networks:\n" + \
                   "\n".join([f"  • {name}" for name in CONFIG["networks"].keys()]),
            response_type=ResponseType.ERROR
        )
    
    if network_name not in CONFIG["networks"]:
        return CommandResponse(
            content=f"Error: Unknown network '{network_name}'\n\nAvailable networks:\n" + \
                   "\n".join([f"  • {name}" for name in CONFIG["networks"].keys()]),
            response_type=ResponseType.ERROR
        )
    
    network_config = CONFIG["networks"][network_name]
    
    if not network_config.get("enabled", True):
        return CommandResponse(
            content=f"Error: Network '{network_name}' is disabled in configuration",
            response_type=ResponseType.ERROR
        )
    
    session.connected_network = network_name
    
    content = f"""Connected to: {network_config['name']}

  Type:        {network_config.get('type', 'unknown')}
  API URL:     {network_config['api_url']}
  Description: {network_config.get('description', 'N/A')}

You can now run commands in the context of this network.
Try 'cns status' to check the connection.
"""
    return CommandResponse(
        content=content,
        response_type=ResponseType.SUCCESS
    )


@command(
    name="networks",
    description="List all available networks",
    usage="cns networks",
    examples=["cns networks"],
    response_type=ResponseType.TEXT,
    category="Connection",
    requires_connection=False
)
async def cmd_networks(args: Dict[str, Any]) -> CommandResponse:
    """List available networks"""
    
    output = "Available Networks:\n\n"
    
    for name, config in CONFIG["networks"].items():
        status = "●" if name == session.connected_network else "○"
        enabled = "✓" if config.get("enabled", True) else "✗"
        output += f"  {status} {name:<12} {enabled} {config['name']}\n"
        output += f"     Type: {config.get('type', 'unknown'):<12} URL: {config['api_url']}\n\n"
    
    output += f"\nCurrent connection: {session.connected_network}\n"
    output += "Use 'cns connect <network>' to switch networks"
    
    return CommandResponse(
        content=output,
        response_type=ResponseType.TEXT
    )


@command(
    name="status",
    description="Check network connection status",
    usage="cns status",
    examples=["cns status"],
    response_type=ResponseType.SUCCESS,
    category="Connection"
)
async def cmd_status(args: Dict[str, Any]) -> CommandResponse:
    """Get status of connected network"""
    
    network_config = session.get_network_config()
    
    try:
        # Query the API status endpoint
        status_data = await api_request("GET", "/status")
        
        content = f"""Connected to: {network_config['name']}
Network Status:
  Type:             {network_config.get('type', 'unknown')}
  API URL:          {network_config['api_url']}
  Status:           ONLINE

Simulation Status:
  Sites:            {status_data.get('num_sites', 0)}
  Cells:            {status_data.get('num_cells', 0)}
  UEs:              {status_data.get('num_ues', 0)}
  Bands:            {', '.join(status_data.get('bands', [])) or 'None'}
  Cells Chunk:      {status_data.get('cells_chunk', 'N/A')}
  UE Chunk:         {status_data.get('ue_chunk', 'N/A')}
  
All systems operational
"""
        return CommandResponse(
            content=content,
            response_type=ResponseType.SUCCESS
        )
        
    except Exception as e:
        content = f"""Connection Failed: {network_config['name']}

  API URL:  {network_config['api_url']}
  Error:    {str(e)}

Troubleshooting:
  1. Check if the simulation API is running
  2. Verify the API URL in config.yaml
  3. Ensure Docker network connectivity (if using Docker)
"""
        return CommandResponse(
            content=content,
            response_type=ResponseType.ERROR
        )
