"""
Simulation Initialization Module for SmartRAN Studio Simulation

Provides on-demand initialization with configurable parameters.
"""

from typing import Optional
from pydantic import BaseModel, Field
import logging
from simulation.helpers import add_site_with_dualband_cells, iter_clustered_sites
from simulation.engine import MultiCellSim

logger = logging.getLogger(__name__)


class SimInitializationRequest(BaseModel):
    """
    Request to initialize the simulation with custom configuration.
    
    All parameters have sensible defaults - only specify what you want to change.
    """
    
    # Site layout
    n_sites: int = Field(10, ge=0, description="Number of sites to create (0 for manual placement)")
    spacing: float = Field(500.0, gt=0, description="Target inter-site spacing in meters")
    seed: int = Field(7, description="Random seed (used for both site placement and UE drop)")
    jitter: float = Field(0.06, ge=0.0, le=1.0, description="Site position jitter (fraction of spacing)")
    
    # Site configuration
    site_height_m: float = Field(20.0, gt=0, description="Site height in meters")
    
    # High band configuration
    fc_hi_hz: float = Field(2500e6, gt=0, description="High band frequency in Hz (default: 2.5 GHz)")
    tilt_hi_deg: float = Field(9.0, description="High band tilt in degrees")
    bs_rows_hi: int = Field(8, ge=1, description="High band antenna rows")
    bs_cols_hi: int = Field(1, ge=1, description="High band antenna columns")
    antenna_pattern_hi: str = Field("38.901", description="High band antenna pattern")
    
    # Low band configuration
    fc_lo_hz: float = Field(600e6, gt=0, description="Low band frequency in Hz (default: 600 MHz)")
    tilt_lo_deg: float = Field(9.0, description="Low band tilt in degrees")
    bs_rows_lo: int = Field(8, ge=1, description="Low band antenna rows")
    bs_cols_lo: int = Field(1, ge=1, description="Low band antenna columns")
    antenna_pattern_lo: str = Field("38.901", description="Low band antenna pattern")
    
    # UE configuration
    num_ue: int = Field(30000, ge=1, description="Number of UEs to drop")
    box_pad_m: float = Field(250.0, gt=0, description="Box padding around sites in meters")
    
    # Chunking (optional, for memory management)
    cells_chunk: Optional[int] = Field(48, ge=1, description="Cell chunk size for compute")
    ue_chunk: Optional[int] = Field(500, ge=1, description="UE chunk size for compute")
    
    class Config:
        schema_extra = {
            "examples": [
                {
                    "n_sites": 10,
                    "spacing": 500.0,
                    "seed": 7,
                    "fc_hi_hz": 2500e6,
                    "fc_lo_hz": 600e6,
                    "num_ue": 30000,
                    "box_pad_m": 250.0
                },
                {
                    "n_sites": 20,
                    "spacing": 600.0,
                    "seed": 42,
                    "site_height_m": 25.0,
                    "tilt_hi_deg": 12.0,
                    "tilt_lo_deg": 10.0,
                    "num_ue": 50000
                },
                {
                    "n_sites": 5,
                    "fc_hi_hz": 3500e6,
                    "bs_rows_hi": 4,
                    "bs_cols_hi": 2,
                    "fc_lo_hz": 700e6,
                    "bs_rows_lo": 8,
                    "bs_cols_lo": 1,
                    "num_ue": 10000
                }
            ]
        }


