from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from simulation.engine import MultiCellSim
from simulation.helpers import rsrp_rows_as_dicts
from api.cell_query import CellQuery, query_cells
from api.cell_update import CellUpdateRequest, BulkCellUpdateRequest, QueryBasedUpdateRequest, update_cell_config, update_cells_bulk, update_cells_by_query
from api.ue_management import UEDropRequest, get_ue_info, drop_ues
from simulation.initialization import SimInitializationRequest, initialize_simulation
import numpy as np
import uvicorn
from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, validator, Field
import logging
import asyncio
import concurrent.futures
from functools import partial
from db.arango_client import init_arango
from db.persist_run import persist_run
import re


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SmartRAN Studio Simulation API",
    description="FastAPI interface for SmartRAN Studio Sionna multi-cell simulation",
    version="1.0.0"
)

db = None
sim_runs = None
sim_reports = None

# Global simulation instance
sim: Optional[MultiCellSim] = None

# Thread pool for blocking operations (releases GIL)
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=1, thread_name_prefix="compute")

# Concurrency locks
compute_lock = asyncio.Lock()    # Serialize GPU compute operations
config_lock = asyncio.Lock()     # Protect configuration reads/writes

# Compute state tracking
compute_in_progress = False

# Pydantic models for request bodies
class CellTiltUpdate(BaseModel):
    cell_id: Optional[int] = None
    cell_name: Optional[str] = None
    tilt_deg: float

    
    @validator('cell_name')
    def validate_cell_identifier(cls, v, values):
        if v is None and values.get('cell_id') is None:
            raise ValueError('Either cell_id or cell_name must be provided')
        if v is not None and values.get('cell_id') is not None:
            raise ValueError('Provide either cell_id OR cell_name, not both')
        return v

class CellTiltUpdates(BaseModel):
    updates: List[CellTiltUpdate]

# Pydantic models for site/cell management
class CellSpec(BaseModel):
    """Specification for a cell to add to a site"""
    sector_id: int = Field(..., ge=0, le=2, description="Sector ID (0, 1, or 2)")
    band: str = Field(..., description="Band identifier (e.g., 'H', 'L', 'M')")
    fc_hz: float = Field(..., gt=0, description="Frequency in Hz")
    tilt_deg: float = Field(9.0, description="Antenna tilt in degrees")
    tx_rs_power_dbm: float = Field(0.0, description="TX power in dBm")
    bs_rows: Optional[int] = Field(None, ge=1, description="Antenna rows")
    bs_cols: Optional[int] = Field(None, ge=1, description="Antenna columns")
    bs_pol: Optional[str] = Field(None, description="Polarization")
    bs_pol_type: Optional[str] = Field(None, description="Polarization type")
    elem_v_spacing: Optional[float] = Field(None, description="Vertical element spacing")
    elem_h_spacing: Optional[float] = Field(None, description="Horizontal element spacing")
    antenna_pattern: Optional[str] = Field(None, description="Antenna pattern model")

class AddSiteRequest(BaseModel):
    """Request to add a new site to the simulation"""
    x: float = Field(..., description="X coordinate in meters")
    y: float = Field(..., description="Y coordinate in meters")
    height_m: float = Field(20.0, gt=0, description="Site height in meters")
    az0_deg: float = Field(0.0, description="Sector 0 azimuth in degrees")
    cells: Optional[List[CellSpec]] = Field(None, description="Cells to add to this site (optional)")

class AddCellRequest(BaseModel):
    """Request to add a single cell to an existing site"""
    site_name: str = Field(..., description="Existing site name (e.g., 'SITE0001A')")
    sector_id: int = Field(..., ge=0, le=2, description="Sector ID (0, 1, or 2)")
    band: str = Field(..., description="Band identifier (e.g., 'H', 'L')")
    fc_hz: float = Field(..., gt=0, description="Frequency in Hz")
    tilt_deg: float = Field(9.0, description="Antenna tilt in degrees")
    tx_rs_power_dbm: float = Field(0.0, description="TX power in dBm")
    sector_azimuth: Optional[float] = Field(None, description="Sector azimuth in degrees (only for first cell on sector)")
    bs_rows: Optional[int] = Field(None, ge=1, description="Antenna rows")
    bs_cols: Optional[int] = Field(None, ge=1, description="Antenna columns")
    bs_pol: Optional[str] = Field(None, description="Polarization")
    bs_pol_type: Optional[str] = Field(None, description="Polarization type")
    elem_v_spacing: Optional[float] = Field(None, description="Element spacing (vertical)")
    elem_h_spacing: Optional[float] = Field(None, description="Element spacing (horizontal)")
    antenna_pattern: Optional[str] = Field(None, description="Antenna pattern model")

def check_sim_initialized():
    """Check if simulation is initialized, raise HTTPException if not"""
    if sim is None:
        raise HTTPException(
            status_code=503, 
            detail="Simulation not initialized. Call POST /initialize first."
        )

