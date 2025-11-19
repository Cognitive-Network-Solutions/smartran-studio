"""
Cell Query Module for CNS Sionna Simulation

Provides flexible querying capabilities for cells with wildcard support,
range filters, and complex criteria matching.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import re


class CellQuery(BaseModel):
    """
    Query model for filtering cells with flexible criteria.
    
    All fields are optional. Empty query returns all cells.
    Supports wildcards (*) in name fields.
    """
    
    # Name patterns (supports wildcards with *)
    cell_name: Optional[str] = Field(None, description="Cell name (supports * wildcard)")
    site_name: Optional[str] = Field(None, description="Site name (supports * wildcard)")
    
    # Exact matches
    band: Optional[str] = Field(None, description="Band identifier (e.g., 'H', 'L')")
    sector_id: Optional[int] = Field(None, ge=0, le=2, description="Sector ID (0, 1, or 2)")
    site_idx: Optional[int] = Field(None, ge=0, description="Site index")
    
    # Antenna configuration
    bs_rows: Optional[int] = Field(None, ge=1, description="Number of antenna rows")
    bs_cols: Optional[int] = Field(None, ge=1, description="Number of antenna columns")
    bs_pol: Optional[str] = Field(None, description="Polarization type (e.g., 'dual', 'single')")
    antenna_pattern: Optional[str] = Field(None, description="Antenna pattern (e.g., '38.901')")
    
    # Frequency filters (GHz)
    fc_ghz_min: Optional[float] = Field(None, ge=0, description="Minimum frequency in GHz")
    fc_ghz_max: Optional[float] = Field(None, ge=0, description="Maximum frequency in GHz")
    fc_ghz: Optional[float] = Field(None, ge=0, description="Exact frequency in GHz")
    
    # Tilt filters (degrees)
    tilt_min: Optional[float] = Field(None, description="Minimum tilt in degrees")
    tilt_max: Optional[float] = Field(None, description="Maximum tilt in degrees")
    tilt_deg: Optional[float] = Field(None, description="Exact tilt in degrees")
    
    # Power filters (dBm)
    power_min: Optional[float] = Field(None, description="Minimum TX power in dBm")
    power_max: Optional[float] = Field(None, description="Maximum TX power in dBm")
    
    # Pagination
    limit: Optional[int] = Field(None, ge=1, description="Maximum number of results to return")
    offset: int = Field(0, ge=0, description="Number of results to skip")
    
    # Sorting
    sort_by: Optional[str] = Field(None, description="Field to sort by (e.g., 'cell_name', 'fc_GHz', 'tilt_deg')")
    sort_desc: bool = Field(False, description="Sort in descending order")
    
    class Config:
        schema_extra = {
            "examples": [
                {
                    "band": "H",
                    "tilt_min": 10
                },
                {
                    "site_name": "SITE000*",
                    "sector_id": 0
                },
                {
                    "bs_rows": 8,
                    "bs_cols": 1,
                    "fc_ghz_min": 2.0,
                    "fc_ghz_max": 3.0
                }
            ]
        }


def matches_pattern(value: str, pattern: str) -> bool:
    """
    Check if value matches pattern with wildcard (*) support.
    
    Args:
        value: String to check
        pattern: Pattern with optional * wildcards
        
    Returns:
        True if value matches pattern
        
    Examples:
        matches_pattern("SITE0001A", "SITE*") -> True
        matches_pattern("SITE0001A", "SITE000*") -> True
        matches_pattern("SITE0001A", "SITE0001A") -> True
        matches_pattern("SITE0001A", "ABC*") -> False
    """
    if '*' not in pattern:
        return value == pattern
    
    # Convert wildcard pattern to regex
    regex = '^' + pattern.replace('*', '.*') + '$'
    return re.match(regex, value) is not None


def matches_query_criteria(cell: Dict[str, Any], query: CellQuery) -> bool:
    """
    Check if a cell matches all query criteria.
    
    Args:
        cell: Cell dictionary from sim.cells_table()
        query: CellQuery object with filter criteria
        
    Returns:
        True if cell matches all specified criteria
    """
    # Name patterns with wildcard support
    if query.cell_name and not matches_pattern(cell['cell_name'], query.cell_name):
        return False
    if query.site_name and not matches_pattern(cell['site_name'], query.site_name):
        return False
    
    # Exact matches
    if query.band and cell['band'] != query.band:
        return False
    if query.sector_id is not None and cell['sector_id'] != query.sector_id:
        return False
    if query.site_idx is not None and cell['site_idx'] != query.site_idx:
        return False
    
    # Antenna configuration
    if query.bs_rows is not None and cell['bs_rows'] != query.bs_rows:
        return False
    if query.bs_cols is not None and cell['bs_cols'] != query.bs_cols:
        return False
    if query.bs_pol and cell['bs_pol'] != query.bs_pol:
        return False
    if query.antenna_pattern and cell['antenna_pattern'] != query.antenna_pattern:
        return False
    
    # Frequency filters
    if query.fc_ghz is not None and abs(cell['fc_GHz'] - query.fc_ghz) > 0.001:
        return False
    if query.fc_ghz_min is not None and cell['fc_GHz'] < query.fc_ghz_min:
        return False
    if query.fc_ghz_max is not None and cell['fc_GHz'] > query.fc_ghz_max:
        return False
    
    # Tilt filters
    if query.tilt_deg is not None:
        if cell['tilt_deg'] is None or abs(cell['tilt_deg'] - query.tilt_deg) > 0.001:
            return False
    if query.tilt_min is not None:
        if cell['tilt_deg'] is None or cell['tilt_deg'] < query.tilt_min:
            return False
    if query.tilt_max is not None:
        if cell['tilt_deg'] is None or cell['tilt_deg'] > query.tilt_max:
            return False
    
    # Power filters
    if query.power_min is not None and cell['tx_rs_power_dbm'] < query.power_min:
        return False
    if query.power_max is not None and cell['tx_rs_power_dbm'] > query.power_max:
        return False
    
    return True


def query_cells(sim, query: CellQuery) -> Dict[str, Any]:
    """
    Query cells from simulation with flexible filtering.
    
    Args:
        sim: MultiCellSim instance
        query: CellQuery object with filter criteria
        
    Returns:
        Dictionary with:
            - cells: List of matching cell dictionaries
            - num_results: Number of cells returned (after pagination)
            - total_matches: Total number of matching cells (before pagination)
            - offset: Offset used
            - limit: Limit used
            - query: Query criteria used (excluding None values)
            
    Example:
        >>> query = CellQuery(band="H", tilt_min=10)
        >>> result = query_cells(sim, query)
        >>> print(f"Found {result['total_matches']} cells")
        >>> for cell in result['cells']:
        ...     print(cell['cell_name'], cell['tilt_deg'])
    """
    # Get all cells
    all_cells = sim.cells_table()
    
    # Apply filters
    filtered_cells = [
        cell for cell in all_cells 
        if matches_query_criteria(cell, query)
    ]
    
    # Sort if requested
    if query.sort_by and filtered_cells:
        # Check if sort field exists
        if query.sort_by in filtered_cells[0]:
            try:
                # Handle None values in sorting
                filtered_cells.sort(
                    key=lambda c: (c[query.sort_by] is None, c[query.sort_by]),
                    reverse=query.sort_desc
                )
            except (TypeError, KeyError):
                # If sorting fails, just skip it
                pass
    
    # Count total matches before pagination
    total_matches = len(filtered_cells)
    
    # Apply pagination
    if query.limit:
        filtered_cells = filtered_cells[query.offset:query.offset + query.limit]
    elif query.offset > 0:
        filtered_cells = filtered_cells[query.offset:]
    
    return {
        "cells": filtered_cells,
        "num_results": len(filtered_cells),
        "total_matches": total_matches,
        "offset": query.offset,
        "limit": query.limit,
        "query": query.dict(exclude_none=True),
    }

