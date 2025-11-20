"""
Simulation initialization commands and interactive wizard
"""
import json
import sys
from pathlib import Path
from typing import List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from session import session
from api_client import api_request
from arango_client import get_state_manager
from framework import CommandResponse, ResponseType


# Define initialization wizard steps - REAL DEFAULTS from sim_initialization.py
INIT_WIZARD_STEPS = [
    {
        "param": "n_sites",
        "prompt": "Number of sites",
        "default": 10,
        "type": "int",
        "description": "Number of cell sites to create"
    },
    {
        "param": "spacing",
        "prompt": "Site spacing (meters)",
        "default": 500.0,
        "type": "float",
        "description": "Target inter-site spacing in meters"
    },
    {
        "param": "seed",
        "prompt": "Random seed",
        "default": 7,
        "type": "int",
        "description": "Random seed for site placement and UE drop"
    },
    {
        "param": "site_height_m",
        "prompt": "Site height (meters)",
        "default": 20.0,
        "type": "float",
        "description": "Height of cell sites in meters"
    },
    {
        "param": "fc_hi_hz",
        "prompt": "High band frequency (Hz)",
        "default": 2500e6,
        "type": "float",
        "description": "High band carrier frequency (e.g., 2500e6 for 2.5 GHz)"
    },
    {
        "param": "tilt_hi_deg",
        "prompt": "High band tilt (degrees)",
        "default": 9.0,
        "type": "float",
        "description": "Antenna tilt angle for high band"
    },
    {
        "param": "bs_rows_hi",
        "prompt": "High band antenna rows",
        "default": 8,
        "type": "int",
        "description": "Number of antenna array rows for high band"
    },
    {
        "param": "bs_cols_hi",
        "prompt": "High band antenna columns",
        "default": 1,
        "type": "int",
        "description": "Number of antenna array columns for high band"
    },
    {
        "param": "fc_lo_hz",
        "prompt": "Low band frequency (Hz)",
        "default": 600e6,
        "type": "float",
        "description": "Low band carrier frequency (e.g., 600e6 for 600 MHz)"
    },
    {
        "param": "tilt_lo_deg",
        "prompt": "Low band tilt (degrees)",
        "default": 9.0,
        "type": "float",
        "description": "Antenna tilt angle for low band"
    },
    {
        "param": "bs_rows_lo",
        "prompt": "Low band antenna rows",
        "default": 8,
        "type": "int",
        "description": "Number of antenna array rows for low band"
    },
    {
        "param": "bs_cols_lo",
        "prompt": "Low band antenna columns",
        "default": 1,
        "type": "int",
        "description": "Number of antenna array columns for low band"
    },
    {
        "param": "num_ue",
        "prompt": "Number of UEs",
        "default": 30000,
        "type": "int",
        "description": "Number of user equipment to simulate"
    },
    {
        "param": "box_pad_m",
        "prompt": "UE box padding (meters)",
        "default": 250.0,
        "type": "float",
        "description": "Padding around sites for UE drop area"
    }
]


