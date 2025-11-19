"""
Command handlers for CNS CLI Backend
"""
from commands.connection import cmd_connect, cmd_networks, cmd_status, cmd_help
from commands.initialization import cmd_init_interactive, process_init_wizard_input
from commands.query import cmd_query_cells, cmd_query_sites, cmd_query_ues
from commands.update import cmd_update_cell, cmd_update_cells_query
from commands.simulation import cmd_compute, cmd_drop_ues, cmd_snapshot_list, cmd_snapshot_get, cmd_snapshot_delete
from commands.config_management import (
    cmd_config_save, 
    cmd_config_load, 
    cmd_config_list, 
    cmd_config_delete
)

__all__ = [
    # Connection commands
    'cmd_help',
    'cmd_connect',
    'cmd_networks',
    'cmd_status',
    # Initialization commands
    'cmd_init_interactive',
    'process_init_wizard_input',
    # Query commands
    'cmd_query_cells',
    'cmd_query_sites',
    'cmd_query_ues',
    # Update commands
    'cmd_update_cell',
    'cmd_update_cells_query',
    # Simulation commands
    'cmd_compute',
    'cmd_drop_ues',
    'cmd_snapshot_list',
    'cmd_snapshot_get',
    'cmd_snapshot_delete',
    # Config management commands
    'cmd_config_save',
    'cmd_config_load',
    'cmd_config_list',
    'cmd_config_delete',
]