def check_config_changes_allowed():
    """Check if configuration changes are allowed (not during compute)"""
    check_sim_initialized()
    if compute_in_progress:
        raise HTTPException(
            status_code=409,  # Conflict
            detail="Cannot modify configuration while compute is in progress. Please wait for compute to complete."
        )

def find_cell_id_by_name(cell_name: str) -> int:
    """Find cell index by cell name"""
    check_sim_initialized()
    
    for i, cell in enumerate(sim.cells):
        if cell.get('name') == cell_name:
            return i
    
    raise HTTPException(status_code=404, detail=f"Cell name '{cell_name}' not found")

@app.on_event("startup")
async def startup_event():
    """API startup - simulation must be initialized via POST /initialize"""
    global db, sim_runs, sim_reports
    db = init_arango()
    # ensure collections exist
    if not db.has_collection("sim_runs"):
        db.create_collection("sim_runs")
    if not db.has_collection("sim_reports"):
        db.create_collection("sim_reports")

    sim_runs = db.collection("sim_runs")
    sim_reports = db.collection("sim_reports")
    print("✅ Connected to ArangoDB:", db.name)
    logger.info(f"✅ Connected to ArangoDB: {db.name}")
    logger.info("CNS Sionna Simulation API started")
    logger.info("Simulation NOT auto-initialized - call POST /initialize to start")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down thread pool...")
    thread_pool.shutdown(wait=True)

