"""
Cell Update Module for CNS Sionna Simulation

Provides flexible cell configuration updates with validation.
"""

from typing import Optional
from pydantic import BaseModel, Field, validator
import logging

logger = logging.getLogger(__name__)


class CellUpdateRequest(BaseModel):
    """
    Generic cell update request.
    
    Specify cell by either cell_id or cell_name (one required).
    All configuration fields are optional - only provided fields will be updated.
    """
    
    # Cell identifier (one required)
    cell_id: Optional[int] = Field(None, ge=0, description="Cell ID (index)")
    cell_name: Optional[str] = Field(None, description="Cell name (e.g., 'HSITE0001A1')")
    
    # NOTE: Identifier fields (site, sector_id, band, site_idx, etc.) are IMMUTABLE
    # and cannot be updated after cell creation
    
    # RF parameters
    fc_hz: Optional[float] = Field(None, gt=0, description="Carrier frequency in Hz")
    tx_rs_power_dbm: Optional[float] = Field(None, description="TX RS power in dBm")
    tilt_deg: Optional[float] = Field(None, description="Tilt angle in degrees")
    roll_deg: Optional[float] = Field(None, description="Roll angle in degrees")
    height_m: Optional[float] = Field(None, gt=0, description="Effective height in meters")
    
    # Antenna array configuration
    bs_rows: Optional[int] = Field(None, ge=1, description="Number of antenna rows")
    bs_cols: Optional[int] = Field(None, ge=1, description="Number of antenna columns")
    bs_pol: Optional[str] = Field(None, description="Polarization type (e.g., 'dual', 'single')")
    bs_pol_type: Optional[str] = Field(None, description="Polarization type detail (e.g., 'VH', 'V')")
    elem_v_spacing: Optional[float] = Field(None, gt=0, description="Vertical element spacing (wavelengths)")
    elem_h_spacing: Optional[float] = Field(None, gt=0, description="Horizontal element spacing (wavelengths)")
    antenna_pattern: Optional[str] = Field(None, description="Antenna pattern (e.g., '38.901')")
    
    # Control flags
    rename: bool = Field(True, description="Auto-rename cell after update")
    
    @validator('cell_name')
    def validate_cell_identifier(cls, v, values):
        """Ensure either cell_id or cell_name is provided"""
        if v is None and values.get('cell_id') is None:
            raise ValueError('Either cell_id or cell_name must be provided')
        return v
    
    @validator('bs_pol_type')
    def validate_pol_type(cls, v, values):
        """Validate polarization type matches polarization"""
        if v is not None and values.get('bs_pol') == 'single' and v != 'V':
            raise ValueError("bs_pol_type must be 'V' when bs_pol is 'single'")
        return v
    
    @validator('bs_cols')
    def validate_antenna_array(cls, v, values):
        """Validate bs_rows and bs_cols are updated together"""
        bs_rows = values.get('bs_rows')
        bs_cols = v
        
        # If one is provided, both must be provided
        if (bs_rows is not None and bs_cols is None):
            raise ValueError("bs_rows and bs_cols must be updated together. You provided bs_rows but not bs_cols.")
        if (bs_cols is not None and bs_rows is None):
            raise ValueError("bs_rows and bs_cols must be updated together. You provided bs_cols but not bs_rows.")
        
        return v
    
    class Config:
        schema_extra = {
            "examples": [
                {
                    "cell_id": 0,
                    "tilt_deg": 12.0
                },
                {
                    "cell_name": "HSITE0001A1",
                    "tilt_deg": 12.0,
                    "tx_rs_power_dbm": 5.0
                },
                {
                    "cell_id": 5,
                    "bs_rows": 8,
                    "bs_cols": 1,
                    "antenna_pattern": "38.901"
                },
                {
                    "cell_id": 10,
                    "bs_rows": 4,
                    "bs_cols": 2
                }
            ]
        }


