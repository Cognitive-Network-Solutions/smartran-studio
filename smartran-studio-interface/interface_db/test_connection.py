"""
Simple test script to verify ArangoDB connection and basic operations
Run after starting the ArangoDB container
"""

from arango import ArangoClient
from arango.exceptions import DatabaseCreateError

# Configuration
ARANGO_HOST = 'http://localhost:8529'
ARANGO_USER = 'root'
ARANGO_PASSWORD = 'cns_dev_password'

def test_connection():
    """Test basic connection and operations"""
    
    print("🔗 Connecting to ArangoDB...")
    client = ArangoClient(hosts=ARANGO_HOST)
    
    try:
        # Connect to system database
        sys_db = client.db('_system', username=ARANGO_USER, password=ARANGO_PASSWORD)
        print("✅ Connected to ArangoDB")
        
        # Check version
        version = sys_db.version()
        print(f"📦 ArangoDB Version: {version}")
        
        # Create CNS database if it doesn't exist
        cns_db_name = 'cns_data'
        if not sys_db.has_database(cns_db_name):
            sys_db.create_database(cns_db_name)
            print(f"✅ Created database: {cns_db_name}")
        else:
            print(f"✅ Database exists: {cns_db_name}")
        
        # Connect to CNS database
        cns_db = client.db(cns_db_name, username=ARANGO_USER, password=ARANGO_PASSWORD)
        
        # Create a test collection
        test_collection_name = 'test_collection'
        if not cns_db.has_collection(test_collection_name):
            collection = cns_db.create_collection(test_collection_name)
            print(f"✅ Created collection: {test_collection_name}")
        else:
            collection = cns_db.collection(test_collection_name)
            print(f"✅ Collection exists: {test_collection_name}")
        
        # Insert a test document
        test_doc = {
            'type': 'connection_test',
            'message': 'CNS ArangoDB is working!',
            'timestamp': '2025-01-01T00:00:00Z'
        }
        result = collection.insert(test_doc)
        print(f"✅ Inserted test document: {result['_key']}")
        
        # Query the document
        cursor = cns_db.aql.execute(
            'FOR doc IN @@collection FILTER doc.type == @type RETURN doc',
            bind_vars={'@collection': test_collection_name, 'type': 'connection_test'}
        )
        docs = list(cursor)
        print(f"✅ Queried {len(docs)} document(s)")
        
        # Clean up test document
        collection.delete(result['_key'])
        print(f"✅ Cleaned up test document")
        
        print("\n🎉 All tests passed! ArangoDB is ready for CNS integration.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == '__main__':
    test_connection()