@app.post("/initialize")
async def initialize_endpoint(config: SimInitializationRequest):
    """
    Initialize the simulation with custom configuration.
    
    This endpoint MUST be called before using any other simulation endpoints.
    If simulation is already initialized, this will REPLACE it with a new one.
    
    Configurable parameters:
    - Site layout: n_sites, spacing, seed, jitter
    - Site config: site_height_m
    - High band: fc_hi_hz, tilt_hi_deg, bs_rows_hi, bs_cols_hi, antenna_pattern_hi
    - Low band: fc_lo_hz, tilt_lo_deg, bs_rows_lo, bs_cols_lo, antenna_pattern_lo
    - UEs: num_ue, box_pad_m
    - Chunking: cells_chunk, ue_chunk
    
    All parameters have sensible defaults - only specify what you want to change.
    
    Example (minimal - use all defaults):
    POST /initialize
    {}
    
    Example (custom configuration):
    POST /initialize
    {
      "n_sites": 20,
      "spacing": 600.0,
      "seed": 42,
      "fc_hi_hz": 3500e6,
      "fc_lo_hz": 700e6,
      "num_ue": 50000
    }
    """
    global sim
    
    # Check if compute is running before allowing initialization/reinitialization
    if compute_in_progress:
        raise HTTPException(
            status_code=409,
            detail="Cannot initialize simulation while compute is in progress. Please wait for compute to complete."
        )
    
    async with config_lock:
        try:
            if sim is not None:
                logger.warning("Simulation already initialized - replacing with new configuration")
            
            result = initialize_simulation(config)
            sim = result['sim']
            
            # Store the init config on the sim object for later reference
            sim.init_config = config.dict()
            sim.init_config_summary = result['config_summary']
            
            return {
                "message": "Simulation initialized successfully",
                "num_sites": result['num_sites'],
                "num_cells": result['num_cells'],
                "num_ues": result['num_ues'],
                "high_band_cells": result['num_hi_cells'],
                "low_band_cells": result['num_lo_cells'],
                "config": result['config_summary'],
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error initializing simulation: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to initialize simulation: {str(e)}")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "CNS Sionna Simulation API is running", "status": "healthy"}

@app.get("/status")
async def get_status():
    """Get simulation status and configuration"""
    check_sim_initialized()
    
    # Protect config reads for consistency
    async with config_lock:
        metadata = sim.get_metadata(include_time=True)
        
        return {
            "simulation_status": "ready",
            "num_sites": len(sim.sites),
            "num_cells": len(sim.cells),
            "num_ues": metadata["num_users"],
            "num_bands": metadata["num_bands"],
            "bands": metadata["bands"],
            "cells_chunk": getattr(sim, 'cells_chunk', None),
            "ue_chunk": getattr(sim, 'ue_chunk', None),
            "metadata": metadata
        }

@app.post("/measurement-reports")
async def get_measurement_reports(
    name: str,  # Required: snapshot name
    threshold_dbm: float = -120.0,
    label_mode: str = "name",
    return_payload: bool = False,  # optional: keep False in prod
):
    """
    Run fresh simulation, store reports to Arango, and return a pointer to the run.
    Args:
        name: Required snapshot name for easy identification
        threshold_dbm: RSRP threshold in dBm
        label_mode: Label mode for reports ('name' or 'idx')
        return_payload: Whether to include full payload in response
    """
    global compute_in_progress
    check_sim_initialized()

    try:
        # --- serialize compute ---
        async with compute_lock:
            compute_in_progress = True
            try:
                loop = asyncio.get_event_loop()

                # 0) Mint run_id ONCE (no timestep increment side-effect)
                meta_for_id = sim.get_metadata(include_time=True, auto_increment=False)
                run_id = meta_for_id["timestamp"]        # e.g. "2025-11-06_00-05-22"
                unix_ts = meta_for_id.get("unix_timestamp")

                # 1) Compute
                logger.info(f"[{run_id}] Running compute…")
                RSRP_dBm, cells_meta = await loop.run_in_executor(thread_pool, sim.compute)
                logger.info(f"[{run_id}] Compute done: RSRP shape={RSRP_dBm.shape}")
            finally:
                compute_in_progress = False

        # 2) Build per-user measurement dicts (same as before)
        logger.info(f"[{run_id}] Building measurement reports (thr={threshold_dbm} dBm)")
        ue_meas_reports = await loop.run_in_executor(
            thread_pool,
            partial(
                rsrp_rows_as_dicts,
                RSRP_dBm,
                cells_meta,
                threshold_dbm=threshold_dbm,
                label_mode=label_mode,
                ue_locations=sim.ue_loc[0],  # [U, 3] -> x,y from [:,0:2]
            ),
        )

        # 3) Get metadata (no new timestamp) and enforce the same run_id in it
        async with config_lock:
            base_meta = sim.get_metadata(include_time=False)
            # Capture current cell states (all tilts and configurations)
            cell_states = sim.cells_table()
            # Get init config (stored during initialization)
            init_config = getattr(sim, 'init_config', {})
            init_config_summary = getattr(sim, 'init_config_summary', {})
        
        metadata = {**base_meta, "timestamp": run_id, "name": name}
        if unix_ts is not None:
            metadata["unix_timestamp"] = unix_ts
        
        # Add init_config and cell_states to metadata
        metadata["init_config"] = init_config
        metadata["init_config_summary"] = init_config_summary
        metadata["cell_states_at_run"] = cell_states

        # 4) Persist to Arango (run header + one doc per user)
        await loop.run_in_executor(
            thread_pool,
            persist_run,
            sim_runs,
            sim_reports,
            run_id,
            ue_meas_reports,
            metadata,
            threshold_dbm,
            label_mode,
        )

        # 5) Return pointer (optionally include big payload if return_payload=True)
        resp = {
            "run_id": run_id,
            "status": "stored",
            "num_reports": len(ue_meas_reports),
            "threshold_dbm": threshold_dbm,
            "label_mode": label_mode,
            "access": {
                "metadata": f"/runs/{run_id}",
                "reports": f"/runs/{run_id}/reports?limit=1000",
            },
            "metadata": metadata,
        }
        if return_payload:
            resp["measurement_reports"] = ue_meas_reports
            resp["metadata"] = metadata
        return resp

    except Exception as e:
        logger.error(f"Failed to generate/store reports: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate/store reports: {e}")


@app.get("/runs")
async def list_runs(
    limit: int = 100,
    offset: int = 0,
    sort_by: str = "created_at",
    sort_order: str = "desc"
):
    """
    List all simulation runs stored in ArangoDB.
    
    Args:
        limit: Maximum number of runs to return (default: 100)
        offset: Number of runs to skip (default: 0)
        sort_by: Field to sort by (default: "created_at")
        sort_order: "asc" or "desc" (default: "desc")
    
    Returns:
        List of runs with metadata (newest first by default)
    """
    try:
        # Build AQL query
        sort_direction = "DESC" if sort_order.lower() == "desc" else "ASC"
        query = f"""
        FOR run IN sim_runs
            SORT run.@sort_by {sort_direction}
            LIMIT @offset, @limit
            RETURN {{
                run_id: run._key,
                name: run.metadata.name,
                created_at: run.created_at,
                num_reports: run.num_reports,
                num_sites: run.metadata.init_config_summary.n_sites,
                num_cells: LENGTH(run.metadata.cell_states_at_run),
                num_ues: run.metadata.num_users,
                bands: run.metadata.bands
            }}
        """
        
        cursor = db.aql.execute(
            query,
            bind_vars={
                "sort_by": sort_by,
                "offset": offset,
                "limit": limit
            }
        )
        runs = list(cursor)
        
        # Get total count
        count_query = "RETURN LENGTH(sim_runs)"
        total_count = list(db.aql.execute(count_query))[0]
        
        return {
            "runs": runs,
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Failed to list runs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list runs: {e}")


@app.get("/runs/{run_id}")
async def get_run(run_id: str):
    """
    Get detailed metadata for a specific run.
    
    Args:
        run_id: The run ID (timestamp format like "2025-11-06_00-05-22")
    
    Returns:
        Full run metadata including init_config and cell_states_at_run
    """
    try:
        # Get run from sim_runs collection
        run_doc = sim_runs.get(run_id)
        
        if not run_doc:
            raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")
        
        return {
            "run_id": run_id,
            "created_at": run_doc.get("created_at"),
            "threshold_dbm": run_doc.get("threshold_dbm"),
            "label_mode": run_doc.get("label_mode"),
            "num_reports": run_doc.get("num_reports"),
            "metadata": run_doc.get("metadata", {}),
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get run {run_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get run: {e}")


@app.get("/runs/{run_id}/reports")
async def get_run_reports(
    run_id: str,
    limit: int = 1000,
    offset: int = 0,
    user_id_min: Optional[int] = None,
    user_id_max: Optional[int] = None
):
    """
    Get measurement reports for a specific run with pagination.
    
    Args:
        run_id: The run ID
        limit: Maximum number of reports to return (default: 1000)
        offset: Number of reports to skip (default: 0)
        user_id_min: Filter for user IDs >= this value (optional)
        user_id_max: Filter for user IDs <= this value (optional)
    
    Returns:
        Paginated list of measurement reports for the run
    """
    try:
        # Check if run exists
        if not sim_runs.has(run_id):
            raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")
        
        # Build AQL query with optional filters
        filters = ["doc.run_id == @run_id"]
        bind_vars = {"run_id": run_id, "offset": offset, "limit": limit}
        
        if user_id_min is not None:
            filters.append("doc.user_id >= @user_id_min")
            bind_vars["user_id_min"] = user_id_min
        
        if user_id_max is not None:
            filters.append("doc.user_id <= @user_id_max")
            bind_vars["user_id_max"] = user_id_max
        
        filter_clause = " AND ".join(filters)
        
        query = f"""
        FOR doc IN sim_reports
            FILTER {filter_clause}
            SORT doc.user_id ASC
            LIMIT @offset, @limit
            RETURN {{
                user_id: doc.user_id,
                x: doc.x,
                y: doc.y,
                readings: doc.readings
            }}
        """
        
        cursor = db.aql.execute(query, bind_vars=bind_vars)
        reports = list(cursor)
        
        # Get total count for this run
        count_query = f"""
        FOR doc IN sim_reports
            FILTER {filter_clause}
            COLLECT WITH COUNT INTO total
            RETURN total
        """
        total_count = list(db.aql.execute(count_query, bind_vars={k: v for k, v in bind_vars.items() if k != 'offset' and k != 'limit'}))[0]
        
        return {
            "run_id": run_id,
            "reports": reports,
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get reports for run {run_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get reports: {e}")


@app.delete("/runs/{run_id}")
async def delete_run(run_id: str):
    """
    Delete a simulation run and all its associated reports.
    
    Args:
        run_id: The run ID to delete
    
    Returns:
        Confirmation of deletion
    """
    try:
        # Check if run exists
        if not sim_runs.has(run_id):
            raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")
        
        # Delete all reports for this run
        delete_reports_query = """
        FOR doc IN sim_reports
            FILTER doc.run_id == @run_id
            REMOVE doc IN sim_reports
            COLLECT WITH COUNT INTO deleted
            RETURN deleted
        """
        cursor = db.aql.execute(delete_reports_query, bind_vars={"run_id": run_id})
        num_reports_deleted = list(cursor)[0]
        
        # Delete the run header
        sim_runs.delete(run_id)
        
        logger.info(f"Deleted run {run_id} and {num_reports_deleted} associated reports")
        
        return {
            "run_id": run_id,
            "num_reports_deleted": num_reports_deleted,
            "status": "deleted",
            "message": f"Run '{run_id}' and {num_reports_deleted} reports deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete run {run_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete run: {e}")


@app.post("/update-cell-tilts")
async def update_cell_tilts(request: CellTiltUpdates):
    """
    Update antenna tilt angles for multiple cells by cell_id OR cell_name
    
    Args:
        request: List of updates with either cell_id or cell_name, plus tilt_deg
    
    Examples:
        By cell_id: {"updates": [{"cell_id": 0, "tilt_deg": 8.0}]}
        By cell_name: {"updates": [{"cell_name": "HSITE0001A1", "tilt_deg": 8.0}]}
        Mixed: {"updates": [{"cell_id": 0, "tilt_deg": 8.0}, {"cell_name": "LSITE0005A2", "tilt_deg": 4.5}]}
    
    Returns:
        Summary of updates applied
    """
    check_config_changes_allowed()
    
    if not request.updates:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    # Protect configuration modifications
    async with config_lock:
        try:
            updated_cells = []
            failed_updates = []
            
            for update in request.updates:
                try:
                    # Determine cell_id from either cell_id or cell_name
                    if update.cell_id is not None:
                        cell_id = update.cell_id
                        identifier = f"cell_id={cell_id}"
                    else:
                        cell_id = find_cell_id_by_name(update.cell_name)
                        identifier = f"cell_name='{update.cell_name}'"
                    
                    # Validate cell_id exists
                    if cell_id < 0 or cell_id >= len(sim.cells):
                        failed_updates.append({
                            "identifier": identifier,
                            "error": f"Cell ID {cell_id} out of range (0-{len(sim.cells)-1})"
                        })
                        continue
                    
                    # Get old tilt for logging
                    old_tilt = sim.cells[cell_id].get('tilt_deg')
                    
                    # Update the cell tilt
                    sim.update_cell(cell_id, tilt_deg=update.tilt_deg)
                    
                    # Get cell info for response
                    cell_info = sim.get_cell(cell_id)
                    updated_cells.append({
                        "cell_id": cell_id,
                        "cell_name": cell_info["cell_name"],
                        "old_tilt_deg": old_tilt,
                        "new_tilt_deg": update.tilt_deg,
                        "band": cell_info["band"],
                        "site_name": cell_info["site_name"],
                        "sector_id": cell_info["sector_id"],
                        "identifier_used": identifier
                    })
                    
                    logger.info(f"Updated cell {cell_id} ({cell_info['cell_name']}) tilt: {old_tilt}° → {update.tilt_deg}° via {identifier}")
                    
                except Exception as e:
                    failed_updates.append({
                        "identifier": identifier if 'identifier' in locals() else "unknown",
                        "error": str(e)
                    })
            
            return {
                "updated_cells": updated_cells,
                "failed_updates": failed_updates,
                "num_updated": len(updated_cells),
                "num_failed": len(failed_updates),
                "status": "success" if updated_cells else "failed"
            }
            
        except Exception as e:
            logger.error(f"Error updating cell tilts: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to update cell tilts: {str(e)}")

@app.post("/update-cell")
async def update_cell_endpoint(request: CellUpdateRequest):
    """
    Generic cell configuration update endpoint.
    
    Update ANY cell parameter - identify cell by ID or name,
    provide only the fields you want to change.
    
    Supports updating:
    - RF parameters (frequency, power, tilt, roll, height)
    - Antenna configuration (rows, cols, polarization, spacing, pattern)
    - Site/sector/band assignment
    
    Examples:
    
    1. Update tilt only:
       POST /update-cell
       {"cell_id": 0, "tilt_deg": 12.0}
    
    2. Update multiple RF params:
       POST /update-cell
       {"cell_name": "HSITE0001A1", "tilt_deg": 12.0, "tx_rs_power_dbm": 5.0}
    
    3. Change antenna array:
       POST /update-cell
       {"cell_id": 5, "bs_rows": 8, "bs_cols": 1}
    
    4. Update frequency and power:
       POST /update-cell
       {"cell_id": 10, "fc_hz": 2600000000, "tx_rs_power_dbm": 3.0}
    
    Returns:
        - cell_id: ID of updated cell
        - cell_name: Name after update
        - updated_fields: List of changed fields
        - cell: Full updated cell configuration
    """
    check_config_changes_allowed()
    
    # Protect configuration modifications
    async with config_lock:
        try:
            result = update_cell_config(sim, request)
            result["status"] = "success"
            return result
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Error in update-cell: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")

@app.post("/update-cells-bulk")
async def update_cells_bulk_endpoint(request: BulkCellUpdateRequest):
    """
    Bulk update multiple cells at once.
    
    Applies a list of cell updates sequentially. By default, continues
    processing all updates even if some fail. Set stop_on_error=true
    to stop at the first failure.
    
    Example:
    
    Update tilts for multiple cells:
    POST /update-cells-bulk
    {
      "updates": [
        {"cell_id": 0, "tilt_deg": 12.0},
        {"cell_id": 1, "tilt_deg": 12.0},
        {"cell_name": "HSITE0003A1", "tilt_deg": 10.0}
      ],
      "stop_on_error": false
    }
    
    Returns:
        - num_requested: Total updates requested
        - num_successful: Number that succeeded
        - num_failed: Number that failed
        - results: Detailed results for each update
        - errors: List of errors (if any)
    """
    check_config_changes_allowed()
    
    # Protect configuration modifications
    async with config_lock:
        try:
            result = update_cells_bulk(sim, request)
            result["status"] = "success" if result["num_failed"] == 0 else "partial"
            return result
        except Exception as e:
            logger.error(f"Error in update-cells-bulk: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Bulk update failed: {str(e)}")

@app.post("/update-cells-by-query")
async def update_cells_by_query_endpoint(request: QueryBasedUpdateRequest):
    """
    Query cells and apply the same update to all matching cells.
    
    Combines /query-cells + /update-cells-bulk in one operation.
    First queries for cells matching criteria, then applies the same
    update values to all of them.
    
    Query fields: Use regular field names (site_name, band, sector_id, etc.)
    Update fields: Use "update_" prefix (update_tilt_deg, update_tx_rs_power_dbm, etc.)
    
    Examples:
    
    1. Update all cells from a site:
       POST /update-cells-by-query
       {
         "site_name": "SITE0001A",
         "update_tilt_deg": 12.0
       }
    
    2. Wildcard update - all sites starting with SITE000, high band only:
       POST /update-cells-by-query
       {
         "site_name": "SITE000*",
         "band": "H",
         "update_tilt_deg": 11.0,
         "update_tx_rs_power_dbm": 5.0
       }
    
    3. Update antenna config for all low band, sector 0 cells:
       POST /update-cells-by-query
       {
         "band": "L",
         "sector_id": 0,
         "update_bs_rows": 8,
         "update_bs_cols": 1
       }
    
    4. Update all cells with current tilt > 10:
       POST /update-cells-by-query
       {
         "tilt_min": 10.0,
         "update_tilt_deg": 9.0
       }
    
    Returns:
        - query_matched: Number of cells matched by query
        - num_updated: Number successfully updated
        - num_failed: Number that failed
        - query_criteria: Query used
        - update_values: Values applied
        - results: Detailed results per cell
        - errors: Any errors (if applicable)
    """
    check_config_changes_allowed()
    
    # Protect configuration modifications
    async with config_lock:
        try:
            result = update_cells_by_query(sim, request, query_cells)
            result["status"] = "success" if result["num_failed"] == 0 else "partial"
            return result
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Error in update-cells-by-query: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Query-based update failed: {str(e)}")

@app.post("/reinitialize")
async def reinitialize_simulation():
    """
    DEPRECATED: Use POST /initialize instead for configurable initialization.
    
    Reinitialize the simulation with default configuration.
    """
    # Check if compute is running
    if compute_in_progress:
        raise HTTPException(
            status_code=409,
            detail="Cannot reinitialize simulation while compute is in progress. Please wait for compute to complete."
        )
    
    # Protect global simulation state during reinitialization
    async with config_lock:
        try:
            initialize_simulation()
            return {"message": "Simulation reinitialized successfully (deprecated - use POST /initialize)", "status": "success"}
        except Exception as e:
            logger.error(f"Error reinitializing simulation: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Reinitialization failed: {str(e)}")

@app.get("/sites")
async def get_sites():
    """Get information about all sites"""
    check_sim_initialized()
    
    # Protect config reads for consistency
    async with config_lock:
        return {
            "sites": sim.sites_table(),
            "num_sites": len(sim.sites),
            "status": "success"
        }

@app.get("/cells")
async def get_cells():
    """Get information about all cells"""
    check_sim_initialized()
    
    # Protect config reads for consistency
    async with config_lock:
        return {
            "cells": sim.cells_table(),
            "num_cells": len(sim.cells),
            "status": "success"
        }

@app.get("/ues")
async def get_ues_endpoint():
    """
    Get information about current UE drop in the simulation.
    
    Returns:
        - num_ues: Current number of UEs
        - layout: Drop layout type ('disk' or 'box')
        - drop_params: Parameters used for drop (center, radius/box bounds, etc.)
        - has_results: Whether compute() has been run with current UEs
        - results: (if has_results=true) Info about computed RSRP, assignments
    """
    check_sim_initialized()
    
    async with config_lock:
        try:
            ue_info = get_ue_info(sim)
            ue_info["status"] = "success"
            return ue_info
        except Exception as e:
            logger.error(f"Error getting UE info: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to get UE info: {str(e)}")

@app.post("/drop-ues")
async def drop_ues_endpoint(request: UEDropRequest):
    """
    Drop or re-drop UEs in the simulation.
    
    WARNING: This REPLACES all existing UEs! Any previous compute() results
    for UEs will be invalidated. You must call /measurement-reports again
    after dropping UEs.
    
    Args:
        num_ue: Number of UEs to drop
        layout: 'disk' or 'box'
        center_x, center_y: Center point (optional, defaults to site mean)
        radius_m: Radius for disk layout
        box_pad_m: Padding for box layout
        height_m: UE height
        seed: Random seed
    """
    check_config_changes_allowed()
    
    async with config_lock:
        try:
            result = drop_ues(sim, request)
            result["status"] = "success"
            return result
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Error dropping UEs: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to drop UEs: {str(e)}")

@app.post("/query-cells")
async def query_cells_endpoint(query: CellQuery):
    """
    Query cells with flexible filtering criteria.
    
    Supports:
    - Wildcard matching (*) in cell_name and site_name
    - Exact matches for band, sector_id, antenna config
    - Range filters for frequency, tilt, power
    - Sorting and pagination
    
    Returns same cell format as /cells endpoint.
    
    Example queries:
    
    1. All high-band cells:
       POST /query-cells
       {"band": "H"}
    
    2. Cells from sites starting with SITE000:
       POST /query-cells
       {"site_name": "SITE000*"}
    
    3. Cells with 8x1 arrays in high band:
       POST /query-cells
       {"band": "H", "bs_rows": 8, "bs_cols": 1}
    
    4. Frequency range with steep tilt:
       POST /query-cells
       {"fc_ghz_min": 2.0, "fc_ghz_max": 3.0, "tilt_min": 10}
    
    5. Paginated results:
       POST /query-cells
       {"band": "H", "limit": 10, "offset": 0}
    """
    check_sim_initialized()
    
    # Protect config reads for consistency
    async with config_lock:
        try:
            result = query_cells(sim, query)
            result["status"] = "success"
            return result
        except Exception as e:
            logger.error(f"Error in query-cells: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

@app.post("/add-site")
async def add_site_endpoint(request: AddSiteRequest):
    """
    Add a new site with configurable cells to the existing simulation.
    
    Enforces naming convention: SITE{site_number:04d}A
    - site_number is auto-calculated as next available number
    - Can add with 0 cells, or specify cells to create
    
    Args:
        x, y: Site coordinates in meters
        height_m: Site height in meters (default: 20.0)
        az0_deg: Sector 0 azimuth in degrees (default: 0.0)
        cells: List of cells to add to this site (optional)
               Each cell needs: sector_id, band, fc_hz, tilt_deg, etc.
    
    Returns:
        site_idx: Internal site index
        site_name: Generated site name (e.g., SITE0001A)
        site_number: Site number (e.g., 1)
        cells_added: List of cells created
    
    Example (site with no cells):
        POST /add-site
        {"x": 1000.0, "y": 500.0}
    
    Example (site with cells):
        POST /add-site
        {
            "x": 1000.0, 
            "y": 500.0,
            "height_m": 25.0,
            "az0_deg": 45.0,
            "cells": [
                {"sector_id": 0, "band": "H", "fc_hz": 2500e6, "tilt_deg": 9.0},
                {"sector_id": 0, "band": "L", "fc_hz": 600e6, "tilt_deg": 9.0}
            ]
        }
    """
    check_config_changes_allowed()
    
    async with config_lock:
        try:
            # Calculate next site number from existing sites
            max_site_num = 0
            for site in sim.sites:
                # Parse existing site names like SITE0001A -> 0001
                match = re.match(r'SITE(\d{4})A', site['name'])
                if match:
                    max_site_num = max(max_site_num, int(match.group(1)))
            
            next_site_num = max_site_num + 1
            site_name = f"SITE{next_site_num:04d}A"
            
            # Add the site
            site_idx = sim.add_site(
                x=request.x, 
                y=request.y, 
                height_m=request.height_m,
                az0_deg=request.az0_deg,
                name=site_name,
                uid=site_name
            )
            
            logger.info(f"Added site {site_name} at ({request.x}, {request.y})")
            
            # Add cells if requested
            cells_added = []
            for cell_spec in (request.cells or []):
                cell_idx = sim.add_cell(
                    site=site_name,
                    sector_id=cell_spec.sector_id,
                    band=cell_spec.band,
                    fc_hz=cell_spec.fc_hz,
                    tilt_deg=cell_spec.tilt_deg,
                    tx_rs_power_dbm=cell_spec.tx_rs_power_dbm,
                    bs_rows=cell_spec.bs_rows,
                    bs_cols=cell_spec.bs_cols,
                    bs_pol=cell_spec.bs_pol,
                    bs_pol_type=cell_spec.bs_pol_type,
                    elem_v_spacing=cell_spec.elem_v_spacing,
                    elem_h_spacing=cell_spec.elem_h_spacing,
                    antenna_pattern=cell_spec.antenna_pattern
                )
                cells_added.append({
                    "cell_idx": cell_idx,
                    "cell_name": sim.cells[cell_idx]['name'],
                    "band": cell_spec.band,
                    "sector_id": cell_spec.sector_id
                })
                logger.info(f"Added cell {sim.cells[cell_idx]['name']} to site {site_name}")
            
            return {
                "status": "success",
                "site_idx": site_idx,
                "site_name": site_name,
                "site_number": next_site_num,
                "position": {"x": request.x, "y": request.y},
                "height_m": request.height_m,
                "az0_deg": request.az0_deg,
                "cells_added": cells_added,
                "num_cells_added": len(cells_added)
            }
            
        except ValueError as e:
            # Catches duplicate name errors and validation errors
            logger.error(f"Validation error adding site: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Error adding site: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to add site: {str(e)}")


@app.post("/add-cell")
async def add_cell_endpoint(request: AddCellRequest):
    """
    Add a single cell to an existing site/sector.
    
    ENFORCES RULES:
    1. Cell must be added to an existing site
    2. Max 3 sectors per site (0, 1, 2)
    3. Each band must be unique per sector (no duplicate H+H on same sector)
    4. Sector azimuth can only be set on first cell for that sector
    5. Subsequent cells on same sector inherit the sector's azimuth
    
    Args:
        site_name: Existing site name (e.g., "SITE0001A")
        sector_id: 0, 1, or 2
        band: Band identifier (e.g., "H", "L", "M")
        fc_hz: Frequency in Hz
        tilt_deg: Antenna tilt in degrees (default: 9.0)
        tx_rs_power_dbm: TX power in dBm (default: 0.0)
        sector_azimuth: Sector azimuth (optional, only for first cell on sector)
        bs_rows, bs_cols: Antenna array configuration (optional, uses sim defaults)
        Other antenna parameters: polarization, spacing, pattern (all optional)
    
    Returns:
        cell_idx: Internal cell index
        cell_name: Generated cell name
        site_name: Site the cell was added to
        sector_id: Sector number
        band: Band identifier
        sector_azimuth: Sector azimuth used
        is_first_cell_on_sector: Whether this was the first cell on this sector
    
    Example:
        POST /add-cell
        {
            "site_name": "SITE0001A",
            "sector_id": 0,
            "band": "H",
            "fc_hz": 2500000000,
            "tilt_deg": 12.0,
            "sector_azimuth": 45.0
        }
    """
    check_config_changes_allowed()
    
    async with config_lock:
        try:
            # Verify site exists and get site info
            site_idx = None
            site_info = None
            for idx, s in enumerate(sim.sites):
                if s['name'] == request.site_name:
                    site_idx = idx
                    site_info = s
                    break
            
            if site_info is None:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Site '{request.site_name}' not found. Create site first with /add-site"
                )
            
            # Check if any cells already exist on this site/sector combination
            existing_cells_on_sector = [
                c for c in sim.cells 
                if c['site_id'] == site_idx and c['sector_id'] == request.sector_id
            ]
            
            is_first_cell_on_sector = len(existing_cells_on_sector) == 0
            
            # Check for duplicate bands on same sector
            existing_bands = [c['band'] for c in existing_cells_on_sector]
            if request.band in existing_bands:
                raise HTTPException(
                    status_code=400,
                    detail=f"Band '{request.band}' already exists on {request.site_name} sector {request.sector_id}. Each band must be unique per sector. Existing bands: {', '.join(existing_bands)}"
                )
            
            # Handle sector azimuth
            if is_first_cell_on_sector:
                # First cell on this sector - use provided azimuth or default
                if request.sector_azimuth is not None:
                    sector_azimuth = request.sector_azimuth % 360.0
                    # Update the site's sector azimuth
                    sim.set_sector_az(request.site_name, request.sector_id, sector_azimuth)
                    logger.info(f"Set sector {request.sector_id} azimuth to {sector_azimuth}° for {request.site_name}")
                else:
                    # Use existing azimuth from site definition
                    sector_azimuth = site_info['az_deg'][request.sector_id]
            else:
                # Not first cell - use existing sector azimuth, ignore any provided value
                sector_azimuth = site_info['az_deg'][request.sector_id]
                if request.sector_azimuth is not None and abs(request.sector_azimuth - sector_azimuth) > 0.01:
                    logger.warning(f"Ignoring sector_azimuth={request.sector_azimuth}° - sector {request.sector_id} already has azimuth {sector_azimuth}°")
            
            # Add the cell
            cell_idx = sim.add_cell(
                site=request.site_name,
                sector_id=request.sector_id,
                band=request.band,
                fc_hz=request.fc_hz,
                tilt_deg=request.tilt_deg,
                tx_rs_power_dbm=request.tx_rs_power_dbm,
                bs_rows=request.bs_rows,
                bs_cols=request.bs_cols,
                bs_pol=request.bs_pol,
                bs_pol_type=request.bs_pol_type,
                elem_v_spacing=request.elem_v_spacing,
                elem_h_spacing=request.elem_h_spacing,
                antenna_pattern=request.antenna_pattern
            )
            
            cell_info = sim.get_cell(cell_idx)
            
            logger.info(f"Added cell {cell_info['cell_name']} to site {request.site_name} sector {request.sector_id} (azimuth: {sector_azimuth}°)")
            
            return {
                "status": "success",
                "cell_idx": cell_idx,
                "cell_name": cell_info['cell_name'],
                "site_name": request.site_name,
                "sector_id": request.sector_id,
                "band": request.band,
                "fc_hz": request.fc_hz,
                "tilt_deg": request.tilt_deg,
                "sector_azimuth": sector_azimuth,
                "is_first_cell_on_sector": is_first_cell_on_sector,
                "existing_bands_on_sector": existing_bands + [request.band]
            }
            
        except ValueError as e:
            # Catches duplicate cell name errors and validation errors
            logger.error(f"Validation error adding cell: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error adding cell: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to add cell: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)