async def cmd_init_interactive(args: List[str]) -> str:
    """Initialize simulation with interactive prompts or JSON config"""
    
    # Check for --help
    if args and args[0] in ['--help', '-h']:
        return """Initialize the simulation

Usage: 
  init                 Start interactive wizard (step-by-step prompts)
  init --default       Initialize with all default values
  init --config <json> Initialize with JSON configuration

Interactive Wizard Mode:
  Walks you through each configuration parameter with defaults shown.
  Press Enter to accept defaults, or type a value to customize.
  
  Parameters configured (15 steps):
    1. Number of sites (default: 10)
    2. Site spacing in meters (default: 500.0)
    3. Random seed (default: 7)
    4. Site height in meters (default: 20.0)
    5. High band frequency in Hz (default: 2500e6)
    6. Low band frequency in Hz (default: 600e6)
    7. High band TX power in dBm (default: 3.0)
    8. Low band TX power in dBm (default: 3.0)
    9. High band downtilt angle (default: 9.0)
    10. Low band downtilt angle (default: 9.0)
    11. High band antenna rows (default: 8)
    12. High band antenna cols (default: 1)
    13. Low band antenna rows (default: 8)
    14. Low band antenna cols (default: 1)
    15. Number of UEs to drop (default: 50000)

Flags:
  --default              Use all default values (quick start)
  --config <json>        Provide JSON configuration directly
  
Examples:
  srs init                                    # Interactive wizard
  srs init --default                          # Quick start with defaults
  srs init --config '{"n_sites": 20}'        # Custom config
  
Output:
  - Number of sites, cells, and UEs created
  - Full configuration used
  - Success message

See also: srs status (check simulation state after init)
"""
    
    # Check if --default flag (initialize with all defaults)
    if args and args[0] == "--default":
        try:
            # Empty config = use all defaults
            config_data = {}
            
            # Send to API
            result = await api_request("POST", "/initialize", data=config_data)
            
            # Save init config to ArangoDB session cache
            state_mgr = get_state_manager()
            if state_mgr:
                try:
                    # Save the actual config used (from result)
                    actual_config = result.get('config', {})
                    state_mgr.save_init_config(actual_config)
                except Exception as e:
                    print(f"Warning: Could not save init config to ArangoDB: {e}")
            
            config = result.get('config', {})
            
            # Format configuration nicely (not as JSON dump)
            high_band = config.get('high_band', {})
            low_band = config.get('low_band', {})
            ues = config.get('ues', {})
            chunking = config.get('chunking', {})
            
            return CommandResponse(
                content=f"""✓ Simulation Initialized with ALL DEFAULTS

Network Configuration:
  Sites:            {result.get('num_sites', 0)}
  Cells:            {result.get('num_cells', 0)}
  High Band Cells:  {result.get('high_band_cells', 0)}
  Low Band Cells:   {result.get('low_band_cells', 0)}
  UEs:              {result.get('num_ues', 0):,}

Site Layout:
  Spacing:          {config.get('spacing_m', 0)} m
  Height:           {config.get('site_height_m', 0)} m
  Seed:             {config.get('seed', 0)}

High Band:
  Frequency:        {high_band.get('fc_ghz', 0)} GHz
  Tilt:             {high_band.get('tilt_deg', 0)}°
  Antenna:          {high_band.get('antenna', 'N/A')}
  Pattern:          {high_band.get('pattern', 'N/A')}

Low Band:
  Frequency:        {low_band.get('fc_ghz', 0)} GHz
  Tilt:             {low_band.get('tilt_deg', 0)}°
  Antenna:          {low_band.get('antenna', 'N/A')}
  Pattern:          {low_band.get('pattern', 'N/A')}

UE Configuration:
  Count:            {ues.get('num_ue', 0):,}
  Box Padding:      {ues.get('box_pad_m', 0)} m

Processing:
  Cells Chunk:      {chunking.get('cells_chunk', 0)}
  UE Chunk:         {chunking.get('ue_chunk', 0)}

Simulation ready! Try 'sim compute' to run your first calculation.
Use 'config save <name>' to save this configuration.
""",
                response_type=ResponseType.SUCCESS
            )
        except Exception as e:
            return CommandResponse(
                content=f"Initialization failed: {str(e)}",
                response_type=ResponseType.ERROR
            )
    
    # Check if JSON config provided (direct init)
    if args and args[0] == "--config":
        if len(args) < 2:
            return CommandResponse(
                content="JSON config required after --config flag",
                response_type=ResponseType.ERROR
            )
        
        try:
            config_json_str = " ".join(args[1:])
            config_data = json.loads(config_json_str)
            
            # Send to API
            result = await api_request("POST", "/initialize", data=config_data)
            
            # Save init config to ArangoDB session cache
            state_mgr = get_state_manager()
            if state_mgr:
                try:
                    # Save the actual config used (from result)
                    actual_config = result.get('config', {})
                    state_mgr.save_init_config(actual_config)
                except Exception as e:
                    print(f"Warning: Could not save init config to ArangoDB: {e}")
            
            config = result.get('config', {})
            
            # Format configuration nicely (not as JSON dump)
            high_band = config.get('high_band', {})
            low_band = config.get('low_band', {})
            ues = config.get('ues', {})
            chunking = config.get('chunking', {})
            
            return CommandResponse(
                content=f"""✓ Simulation Initialized

Network Configuration:
  Sites:            {result.get('num_sites', 0)}
  Cells:            {result.get('num_cells', 0)}
  High Band Cells:  {result.get('high_band_cells', 0)}
  Low Band Cells:   {result.get('low_band_cells', 0)}
  UEs:              {result.get('num_ues', 0):,}

Site Layout:
  Spacing:          {config.get('spacing_m', 0)} m
  Height:           {config.get('site_height_m', 0)} m
  Seed:             {config.get('seed', 0)}

High Band:
  Frequency:        {high_band.get('fc_ghz', 0)} GHz
  Tilt:             {high_band.get('tilt_deg', 0)}°
  Antenna:          {high_band.get('antenna', 'N/A')}
  Pattern:          {high_band.get('pattern', 'N/A')}

Low Band:
  Frequency:        {low_band.get('fc_ghz', 0)} GHz
  Tilt:             {low_band.get('tilt_deg', 0)}°
  Antenna:          {low_band.get('antenna', 'N/A')}
  Pattern:          {low_band.get('pattern', 'N/A')}

UE Configuration:
  Count:            {ues.get('num_ue', 0):,}
  Box Padding:      {ues.get('box_pad_m', 0)} m

Processing:
  Cells Chunk:      {chunking.get('cells_chunk', 0)}
  UE Chunk:         {chunking.get('ue_chunk', 0)}

Simulation ready! Try 'sim compute' to run your first calculation.
Use 'config save <name>' to save this configuration.
""",
                response_type=ResponseType.SUCCESS
            )
        except json.JSONDecodeError as e:
            return CommandResponse(
                content=f"Invalid JSON config: {str(e)}",
                response_type=ResponseType.ERROR
            )
        except Exception as e:
            return CommandResponse(
                content=f"Initialization failed: {str(e)}",
                response_type=ResponseType.ERROR
            )
    
    # Start interactive wizard
    session.start_init_wizard()
    return get_init_wizard_prompt()


