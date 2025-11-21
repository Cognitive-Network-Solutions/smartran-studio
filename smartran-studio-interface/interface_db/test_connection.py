"""
Test script to verify ArangoDB connection and basic operations.

This script reads credentials from environment variables (as configured in compose.yaml).
Run after starting the ArangoDB container.

Usage:
    # With docker compose environment variables
    docker compose exec backend python /path/to/test_connection.py
    
    # Or set environment variables manually
    export ARANGO_HOST=http://localhost:8529
    export ARANGO_USERNAME=root
    export ARANGO_PASSWORD=your_password
    export ARANGO_DATABASE=smartran-studio_db
    python test_connection.py
"""

from arango import ArangoClient
from arango.exceptions import DatabaseCreateError
import os
import sys

# Read configuration from environment variables (NO HARDCODED CREDENTIALS)
ARANGO_HOST = os.getenv('ARANGO_HOST', 'http://localhost:8529')
ARANGO_USER = os.getenv('ARANGO_USERNAME')
ARANGO_PASSWORD = os.getenv('ARANGO_PASSWORD')
ARANGO_DATABASE = os.getenv('ARANGO_DATABASE', 'smartran-studio_db')

# Validate required environment variables
if not ARANGO_USER:
    print("❌ Error: ARANGO_USERNAME environment variable is required")
    print("Set it in your shell or run via docker compose exec")
    sys.exit(1)

if not ARANGO_PASSWORD:
    print("❌ Error: ARANGO_PASSWORD environment variable is required")
    print("This should match the password configured in compose.yaml")
    sys.exit(1)

def test_connection():
    """Test basic connection and operations"""
    
    print("=" * 60)
    print("SmartRAN Studio - ArangoDB Connection Test")
    print("=" * 60)
    print(f"Host: {ARANGO_HOST}")
    print(f"User: {ARANGO_USER}")
    print(f"Database: {ARANGO_DATABASE}")
    print("=" * 60)
    
    print("\n🔗 Connecting to ArangoDB...")
    client = ArangoClient(hosts=ARANGO_HOST)
    
    try:
        # Connect to system database
        sys_db = client.db('_system', username=ARANGO_USER, password=ARANGO_PASSWORD)
        print("✅ Connected to ArangoDB")
        
        # Check version
        version = sys_db.version()
        print(f"📦 ArangoDB Version: {version}")
        
        # Check/create SmartRAN Studio database
        if not sys_db.has_database(ARANGO_DATABASE):
            sys_db.create_database(ARANGO_DATABASE)
            print(f"✅ Created database: {ARANGO_DATABASE}")
        else:
            print(f"✅ Database exists: {ARANGO_DATABASE}")
        
        # Connect to SmartRAN Studio database
        app_db = client.db(ARANGO_DATABASE, username=ARANGO_USER, password=ARANGO_PASSWORD)
        
        # Create a test collection
        test_collection_name = 'connection_test'
        if not app_db.has_collection(test_collection_name):
            collection = app_db.create_collection(test_collection_name)
            print(f"✅ Created test collection: {test_collection_name}")
        else:
            collection = app_db.collection(test_collection_name)
            print(f"✅ Test collection exists: {test_collection_name}")
        
        # Insert a test document
        test_doc = {
            'type': 'connection_test',
            'message': 'SmartRAN Studio ArangoDB is working!',
            'test_run': 'automated'
        }
        result = collection.insert(test_doc)
        print(f"✅ Inserted test document: {result['_key']}")
        
        # Query the document
        cursor = app_db.aql.execute(
            'FOR doc IN @@collection FILTER doc.type == @type RETURN doc',
            bind_vars={'@collection': test_collection_name, 'type': 'connection_test'}
        )
        docs = list(cursor)
        print(f"✅ Queried {len(docs)} document(s)")
        
        # Clean up test document
        collection.delete(result['_key'])
        print(f"✅ Cleaned up test document")
        
        # Check for SmartRAN Studio collections
        print("\n📋 Checking SmartRAN Studio collections:")
        expected_collections = ['sim_runs', 'sim_reports', 'saved_configs', 'session_cache']
        for coll_name in expected_collections:
            exists = app_db.has_collection(coll_name)
            status = "✅" if exists else "⚠️ "
            print(f"  {status} {coll_name}: {'exists' if exists else 'will be created on first use'}")
        
        print("\n" + "=" * 60)
        print("🎉 All tests passed! ArangoDB is ready for SmartRAN Studio.")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("  1. Ensure ArangoDB container is running: docker ps | grep arangodb")
        print("  2. Check credentials match compose.yaml")
        print("  3. Verify environment variables are set")
        return False
    
    return True

if __name__ == '__main__':
    test_connection()

