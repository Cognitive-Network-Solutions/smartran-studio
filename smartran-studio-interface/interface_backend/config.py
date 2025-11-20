"""
Configuration management for SmartRAN Studio CLI Backend
"""
from pathlib import Path
import yaml
import os
from typing import Dict, Any


def load_config() -> Dict[str, Any]:
    """
    Load configuration from environment variables and config.yaml.
    
    Environment Variables (REQUIRED):
        SIONNA_API_URL: URL for simulation engine API (set by Docker Compose)
    
    The API URL MUST come from the SIONNA_API_URL environment variable.
    No default is provided to ensure proper configuration.
    """
    
    # Read from environment variables (REQUIRED - injected by Docker Compose)
    sionna_api_url = os.getenv('SIONNA_API_URL')
    
    if not sionna_api_url:
        raise ValueError(
            "SIONNA_API_URL environment variable is required. "
            "Set this in docker-compose.yaml or your environment."
        )
    
    # Try to load config.yaml for additional settings
    config_path = Path(__file__).parent / "config.yaml"
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            # Override API URL with env var (always use env var, never yaml default)
            if 'networks' in config and 'sim' in config['networks']:
                config['networks']['sim']['api_url'] = sionna_api_url
            return config
    
    # Fallback config using env vars only
    return {
        "networks": {
            "sim": {
                "name": "SmartRAN Studio Simulation",
                "api_url": sionna_api_url,
                "enabled": True
            }
        },
        "default_network": "sim"
    }


# Load configuration on module import
CONFIG = load_config()

