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

## Collections

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

Simulation compute run metadata:
- Snapshot ID, name, timestamp
- Run parameters
- Statistics

### `sim_reports`

RSRP measurement data:
- Full measurement reports
- UE-cell RSRP values
- Large documents (can be multi-MB)

## Access

### Web UI

http://localhost:8529

**Credentials**:
- Username: `root`
- Password: `smartran-studio_dev_password`

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

client = ArangoClient(hosts='http://smartran-studio-arangodb:8529')
db = client.db('smartran-studio_db', username='root', password='...')

# Query
configs = db.collection('saved_configs').all()

# Insert
db.collection('saved_configs').insert({'_key': 'test', ...})
```

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

1. **Change default password** in `docker-compose.yaml`
2. **Enable authentication** (remove `ARANGO_NO_AUTH` or set to 1)
3. **Configure backups** (regular dumps)
4. **Use volumes** on dedicated storage
5. **Monitor performance** (built-in web UI metrics)
6. **Secure network** access (firewall rules)

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
