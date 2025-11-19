"""
ArangoDB client for SmartRAN Studio simulation state management.

Manages:
- Session cache (current init config)
- Saved configurations (snapshots of sim state)
"""

from arango import ArangoClient
from datetime import datetime
from typing import Dict, List, Optional
import logging
import os

logger = logging.getLogger(__name__)


class SimStateManager:
    """Manages simulation state in ArangoDB"""
    
    def __init__(self, 
                 host: str = None,
                 username: str = None,
                 password: str = None,
                 database: str = None):
        """Initialize ArangoDB client (reads from env vars if not provided)"""
        # Read from environment variables (injected by Docker Compose)
        host = host or os.getenv('ARANGO_HOST', 'http://smartran-studio-arangodb:8529')
        username = username or os.getenv('ARANGO_USERNAME', 'root')
        password = password or os.getenv('ARANGO_PASSWORD', 'smartran-studio_dev_password')
        database = database or os.getenv('ARANGO_DATABASE', 'smartran-studio_db')
        self.client = ArangoClient(hosts=host)
        
        # Connect to _system database first to check/create our database
        sys_db = self.client.db('_system', username=username, password=password)
        
        # Create database if it doesn't exist
        if not sys_db.has_database(database):
            sys_db.create_database(database)
            logger.info(f"Created database: {database}")
        else:
            logger.info(f"Database {database} already exists")
        
        # Connect to our database
        self.db = self.client.db(database, username=username, password=password)
        logger.info(f"Connected to database: {database}")
        
        # Ensure collections exist
        self._ensure_collections()
    
    def _ensure_collections(self):
        """Create collections if they don't exist"""
        # Session cache - tracks current init config
        if not self.db.has_collection('session_cache'):
            self.db.create_collection('session_cache')
            logger.info("Created collection: session_cache")
        
        # Saved configs - permanent storage
        if not self.db.has_collection('saved_configs'):
            self.db.create_collection('saved_configs')
            logger.info("Created collection: saved_configs")
    
    # ===== Session Cache (Init Config Only) =====
    
    def save_init_config(self, init_config: Dict) -> None:
        """Save initialization config to session cache"""
        collection = self.db.collection('session_cache')
        
        doc = {
            '_key': 'current_init',
            'init_config': init_config,
            'saved_at': datetime.utcnow().isoformat()
        }
        
        collection.insert(doc, overwrite=True)
        logger.info("Saved init config to session cache")
    
    def get_init_config(self) -> Optional[Dict]:
        """Get current init config from session cache"""
        collection = self.db.collection('session_cache')
        doc = collection.get('current_init')
        return doc['init_config'] if doc else None
    
    # ===== Saved Configs (Permanent Snapshots) =====
    
    def save_config(self, 
                   name: str,
                   init_config: Dict,
                   cells_state: List[Dict],
                   ues_state: Dict,
                   topology: Dict,
                   description: str = "") -> Dict:
        """
        Save a complete simulation configuration snapshot.
        
        Args:
            name: Unique config name
            init_config: Initial simulation parameters
            cells_state: Current state of all cells (from Sionna API)
            ues_state: Current UE configuration (from Sionna API)
            topology: Topology metadata (sites, cells count)
            description: User description
        
        Returns:
            Saved config document
        """
        collection = self.db.collection('saved_configs')
        
        config = {
            '_key': name,
            'config_name': name,
            'description': description,
            'init_config': init_config,
            'cells_state': cells_state,  # Full cell state from API
            'ues_state': ues_state,
            'topology': topology,
            'metadata': {
                'created_at': datetime.utcnow().isoformat(),
                'num_cells': len(cells_state),
                'num_sites': topology.get('num_sites', 0),
                'num_ues': ues_state.get('num_ues', 0)
            }
        }
        
        collection.insert(config, overwrite=True)
        logger.info(f"Saved config: {name}")
        
        return config
    
    def load_config(self, name: str) -> Optional[Dict]:
        """Load saved config by name"""
        collection = self.db.collection('saved_configs')
        config = collection.get(name)
        
        if config:
            logger.info(f"Loaded config: {name}")
        else:
            logger.warning(f"Config not found: {name}")
        
        return config
    
    def list_configs(self) -> List[Dict]:
        """List all saved configurations"""
        collection = self.db.collection('saved_configs')
        
        # Get all documents
        configs = []
        for doc in collection.all():
            # Return minimal info for listing
            configs.append({
                'name': doc['config_name'],
                'description': doc.get('description', ''),
                'num_sites': doc['metadata']['num_sites'],
                'num_cells': doc['metadata']['num_cells'],
                'num_ues': doc['metadata']['num_ues'],
                'created_at': doc['metadata']['created_at']
            })
        
        # Sort by creation date (newest first)
        configs.sort(key=lambda x: x['created_at'], reverse=True)
        
        return configs
    
    def delete_config(self, name: str) -> bool:
        """Delete a saved config"""
        collection = self.db.collection('saved_configs')
        
        if collection.has(name):
            collection.delete(name)
            logger.info(f"Deleted config: {name}")
            return True
        else:
            logger.warning(f"Config not found for deletion: {name}")
            return False
    
    def config_exists(self, name: str) -> bool:
        """Check if a config exists"""
        collection = self.db.collection('saved_configs')
        return collection.has(name)


# Global instance
state_manager: Optional[SimStateManager] = None


def get_state_manager() -> SimStateManager:
    """Get or create global state manager instance"""
    global state_manager
    
    if state_manager is None:
        try:
            state_manager = SimStateManager()
        except Exception as e:
            logger.error(f"Failed to initialize ArangoDB: {e}")
            logger.warning("ArangoDB features disabled")
            # Return a dummy manager that does nothing
            return None
    
    return state_manager

