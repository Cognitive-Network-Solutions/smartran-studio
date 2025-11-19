"""
HTTP client for making API requests to connected networks
"""
import httpx
from fastapi import HTTPException
from typing import Optional, Dict, Any
from session import session


async def api_request(
    method: str, 
    endpoint: str, 
    data: Optional[Dict] = None, 
    params: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Make HTTP request to connected network API
    
    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint path
        data: JSON data for POST requests
        params: Query parameters
        
    Returns:
        JSON response from API
        
    Raises:
        HTTPException: If request fails
    """
    base_url = session.get_api_url()
    url = f"{base_url}{endpoint}"
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            if method.upper() == "GET":
                response = await client.get(url, params=params)
            elif method.upper() == "POST":
                response = await client.post(url, json=data, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f"API request failed: {str(e)}")

