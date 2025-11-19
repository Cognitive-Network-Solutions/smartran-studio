# db/arango_client.py
import os
from arango import ArangoClient

ARANGO_HOST = os.getenv("ARANGO_HOST", "http://localhost:8529")
ARANGO_USERNAME = os.getenv("ARANGO_USERNAME", "root")
ARANGO_PASSWORD = os.getenv("ARANGO_PASSWORD", "")
ARANGO_DATABASE = os.getenv("ARANGO_DATABASE", "_system")

client = ArangoClient(hosts=ARANGO_HOST)

# Call this once on startup
def init_arango():
    db = client.db(
        ARANGO_DATABASE,
        username=ARANGO_USERNAME,
        password=ARANGO_PASSWORD
    )
    return db
