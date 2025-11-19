"""
Response type system for CLI framework

Defines structured response types that can be rendered differently
on the frontend based on their type.
"""
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel


class ResponseType(str, Enum):
    """Types of responses the CLI can return"""
    TEXT = "text"              # Plain text output
    TABLE = "table"            # Tabular data
    JSON = "json"              # JSON data (pretty printed)
    LIST = "list"              # Bullet/numbered list
    CHART = "chart"            # Chart/graph data
    INTERACTIVE = "interactive" # Interactive prompt/wizard
    ERROR = "error"            # Error message
    SUCCESS = "success"        # Success message with icon
    INFO = "info"              # Info message with icon
    WARNING = "warning"        # Warning message with icon
    PROGRESS = "progress"      # Progress indicator
    CODE = "code"              # Code block with syntax highlighting


class TableData(BaseModel):
    """Structured table data"""
    headers: List[str]
    rows: List[List[Any]]
    title: Optional[str] = None
    footer: Optional[str] = None


class ChartData(BaseModel):
    """Chart/visualization data"""
    chart_type: str  # 'bar', 'line', 'pie', 'scatter'
    data: Dict[str, Any]
    title: Optional[str] = None
    x_label: Optional[str] = None
    y_label: Optional[str] = None


class InteractivePrompt(BaseModel):
    """Interactive prompt data"""
    prompt_type: str  # 'input', 'select', 'multiselect', 'confirm'
    message: str
    options: Optional[List[str]] = None
    default: Optional[Any] = None


class CommandResponse(BaseModel):
    """Enhanced response model with type system"""
    # Primary content
    content: Any  # Can be string, TableData, ChartData, etc.
    response_type: ResponseType = ResponseType.TEXT
    
    # Metadata
    exit_code: int = 0
    metadata: Optional[Dict[str, Any]] = None
    
    # Additional content sections
    header: Optional[str] = None
    footer: Optional[str] = None
    
    # UI hints
    scroll_to: Optional[str] = None  # 'top', 'bottom', 'element_id'
    clear_before: bool = False


class CommandError(Exception):
    """Exception for command errors with structured data"""
    def __init__(self, message: str, suggestions: List[str] = None):
        self.message = message
        self.suggestions = suggestions or []
        super().__init__(message)