def update_cell_config(sim, request: CellUpdateRequest) -> dict:
    """
    Update cell configuration with flexible parameters.
    
    Args:
        sim: MultiCellSim instance
        request: CellUpdateRequest with cell identifier and update fields
        
    Returns:
        Dictionary with:
            - cell_id: ID of updated cell
            - cell_name: Name of updated cell (after update)
            - updated_fields: List of fields that were updated
            - cell: Full updated cell configuration
            
    Raises:
        ValueError: If cell not found or validation fails
        
    Example:
        >>> request = CellUpdateRequest(cell_id=0, tilt_deg=12.0, tx_rs_power_dbm=5.0)
        >>> result = update_cell_config(sim, request)
        >>> print(f"Updated {result['cell_name']}: {result['updated_fields']}")
    """
    # Resolve cell ID
    if request.cell_id is not None:
        cell_id = request.cell_id
        if cell_id < 0 or cell_id >= len(sim.cells):
            raise ValueError(f"Invalid cell_id: {cell_id} (valid range: 0-{len(sim.cells)-1})")
    elif request.cell_name is not None:
        # Find cell by name
        cell_id = None
        for idx, cell in enumerate(sim.cells):
            if cell.get('name') == request.cell_name:
                cell_id = idx
                break
        if cell_id is None:
            raise ValueError(f"Cell not found: {request.cell_name}")
    else:
        raise ValueError("Either cell_id or cell_name must be provided")
    
    # Get original cell name for logging
    original_name = sim.cells[cell_id].get('name', f"Cell {cell_id}")
    
    # Build kwargs for update_cell() - only include non-None fields
    update_kwargs = {}
    updated_fields = []
    
    # Map request fields to update_cell() parameters
    # NOTE: Identifier fields (site, sector_id, band) are excluded - they're immutable
    field_map = {
        'fc_hz': 'fc_hz',
        'tx_rs_power_dbm': 'tx_rs_power_dbm',
        'tilt_deg': 'tilt_deg',
        'roll_deg': 'roll_deg',
        'height_m': 'height_m',
        'bs_rows': 'bs_rows',
        'bs_cols': 'bs_cols',
        'bs_pol': 'bs_pol',
        'bs_pol_type': 'bs_pol_type',
        'elem_v_spacing': 'elem_v_spacing',
        'elem_h_spacing': 'elem_h_spacing',
        'antenna_pattern': 'antenna_pattern',
        'rename': 'rename',
    }
    
    for request_field, sim_field in field_map.items():
        value = getattr(request, request_field)
        if value is not None:
            update_kwargs[sim_field] = value
            if request_field != 'rename':  # Don't count rename as an updated field
                updated_fields.append(request_field)
    
    # Validate that at least one field is being updated
    if not updated_fields:
        raise ValueError("No fields to update. Provide at least one configuration parameter.")
    
    # Perform the update
    logger.info(f"Updating cell {cell_id} ({original_name}): {updated_fields}")
    sim.update_cell(cell_id, **update_kwargs)
    
    # Get updated cell info
    updated_cell = sim.get_cell(cell_id)
    new_name = updated_cell['cell_name']
    
    logger.info(f"Successfully updated cell {cell_id}: {original_name} -> {new_name}")
    
    return {
        "cell_id": cell_id,
        "cell_name": new_name,
        "original_name": original_name,
        "updated_fields": updated_fields,
        "num_fields_updated": len(updated_fields),
        "cell": updated_cell,
    }


class BulkCellUpdateRequest(BaseModel):
    """
    Request to update multiple cells at once.
    
    All updates are applied sequentially. If any update fails, 
    previous updates are NOT rolled back.
    """
    updates: list[CellUpdateRequest] = Field(
        ..., 
        min_items=1,
        description="List of cell updates to apply"
    )
    stop_on_error: bool = Field(
        False, 
        description="Stop processing if an update fails"
    )
    
    class Config:
        schema_extra = {
            "examples": [
                {
                    "updates": [
                        {"cell_id": 0, "tilt_deg": 12.0},
                        {"cell_id": 1, "tilt_deg": 12.0},
                        {"cell_id": 2, "tilt_deg": 12.0}
                    ],
                    "stop_on_error": True
                }
            ]
        }


def update_cells_bulk(sim, request: BulkCellUpdateRequest) -> dict:
    """
    Update multiple cells in bulk.
    
    Args:
        sim: MultiCellSim instance
        request: BulkCellUpdateRequest with list of updates
        
    Returns:
        Dictionary with:
            - num_requested: Number of updates requested
            - num_successful: Number of successful updates
            - num_failed: Number of failed updates
            - results: List of results for each update
            - errors: List of errors (if any)
    """
    results = []
    errors = []
    
    for idx, update_req in enumerate(request.updates):
        try:
            result = update_cell_config(sim, update_req)
            results.append({
                "index": idx,
                "status": "success",
                "cell_id": result["cell_id"],
                "cell_name": result["cell_name"],
                "updated_fields": result["updated_fields"],
            })
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Bulk update failed for item {idx}: {error_msg}")
            errors.append({
                "index": idx,
                "error": error_msg,
                "request": update_req.dict(exclude_none=True)
            })
            results.append({
                "index": idx,
                "status": "failed",
                "error": error_msg,
            })
            
            if request.stop_on_error:
                logger.warning(f"Stopping bulk update after error at index {idx}")
                break
    
    num_successful = sum(1 for r in results if r.get("status") == "success")
    num_failed = len(errors)
    
    return {
        "num_requested": len(request.updates),
        "num_successful": num_successful,
        "num_failed": num_failed,
        "results": results,
        "errors": errors if errors else None,
    }


