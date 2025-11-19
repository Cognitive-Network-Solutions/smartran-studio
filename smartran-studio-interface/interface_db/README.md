# CNS ArangoDB - Data Persistence Layer

ArangoDB instance for CNS protostack data persistence, caching, and state management.

## Quick Start

### 1. Start ArangoDB
```bash
docker compose up -d
```

### 2. Access Web UI
- URL: http://localhost:8529
- Username: `root`
- Password: `cns_dev_password`

### 3. Internal Docker Network Access
From other CNS services (Sionna, Interface):
```
http://cns-arangodb:8529
```

## Configuration

### Default Credentials
- **Root Password**: `cns_dev_password`
- **Auth Enabled**: Yes (`ARANGO_NO_AUTH=0`)

### To Disable Auth (Testing Only)
Edit `compose.yaml`:
```yaml
environment:
  - ARANGO_NO_AUTH=1  # Disables authentication
```

## Data Persistence

Data is stored in Docker volumes:
- `cns_arango_data` - Database files
- `cns_arango_apps` - Application data

Data persists between container restarts.

## Management Commands

```bash
# Start service
docker compose up -d

# Stop service (keeps data)
docker compose down

# View logs
docker compose logs -f

# Stop and remove all data
docker compose down -v  # ⚠️ Deletes all data!

# Restart service
docker compose restart
```

## Network Integration

This service joins the `cns-network` Docker network, allowing:
- CNS Sionna Sim → ArangoDB (internal communication)
- CNS Interface → ArangoDB (internal communication)
- Host → ArangoDB (via localhost:8529)

## Future Integration

This database will support:
1. **Simulation State Persistence** - Save/load network topologies
2. **Measurement Report Caching** - Store compute results for re-analysis
3. **Scenario Management** - Version and compare different network configs
4. **ML Training Data** - Persistent storage for learning pipelines

## Python Client Example

```python
from arango import ArangoClient

# Initialize client
client = ArangoClient(hosts='http://localhost:8529')

# Connect to database
db = client.db('_system', username='root', password='cns_dev_password')

# Create CNS database
if not db.has_database('cns_data'):
    db.create_database('cns_data')

# Use CNS database
cns_db = client.db('cns_data', username='root', password='cns_dev_password')
```

## Port Information

- **8529** - HTTP API and Web UI (exposed to host)
- Internal Docker network communication on same port

## Version

- **ArangoDB**: 3.11 (official image)
- **Docker Compose**: 3.8