def get_init_wizard_prompt() -> str:
    """Get the current prompt for the init wizard"""
    step = session.init_step
    
    if step >= len(INIT_WIZARD_STEPS):
        # Shouldn't happen, but safety check
        return "❌ Error: Wizard step out of range"
    
    current = INIT_WIZARD_STEPS[step]
    
    # Calculate progress bar
    progress_pct = int((step / len(INIT_WIZARD_STEPS)) * 100)
    bar_width = 40
    filled = int((progress_pct / 100) * bar_width)
    bar = "█" * filled + "░" * (bar_width - filled)
    
    return f"""╔════════════════════════════════════════════════════════════════════════════════╗
║                 SMARTRAN STUDIO INITIALIZATION WIZARD                          ║
╠════════════════════════════════════════════════════════════════════════════════╣
║                                                                                ║
║  Progress: [{bar}] {progress_pct}%   Step {step + 1}/{len(INIT_WIZARD_STEPS)}
║                                                                                ║
║  {current['description']:<78}║
║                                                                                ║
║  {current['prompt']}:
║  Default: {current['default']}
║                                                                                ║
║  Press Enter to use default, or type a value to customize                     ║
║  Type 'cancel' to abort                                                       ║
║                                                                                ║
╚════════════════════════════════════════════════════════════════════════════════╝

→ """


