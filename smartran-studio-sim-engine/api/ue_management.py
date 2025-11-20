"""
UE Management Module for CNS Sionna Simulation

Provides UE query and drop/redrop capabilities.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


class UEDropRequest(BaseModel):
    """
    Request to drop/redrop UEs in the simulation.
    
    WARNING: This REPLACES all existing UEs!
    """
    num_ue: int = Field(..., ge=1, description="Number of UEs to drop")
    layout: str = Field("box", description="Layout type: 'disk' or 'box'")
    center_x: Optional[float] = Field(None, description="Center X coordinate (defaults to site mean)")
    center_y: Optional[float] = Field(None, description="Center Y coordinate (defaults to site mean)")
    radius_m: float = Field(500.0, gt=0, description="Radius in meters (for disk layout)")
    box_pad_m: float = Field(500.0, gt=0, description="Padding around sites in meters (for box layout)")
    height_m: float = Field(1.5, gt=0, description="UE height in meters")
    seed: int = Field(7, description="Random seed for reproducibility")
    
    class Config:
        schema_extra = {
            "examples": [
                {
                    "num_ue": 30000,
                    "layout": "box",
                    "box_pad_m": 250.0,
                    "height_m": 1.5,
                    "seed": 7
                },
                {
                    "num_ue": 10000,
                    "layout": "disk",
                    "center_x": 0.0,
                    "center_y": 0.0,
                    "radius_m": 1000.0,
                    "seed": 42
                }
            ]
        }


def get_ue_info(sim) -> Dict[str, Any]:
    """
    Get information about the current UE drop.
    
    Args:
        sim: MultiCellSim instance
        
    Returns:
        Dictionary with:
            - num_ues: Current number of UEs
            - layout: Drop layout type
            - drop_params: Parameters used for last drop
            - has_results: Whether compute() has been run
            - results: (if has_results) Info about computed RSRP
    """
    return sim.get_ue_info()


def drop_ues(sim, request: UEDropRequest) -> Dict[str, Any]:
    """
    Drop or re-drop UEs in the simulation.
    
    WARNING: This REPLACES all existing UEs! Previous compute() results
    for UEs will be invalidated.
    
    Args:
        sim: MultiCellSim instance
        request: UEDropRequest with drop parameters
        
    Returns:
        Dictionary with:
            - num_ues: Number of UEs dropped
            - drop_params: Parameters used
            - message: Success message
            
    Raises:
        ValueError: If layout is invalid
        
    Example:
        >>> request = UEDropRequest(num_ue=50000, layout="box", box_pad_m=250.0)
        >>> result = drop_ues(sim, request)
        >>> print(f"Dropped {result['num_ues']} UEs")
    """
    # Validate layout
    if request.layout not in ['disk', 'box']:
        raise ValueError(f"layout must be 'disk' or 'box', got '{request.layout}'")
    
    # Build center parameter
    center = None
    if request.center_x is not None and request.center_y is not None:
        center = (request.center_x, request.center_y)
    
    # Drop UEs
    logger.info(f"Dropping {request.num_ue} UEs with layout='{request.layout}'")
    sim.drop_ues(
        num_ue=request.num_ue,
        layout=request.layout,
        center=center,
        radius_m=request.radius_m,
        box_pad_m=request.box_pad_m,
        height_m=request.height_m,
        seed=request.seed
    )
    
    # Get updated info
    ue_info = sim.get_ue_info()
    
    logger.info(f"Successfully dropped {ue_info['num_ues']} UEs")
    
    return {
        "num_ues": ue_info['num_ues'],
        "drop_params": ue_info['drop_params'],
        "message": f"Successfully dropped {ue_info['num_ues']} UEs. Call /measurement-reports to compute new RSRP.",
    }

