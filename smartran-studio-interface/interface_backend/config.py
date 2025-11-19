"""
Configuration management for SmartRAN Studio CLI Backend
"""
from pathlib import Path
import yaml
import os
from typing import Dict, Any


def load_config() -> Dict[str, Any]:
    """Load configuration from environment variables and config.yaml"""
    
    # Read from environment variables (injected by Docker Compose)
    sionna_api_url = os.getenv('SIONNA_API_URL', 'http://smartran-studio-engine:8000')
    
    # Try to load config.yaml for additional settings
    config_path = Path(__file__).parent / "config.yaml"
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            # Override API URL with env var if present
            if 'networks' in config and 'sim' in config['networks']:
                config['networks']['sim']['api_url'] = sionna_api_url
            return config
    
    # Fallback config using env vars
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