async def process_init_wizard_input(user_input: str) -> str:
    """Process user input for the init wizard"""
    user_input = user_input.strip()
    
    # Check for cancel or exit
    if user_input.lower() in ['cancel', 'exit', 'quit']:
        session.end_init_wizard()
        return "❌ Initialization cancelled\n\nYou can now run normal commands."
    
    # Detect if user is trying to run a command
    if user_input.lower().startswith(('help', 'status', 'query', 'update', 'drop', 'compute', 'networks', 'connect')):
        return f"⚠️  You're currently in the initialization wizard.\n\n" \
               f"Other commands are disabled during setup.\n" \
               f"Type 'cancel' to exit the wizard and run normal commands.\n\n" \
               + get_init_wizard_prompt()
    
    step = session.init_step
    current = INIT_WIZARD_STEPS[step]
    
    # Use default if empty
    if not user_input:
        value = current['default']
    else:
        # Parse value based on type
        try:
            if current['type'] == 'int':
                value = int(user_input)
            elif current['type'] == 'float':
                value = float(user_input)
            else:
                value = user_input
        except ValueError:
            return f"❌ Error: Invalid {current['type']} value. Please try again.\n\n" + get_init_wizard_prompt()
    
    # Store the value
    session.init_config[current['param']] = value
    
    # Move to next step
    session.init_step += 1
    
    # Check if we're done
    if session.init_step >= len(INIT_WIZARD_STEPS):
        # Execute initialization
        result = await finalize_init_wizard()
        return result
    
    # Show next prompt
    return get_init_wizard_prompt()


async def finalize_init_wizard() -> str:
    """Finalize and execute the initialization"""
    config_data = session.init_config.copy()
    session.end_init_wizard()
    
    try:
        # Send to API
        result = await api_request("POST", "/initialize", data=config_data)
        
        # Save init config to ArangoDB session cache
        state_mgr = get_state_manager()
        if state_mgr:
            try:
                state_mgr.save_init_config(config_data)
            except Exception as e:
                # Don't fail init if ArangoDB save fails
                print(f"Warning: Could not save init config to ArangoDB: {e}")
        
        return f"""✓ Simulation Initialized Successfully!

  Sites:            {result.get('num_sites', 0)}
  Cells:            {result.get('num_cells', 0)}
  High Band Cells:  {result.get('high_band_cells', 0)}
  Low Band Cells:   {result.get('low_band_cells', 0)}
  UEs:              {result.get('num_ues', 0)}

Configuration Applied:
{json.dumps(config_data, indent=2)}

✓ Simulation ready! 

Next steps:
  • Run 'status' to verify
  • Run 'query cells' to see cells
  • Run 'compute' to generate RSRP data
  • Run 'config save <name>' to save this configuration
"""
    except Exception as e:
        return f"❌ Error: Initialization failed: {str(e)}\n\nConfiguration attempted:\n{json.dumps(config_data, indent=2)}"


        
        # Save init config to ArangoDB session cache
        state_mgr = get_state_manager()
        if state_mgr:
            try:
                state_mgr.save_init_config(config_data)
            except Exception as e:
                # Don't fail init if ArangoDB save fails
                print(f"Warning: Could not save init config to ArangoDB: {e}")
        
        return f"""✓ Simulation Initialized Successfully!

  Sites:            {result.get('num_sites', 0)}
  Cells:            {result.get('num_cells', 0)}
  High Band Cells:  {result.get('high_band_cells', 0)}
  Low Band Cells:   {result.get('low_band_cells', 0)}
  UEs:              {result.get('num_ues', 0)}

Configuration Applied:
{json.dumps(config_data, indent=2)}

✓ Simulation ready! 

Next steps:
  • Run 'status' to verify
  • Run 'query cells' to see cells
  • Run 'compute' to generate RSRP data
  • Run 'config save <name>' to save this configuration
"""
    except Exception as e:
        return f"❌ Error: Initialization failed: {str(e)}\n\nConfiguration attempted:\n{json.dumps(config_data, indent=2)}"

