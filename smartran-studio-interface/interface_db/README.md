# Database - ArangoDB

Persistent storage for SmartRAN Studio simulation state and configurations.

## Technology

**ArangoDB 3.11** - Multi-model NoSQL database

## Purpose

Stores:
- Simulation configurations (save/load)
- Measurement snapshots (compute results)
- Session state (current initialization)
- Run metadata

---

## 📖 Complete Documentation

**For comprehensive database schema documentation, query examples, and data extraction guides, see:**

👉 **[Database Schema Reference](../../docs/DATABASE_SCHEMA.md)**

This includes:
- Complete document structures for all collections
- 20+ AQL query examples
- Python access examples with pandas
- Data export strategies (JSON, CSV)
- Storage estimates and performance metrics

---

## Collections Overview

### `session_cache`

Current simulation state:
- Single document with key `current_init`
- Stores active initialization parameters
- Overwritten on each init

### `saved_configs`

User-saved simulation configurations:
- Named snapshots of full simulation state
- Includes init params, cell configs, UE distribution
- Restorable via `srs config load`

**Document Structure**:
```json
{
  "_key": "baseline",
  "config_name": "baseline",
  "description": "Baseline configuration",
  "init_config": {...},
  "cells_state": [...],
  "ues_state": {...},
  "topology": {...},
  "metadata": {
    "created_at": "2025-11-18T10:30:00Z",
    "num_sites": 10,
    "num_cells": 60,
    "num_ues": 30000
  }
}
```

### `sim_runs`

Simulation compute run metadata (one document per run):
- Snapshot ID, name, timestamp
- Complete initialization configuration
- Full cell states snapshot at run time
- Run parameters and statistics

**See [Database Schema Reference](../../docs/DATABASE_SCHEMA.md#1-sim_runs-collection)** for complete document structure.

### `sim_reports`

Per-UE RSRP measurement data (one document per UE per run):
- UE coordinates (x, y)
- Sparse RSRP readings (cell name → dBm)
- Linked to `sim_runs` via `run_id`
- Optimized storage (only cells above threshold)

**See [Database Schema Reference](../../docs/DATABASE_SCHEMA.md#2-sim_reports-collection)** for complete document structure and query examples.

## Access

### Web UI

http://localhost:8529

**Default Credentials (Development Only)**:
- Username: `root`
- Password: `smartran-studio_dev_password`

⚠️ **Change these credentials for any deployment beyond local testing!**  
See **[Configuration Guide](../../docs/CONFIGURATION.md)** for instructions.

### API

```bash
# List databases
curl http://localhost:8529/_api/database

# Query collection
curl -u root:smartran-studio_dev_password \
  http://localhost:8529/_db/smartran-studio_db/_api/document/saved_configs
```

## Docker Configuration

From `docker-compose.yaml`:

```yaml
smartran-studio-arangodb:
  image: arangodb:3.11
  container_name: smartran-studio-arangodb
  ports:
    - "8529:8529"
  volumes:
    - arango_data:/var/lib/arangodb3
    - arango_apps:/var/lib/arangodb3-apps
  environment:
    - ARANGO_ROOT_PASSWORD=smartran-studio_dev_password
    - ARANGO_NO_AUTH=0
```

## Volumes

- `arango_data` - Database files
- `arango_apps` - Foxx apps

Persistent across container restarts.

## Python Client

Both backend and sim-engine use `python-arango`:

```python
from arango import ArangoClient
import os

# Credentials come from environment variables (set in compose.yaml)
client = ArangoClient(hosts=os.getenv('ARANGO_HOST'))
db = client.db(
    os.getenv('ARANGO_DATABASE'),
    username=os.getenv('ARANGO_USERNAME'),
    password=os.getenv('ARANGO_PASSWORD')
)

# Query
configs = db.collection('saved_configs').all()

# Insert
db.collection('saved_configs').insert({'_key': 'test', ...})
```

For detailed query examples and data extraction patterns, see:  
**[Database Schema Reference](../../docs/DATABASE_SCHEMA.md#python-access-examples)**

## Testing Connection

```bash
cd interface_db
python test_connection.py
```

## Backup

### Export Database

```bash
docker exec smartran-studio-arangodb arangodump \
  --server.database smartran-studio_db \
  --output-directory /backup

docker cp smartran-studio-arangodb:/backup ./backup
```

### Restore Database

```bash
docker cp ./backup smartran-studio-arangodb:/backup

docker exec smartran-studio-arangodb arangorestore \
  --server.database smartran-studio_db \
  --input-directory /backup
```

## Production Recommendations

1. **Change default password** - See **[Configuration Guide](../../docs/CONFIGURATION.md)**
2. **Enable authentication** (already enabled with `ARANGO_NO_AUTH=0`)
3. **Configure backups** (regular dumps via `arangodump`)
4. **Use volumes** on dedicated storage
5. **Monitor performance** (built-in web UI metrics at port 8529)
6. **Secure network** access (firewall rules, don't expose 8529 publicly)

For complete security best practices and credential management, see:
- **[Configuration Guide](../../docs/CONFIGURATION.md)** - How to change passwords
- **[Database Schema Reference](../../docs/DATABASE_SCHEMA.md)** - Backup strategies

## Troubleshooting

### Cannot Connect

Check container is running:
```bash
docker ps | grep arangodb
```

Check logs:
```bash
docker logs smartran-studio-arangodb
```

### Permission Errors

Ensure volumes have correct ownership:
```bash
docker-compose down
docker volume rm smartran_arango_data smartran_arango_apps
docker-compose up -d
```

### Database Full

Clean old snapshots:
```bash
srs snapshot list
srs snapshot delete <old-snapshot-id>
```

## License

See main repository LICENSE file.