def initialize_simulation(config: SimInitializationRequest) -> dict:
    """
    Initialize a new simulation with the given configuration.
    
    Args:
        config: SimInitializationRequest with initialization parameters
        
    Returns:
        Dictionary with:
            - sim: The initialized MultiCellSim object
            - num_sites: Number of sites created
            - num_cells: Number of cells created
            - num_ues: Number of UEs dropped
            - config_summary: Summary of configuration used
            
    Example:
        >>> config = SimInitializationRequest(n_sites=10, num_ue=30000)
        >>> result = initialize_simulation(config)
        >>> sim = result['sim']
    """
    logger.info("Initializing simulation with custom configuration...")
    
    # 0) Instantiate simulation object
    # NOTE: These are fixed - not configurable via endpoint
    sim = MultiCellSim(bs_rows=8, bs_cols=1, fft_size=32)
    
    # 1) Configure naming convention (fixed)
    sim.configure_naming(use_site='id', sector_mode='1based', pattern='{band}{site}{sector}')
    
    # 2) Add sites with dual-band cells
    logger.info(f"Creating {config.n_sites} sites with spacing={config.spacing}m, seed={config.seed}")
    
    for idx, (x, y, az0) in enumerate(
        iter_clustered_sites(
            n_sites=config.n_sites,
            spacing=config.spacing,
            center=(0.0, 0.0),
            jitter=config.jitter,
            seed=config.seed
        ),
        start=1
    ):
        site_name = f"SITE{idx:04d}A"
        
        add_site_with_dualband_cells(
            sim,
            site_name=site_name,
            x=x, y=y,
            height_m=config.site_height_m,
            az0_deg=az0,
            # High band (configurable)
            fc_hi_hz=config.fc_hi_hz,
            band_hi="H",  # Fixed
            tilt_hi_deg=config.tilt_hi_deg,
            pwr_hi_dbm=0.0,  # Fixed
            bs_rows_hi=config.bs_rows_hi,
            bs_cols_hi=config.bs_cols_hi,
            antenna_pattern_hi=config.antenna_pattern_hi,
            # Low band (configurable)
            fc_lo_hz=config.fc_lo_hz,
            band_lo="L",  # Fixed
            tilt_lo_deg=config.tilt_lo_deg,
            pwr_lo_dbm=0.0,  # Fixed
            bs_rows_lo=config.bs_rows_lo,
            bs_cols_lo=config.bs_cols_lo,
            antenna_pattern_lo=config.antenna_pattern_lo,
            order="hi_lo",  # Fixed
        )
    
    # 3) Drop UEs (using same seed)
    logger.info(f"Dropping {config.num_ue} UEs with box_pad_m={config.box_pad_m}, seed={config.seed}")
    sim.drop_ues(
        num_ue=config.num_ue,
        layout='box',
        box_pad_m=config.box_pad_m,
        seed=config.seed
    )
    
    # 4) Set chunking parameters
    sim.cells_chunk = config.cells_chunk
    sim.ue_chunk = config.ue_chunk
    
    # Get counts
    num_sites = len(sim.sites)
    num_cells = len(sim.cells)
    num_ues = sim.ue_loc.shape[1] if sim.ue_loc is not None else 0
    num_hi_cells = len([c for c in sim.cells if c['fc_hz'] == config.fc_hi_hz])
    num_lo_cells = len([c for c in sim.cells if c['fc_hz'] == config.fc_lo_hz])
    
    logger.info(f"Simulation initialized successfully:")
    logger.info(f"  - Sites: {num_sites}")
    logger.info(f"  - Cells: {num_cells} (High band: {num_hi_cells}, Low band: {num_lo_cells})")
    logger.info(f"  - UEs: {num_ues}")
    logger.info(f"  - Chunk sizes: cells_chunk={sim.cells_chunk}, ue_chunk={sim.ue_chunk}")
    
    return {
        "sim": sim,
        "num_sites": num_sites,
        "num_cells": num_cells,
        "num_ues": num_ues,
        "num_hi_cells": num_hi_cells,
        "num_lo_cells": num_lo_cells,
        "config_summary": {
            "n_sites": config.n_sites,
            "spacing_m": config.spacing,
            "seed": config.seed,
            "site_height_m": config.site_height_m,
            "high_band": {
                "fc_hz": config.fc_hi_hz,
                "fc_ghz": config.fc_hi_hz / 1e9,
                "tilt_deg": config.tilt_hi_deg,
                "antenna": f"{config.bs_rows_hi}x{config.bs_cols_hi}",
                "pattern": config.antenna_pattern_hi,
            },
            "low_band": {
                "fc_hz": config.fc_lo_hz,
                "fc_ghz": config.fc_lo_hz / 1e9,
                "tilt_deg": config.tilt_lo_deg,
                "antenna": f"{config.bs_rows_lo}x{config.bs_cols_lo}",
                "pattern": config.antenna_pattern_lo,
            },
            "ues": {
                "num_ue": config.num_ue,
                "box_pad_m": config.box_pad_m,
            },
            "chunking": {
                "cells_chunk": config.cells_chunk,
                "ue_chunk": config.ue_chunk,
            }
        }
    }

