"""
Pydantic models for SmartRAN Studio CLI Backend API
"""
from pydantic import BaseModel
from typing import Optional, Dict, Any


class CommandRequest(BaseModel):
    """Request model for command execution"""
    command: str
    args: Optional[list[str]] = []


class APICommandResponse(BaseModel):
    """API response model for command execution (sent to frontend)"""
    result: str
    exit_code: int = 0
    data: Optional[Dict[str, Any]] = None