class QueryBasedUpdateRequest(BaseModel):
    """
    Update cells matching query criteria with the same values.
    
    Combines query + bulk update in one operation.
    First queries for matching cells, then applies the same update to all.
    """
    
    # Query criteria (from cell_query.CellQuery)
    # Note: We can't import CellQuery here to avoid circular imports,
    # so we define the query fields inline
    
    # Query - Name patterns (supports wildcards with *)
    cell_name: Optional[str] = Field(None, description="Cell name pattern (supports * wildcard)")
    site_name: Optional[str] = Field(None, description="Site name pattern (supports * wildcard)")
    
    # Query - Exact matches
    band: Optional[str] = Field(None, description="Band identifier")
    sector_id: Optional[int] = Field(None, ge=0, le=2, description="Sector ID")
    site_idx: Optional[int] = Field(None, ge=0, description="Site index")
    
    # Query - Antenna configuration
    query_bs_rows: Optional[int] = Field(None, ge=1, description="Query: Number of antenna rows")
    query_bs_cols: Optional[int] = Field(None, ge=1, description="Query: Number of antenna columns")
    query_bs_pol: Optional[str] = Field(None, description="Query: Polarization type")
    query_antenna_pattern: Optional[str] = Field(None, description="Query: Antenna pattern")
    
    # Query - Frequency filters (GHz)
    fc_ghz_min: Optional[float] = Field(None, ge=0, description="Query: Min frequency in GHz")
    fc_ghz_max: Optional[float] = Field(None, ge=0, description="Query: Max frequency in GHz")
    fc_ghz: Optional[float] = Field(None, ge=0, description="Query: Exact frequency in GHz")
    
    # Query - Tilt filters
    tilt_min: Optional[float] = Field(None, description="Query: Min tilt in degrees")
    tilt_max: Optional[float] = Field(None, description="Query: Max tilt in degrees")
    query_tilt_deg: Optional[float] = Field(None, description="Query: Exact tilt in degrees")
    
    # Query - Power filters
    power_min: Optional[float] = Field(None, description="Query: Min TX power in dBm")
    power_max: Optional[float] = Field(None, description="Query: Max TX power in dBm")
    
    # UPDATE VALUES - these will be applied to all matching cells
    # Prefix with "update_" to distinguish from query fields
    
    # RF parameters to update
    update_fc_hz: Optional[float] = Field(None, gt=0, description="Update: New carrier frequency in Hz")
    update_tx_rs_power_dbm: Optional[float] = Field(None, description="Update: New TX RS power in dBm")
    update_tilt_deg: Optional[float] = Field(None, description="Update: New tilt angle in degrees")
    update_roll_deg: Optional[float] = Field(None, description="Update: New roll angle in degrees")
    update_height_m: Optional[float] = Field(None, gt=0, description="Update: New height in meters")
    
    # Antenna configuration to update
    update_bs_rows: Optional[int] = Field(None, ge=1, description="Update: New number of antenna rows")
    update_bs_cols: Optional[int] = Field(None, ge=1, description="Update: New number of antenna columns")
    update_bs_pol: Optional[str] = Field(None, description="Update: New polarization type")
    update_bs_pol_type: Optional[str] = Field(None, description="Update: New polarization type detail")
    update_elem_v_spacing: Optional[float] = Field(None, gt=0, description="Update: New vertical element spacing")
    update_elem_h_spacing: Optional[float] = Field(None, gt=0, description="Update: New horizontal element spacing")
    update_antenna_pattern: Optional[str] = Field(None, description="Update: New antenna pattern")
    
    # NOTE: Identifier fields (site, sector_id, band, site_idx, etc.) are IMMUTABLE
    # and cannot be updated after cell creation
    
    # Control
    rename: bool = Field(True, description="Auto-rename cells after update")
    stop_on_error: bool = Field(False, description="Stop processing if an update fails")
    
    @validator('update_bs_cols')
    def validate_antenna_array_update(cls, v, values):
        """Validate update_bs_rows and update_bs_cols are updated together"""
        bs_rows = values.get('update_bs_rows')
        bs_cols = v
        
        # If one is provided, both must be provided
        if (bs_rows is not None and bs_cols is None):
            raise ValueError("update_bs_rows and update_bs_cols must be provided together. You provided update_bs_rows but not update_bs_cols.")
        if (bs_cols is not None and bs_rows is None):
            raise ValueError("update_bs_rows and update_bs_cols must be provided together. You provided update_bs_cols but not update_bs_rows.")
        
        return v
    
    class Config:
        schema_extra = {
            "examples": [
                {
                    "site_name": "SITE0001A",
                    "update_tilt_deg": 12.0
                },
                {
                    "site_name": "SITE000*",
                    "band": "H",
                    "update_tilt_deg": 11.0,
                    "update_tx_rs_power_dbm": 5.0
                },
                {
                    "band": "L",
                    "sector_id": 0,
                    "update_bs_rows": 8,
                    "update_bs_cols": 1
                }
            ]
        }


