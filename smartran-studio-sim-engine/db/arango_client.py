"""
ArangoDB Database Client for SmartRAN Studio Simulation Engine

Handles database connection initialization with retry logic and automatic
database creation. Used for persisting simulation run results and measurements.

Key Features:
    - Automatic retry on connection failure (handles container startup timing)
    - Database auto-creation if not exists
    - Environment variable configuration for Docker deployment
    - Connection pooling via python-arango client

Environment Variables:
    ARANGO_HOST: Database host URL (default: http://localhost:8529)
    ARANGO_USERNAME: Database username (default: root)
    ARANGO_PASSWORD: Database password (default: empty string)
    ARANGO_DATABASE: Database name (default: smartran-studio_db)

Usage:
    >>> from db.arango_client import init_arango
    >>> db = init_arango()
    >>> collection = db.collection('sim_runs')

Author: Cognitive Network Solutions Inc.
License: Apache 2.0
"""

import os
import time
import logging
from arango import ArangoClient

logger = logging.getLogger(__name__)

# Read configuration from environment (set by Docker Compose)
ARANGO_HOST = os.getenv("ARANGO_HOST", "http://localhost:8529")
ARANGO_USERNAME = os.getenv("ARANGO_USERNAME", "root")
ARANGO_PASSWORD = os.getenv("ARANGO_PASSWORD", "")
ARANGO_DATABASE = os.getenv("ARANGO_DATABASE", "smartran-studio_db")

# Global client instance
client = ArangoClient(hosts=ARANGO_HOST)


def init_arango(max_retries=10, retry_delay=2):
    """
    Initialize ArangoDB connection with automatic retry and database creation.
    
    Implements exponential backoff retry logic to handle Docker container
    startup timing issues. If the database doesn't exist, it's automatically
    created.
    
    This function should be called once during application startup (e.g., in
    FastAPI's startup event handler).
    
    Args:
        max_retries: Maximum number of connection attempts (default: 10)
        retry_delay: Delay in seconds between retries (default: 2)
    
    Returns:
        arango.database.StandardDatabase: Connected database instance
        
    Raises:
        Exception: If connection fails after all retries
        
    Example:
        >>> db = init_arango(max_retries=5, retry_delay=3)
        >>> print(db.name)
        'smartran-studio_db'
        
    Note:
        The function first connects to the _system database to check/create
        the target database, then reconnects to the target database. This
        two-step process ensures the database exists before returning.
        
    Connection Flow:
        1. Connect to _system database with credentials
        2. Check if target database exists
        3. Create database if missing
        4. Reconnect to target database
        5. Return database instance
        
    Docker Integration:
        The function reads connection parameters from environment variables
        which are injected by Docker Compose. This enables container-based
        deployment without code changes.
    """
    for attempt in range(max_retries):
        try:
            # Connect to _system database first
            sys_db = client.db('_system', username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
            
            # Create database if it doesn't exist
            if not sys_db.has_database(ARANGO_DATABASE):
                sys_db.create_database(ARANGO_DATABASE)
                logger.info(f"Created database: {ARANGO_DATABASE}")
            
            # Connect to our database
            db = client.db(ARANGO_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
            logger.info(f"Successfully connected to ArangoDB: {ARANGO_DATABASE}")
            return db
            
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Failed to connect to ArangoDB (attempt {attempt + 1}/{max_retries}): {e}")
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error(f"Failed to connect to ArangoDB after {max_retries} attempts: {e}")
                raise
    
    raise Exception("Failed to initialize ArangoDB connection")
