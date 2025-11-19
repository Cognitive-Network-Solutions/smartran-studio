# db/arango_client.py
import os
import time
import logging
from arango import ArangoClient

logger = logging.getLogger(__name__)

ARANGO_HOST = os.getenv("ARANGO_HOST", "http://localhost:8529")
ARANGO_USERNAME = os.getenv("ARANGO_USERNAME", "root")
ARANGO_PASSWORD = os.getenv("ARANGO_PASSWORD", "")
ARANGO_DATABASE = os.getenv("ARANGO_DATABASE", "smartran-studio_db")

client = ArangoClient(hosts=ARANGO_HOST)

# Call this once on startup
def init_arango(max_retries=10, retry_delay=2):
    """
    Initialize ArangoDB connection with retry logic.
    Creates database if it doesn't exist.
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