def update_cells_by_query(sim, request: QueryBasedUpdateRequest, query_cells_func) -> dict:
    """
    Query cells and apply the same update to all matching cells.
    
    Args:
        sim: MultiCellSim instance
        request: QueryBasedUpdateRequest with query criteria and update values
        query_cells_func: Function to query cells (from cell_query module)
        
    Returns:
        Dictionary with:
            - query_matched: Number of cells matched by query
            - num_updated: Number of cells successfully updated
            - num_failed: Number of failed updates
            - query_criteria: Query criteria used
            - update_values: Update values applied
            - results: List of update results
            - errors: List of errors (if any)
    """
    from cell_query import CellQuery
    
    # Build query from request
    query = CellQuery(
        cell_name=request.cell_name,
        site_name=request.site_name,
        band=request.band,
        sector_id=request.sector_id,
        site_idx=request.site_idx,
        bs_rows=request.query_bs_rows,
        bs_cols=request.query_bs_cols,
        bs_pol=request.query_bs_pol,
        antenna_pattern=request.query_antenna_pattern,
        fc_ghz_min=request.fc_ghz_min,
        fc_ghz_max=request.fc_ghz_max,
        fc_ghz=request.fc_ghz,
        tilt_min=request.tilt_min,
        tilt_max=request.tilt_max,
        tilt_deg=request.query_tilt_deg,
        power_min=request.power_min,
        power_max=request.power_max,
    )
    
    # Query for matching cells
    query_result = query_cells_func(sim, query)
    matched_cells = query_result['cells']
    
    if not matched_cells:
        logger.warning("Query matched no cells - no updates will be applied")
        return {
            "query_matched": 0,
            "num_updated": 0,
            "num_failed": 0,
            "query_criteria": query.dict(exclude_none=True),
            "update_values": {},
            "results": [],
            "errors": None,
        }
    
    # Build update values (only include fields that are set)
    # NOTE: Identifier fields (site, sector_id, band) are excluded - they're immutable
    update_values = {}
    update_field_map = {
        'update_fc_hz': 'fc_hz',
        'update_tx_rs_power_dbm': 'tx_rs_power_dbm',
        'update_tilt_deg': 'tilt_deg',
        'update_roll_deg': 'roll_deg',
        'update_height_m': 'height_m',
        'update_bs_rows': 'bs_rows',
        'update_bs_cols': 'bs_cols',
        'update_bs_pol': 'bs_pol',
        'update_bs_pol_type': 'bs_pol_type',
        'update_elem_v_spacing': 'elem_v_spacing',
        'update_elem_h_spacing': 'elem_h_spacing',
        'update_antenna_pattern': 'antenna_pattern',
    }
    
    for request_field, update_field in update_field_map.items():
        value = getattr(request, request_field)
        if value is not None:
            update_values[update_field] = value
    
    if not update_values:
        raise ValueError("No update values provided. Specify at least one 'update_*' field.")
    
    logger.info(f"Query matched {len(matched_cells)} cells. Applying updates: {list(update_values.keys())}")
    
    # Apply updates to all matched cells
    results = []
    errors = []
    
    for idx, cell in enumerate(matched_cells):
        cell_id = cell['cell_idx']
        try:
            # Build update request for this cell
            update_req = CellUpdateRequest(
                cell_id=cell_id,
                rename=request.rename,
                **update_values
            )
            
            result = update_cell_config(sim, update_req)
            results.append({
                "index": idx,
                "status": "success",
                "cell_id": result["cell_id"],
                "cell_name": result["cell_name"],
                "updated_fields": result["updated_fields"],
            })
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Query-based update failed for cell {cell_id} at index {idx}: {error_msg}")
            errors.append({
                "index": idx,
                "cell_id": cell_id,
                "error": error_msg,
            })
            results.append({
                "index": idx,
                "cell_id": cell_id,
                "status": "failed",
                "error": error_msg,
            })
            
            if request.stop_on_error:
                logger.warning(f"Stopping query-based update after error at index {idx}")
                break
    
    num_updated = sum(1 for r in results if r.get("status") == "success")
    num_failed = len(errors)
    
    return {
        "query_matched": len(matched_cells),
        "num_updated": num_updated,
        "num_failed": num_failed,
        "query_criteria": query.dict(exclude_none=True),
        "update_values": update_values,
        "results": results,
        "errors": errors if errors else None,
    }

