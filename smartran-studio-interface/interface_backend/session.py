"""
Session state management for CNS CLI Backend
"""
from typing import Dict, Any
from config import CONFIG


class SessionState:
    """Manage CLI session state (connection context, interactive modes, etc.)"""
    
    def __init__(self):
        self.connected_network = CONFIG.get("default_network", "sim")
        self.init_config = {}  # Store partial init config during interactive setup
        self.init_mode = False  # Track if we're in interactive init mode
        self.init_step = 0  # Current step in init process
        
    def get_network_config(self) -> Dict[str, Any]:
        """Get current network configuration"""
        network = self.connected_network
        if network not in CONFIG["networks"]:
            raise ValueError(f"Network '{network}' not found in configuration")
        return CONFIG["networks"][network]
    
    def get_api_url(self) -> str:
        """Get API URL for current network"""
        return self.get_network_config()["api_url"]
    
    def start_init_wizard(self):
        """Start interactive initialization wizard"""
        self.init_mode = True
        self.init_step = 0
        self.init_config = {}
    
    def end_init_wizard(self):
        """End interactive initialization wizard"""
        self.init_mode = False
        self.init_step = 0
        self.init_config = {}


# Global session state (in production, use proper session management)
session = SessionState()

