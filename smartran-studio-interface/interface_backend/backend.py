#!/usr/bin/env python3
"""
CNS CLI Backend API - Main application entry point (Framework version)

This is the main FastAPI application that provides CLI commands
for interacting with CNS networks (simulation and live).
"""
import uvicorn
import json
import inspect
from typing import Dict, Any
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import models and dependencies
from models import CommandRequest, APICommandResponse
from session import session

# Import framework
from framework import registry, CommandResponse, ResponseType, FrameworkArgumentParser, CommandError, TableData

# Import all command modules to trigger @command decorators
import commands.connection
import commands.query
import commands.update
import commands.simulation
import commands.config_management
import commands.site_management

# Import init wizard separately (special case - interactive mode)
from commands.initialization import process_init_wizard_input, cmd_init_interactive


# ========== FastAPI App Setup ==========

app = FastAPI(
    title="CNS CLI Backend API",
    version="2.0.0 (Framework)",
    description="Backend API for CNS CLI commands with framework support"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== Helper Functions ==========

def convert_response(response: CommandResponse) -> APICommandResponse:
    """Convert framework CommandResponse to API response format"""
    
    # Handle different response types
    if response.response_type == ResponseType.TABLE:
        # TableData needs to be serialized
        if isinstance(response.content, TableData):
            # Send structured table data to frontend
            data = {
                "response_type": response.response_type.value,
                "table_data": {
                    "headers": response.content.headers,
                    "rows": response.content.rows,
                    "title": response.content.title,
                    "footer": response.content.footer
                }
            }
            # For result, send the structured data as JSON string
            result = json.dumps(response.content.dict())
        else:
            result = str(response.content)
            data = {"response_type": response.response_type.value}
    else:
        # All other types - send content as string
        result = str(response.content)
        data = {"response_type": response.response_type.value}
    
    # Add header/footer if present
    if response.header:
        result = response.header + "\n\n" + result
    if response.footer:
        result = result + "\n\n" + response.footer
    
    return APICommandResponse(
        result=result,
        exit_code=response.exit_code,
        data=data
    )


# ========== API Endpoints ==========

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "CNS CLI Backend API is running (Framework v2.0)"}


@app.get("/map/cells")
async def get_map_cells():
    """
    Get cell data formatted for map visualization
    Returns cells with position, azimuth, and metadata
    """
    try:
        from api_client import api_request
        
        # Get all cells from Sionna API
        result = await api_request("GET", "/cells")
        cells = result.get("cells", [])
        
        # Format for map visualization
        map_cells = []
        for cell in cells:
            map_cells.append({
                "cell_idx": cell.get("cell_idx"),
                "cell_name": cell.get("cell_name"),
                "site_name": cell.get("site_name"),
                "band": cell.get("band"),
                "x": cell.get("x", 0),
                "y": cell.get("y", 0),
                "azimuth": cell.get("sector_az_deg", 0),
                "tilt": cell.get("tilt_deg", 0),
                "frequency": cell.get("fc_MHz", 0),
                "antenna_rows": cell.get("bs_rows", 0),
                "antenna_cols": cell.get("bs_cols", 0),
                "antenna_pattern": cell.get("antenna_pattern", "N/A")
            })
        
        return {
            "cells": map_cells,
            "count": len(map_cells),
            "coordinate_system": "cartesian",
            "origin": [0, 0]
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "cells": [],
            "count": 0
        }


@app.post("/command")
async def execute_command(req: CommandRequest) -> APICommandResponse:
    """
    Framework-based command handler
    Uses command registry to route and execute commands
    """
    command = req.command.strip()
    
    # Handle init wizard mode FIRST (special case - not in registry)
    # In wizard mode, empty commands are valid (they mean "use default")
    if session.init_mode:
        result = await process_init_wizard_input(command)
        return APICommandResponse(result=result, exit_code=0)
    
    parts = command.split()
    
    if not parts:
        return APICommandResponse(result="No command provided", exit_code=1)
    
    # Remove 'cns' prefix if present
    if parts[0].lower() == "cns":
        parts = parts[1:]
    
    if not parts:
        return APICommandResponse(result="No command provided", exit_code=1)
    
    cmd = parts[0].lower()
    args = parts[1:]
    
    # Special case: clear command
    if cmd == "clear":
        return APICommandResponse(result="[CLEAR_SCREEN]", exit_code=0)
    
    try:
        # Build command name (handle multi-word commands)
        full_cmd = cmd
        remaining_args = args[:]
        
        # Try progressively longer command names
        if args:
            # Try three-word first (e.g. "update cells query")
            if len(args) >= 2:
                potential_three = f"{cmd} {args[0]} {args[1]}"
                if registry.get_command(potential_three):
                    full_cmd = potential_three
                    remaining_args = args[2:]
                # Also try with underscores
                elif registry.get_command(potential_three.replace(" ", "_")):
                    full_cmd = potential_three.replace(" ", "_")
                    remaining_args = args[2:]
            
            # Try two-word (e.g. "query cells", "config save")
            if full_cmd == cmd and len(args) >= 1:
                potential_two = f"{cmd} {args[0]}"
                if registry.get_command(potential_two):
                    full_cmd = potential_two
                    remaining_args = args[1:]
                # Also try with underscores
                elif registry.get_command(potential_two.replace(" ", "_")):
                    full_cmd = potential_two.replace(" ", "_")
                    remaining_args = args[1:]
        
        # Get command from registry
        command_entry = registry.get_command(full_cmd)
        
        if command_entry:
            # Framework command - execute it
            handler = command_entry['handler']
            metadata = command_entry['metadata']
            
            # Check if handler expects parsed dict or raw list
            # Query commands (old style) expect Dict[str, Any]
            # New commands expect List[str]
            sig = inspect.signature(handler)
            params = list(sig.parameters.values())
            
            if params and params[0].annotation == Dict[str, Any]:
                # Old style - parse args first
                parsed_args = FrameworkArgumentParser.parse(remaining_args, metadata.arguments)
                response = await handler(parsed_args)
            else:
                # New style - pass raw args, handler will parse
                response = await handler(remaining_args)
            
            # Convert to API response
            return convert_response(response)
        
        # Special case: init command (interactive wizard)
        if cmd == "init":
            response = await cmd_init_interactive(args)
            # If it returns a CommandResponse, convert it
            if isinstance(response, CommandResponse):
                return convert_response(response)
            # Otherwise return as plain string (for wizard prompts)
            return APICommandResponse(result=response, exit_code=0)
        
        # Unknown command
        result = f"""❌ Unknown command: {cmd}

Try 'cns help' to see available commands.

Common commands:
  connect, status, help, query, update, compute, config
"""
        return APICommandResponse(result=result, exit_code=1)
    
    except CommandError as e:
        error_text = f"❌ Error: {e.message}\n"
        if e.suggestions:
            error_text += "\nSuggestions:\n"
            for suggestion in e.suggestions:
                error_text += f"  • {suggestion}\n"
        return APICommandResponse(result=error_text, exit_code=1)
    
    except Exception as e:
        return APICommandResponse(
            result=f"❌ Command failed: {str(e)}",
            exit_code=1
        )


# ========== Server Startup ==========

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Starting CNS CLI Backend API (Framework v2.0)")
    print("=" * 60)
    print("\nServer running at: http://localhost:8001")
    print("API docs at: http://localhost:8001/docs")
    print("\nPress CTRL+C to stop\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
