# Configuration Guide

SmartRAN Studio is designed for secure, customizable deployments. All credentials, database names, and service URLs are configured via environment variables in `compose.yaml` - **no hardcoded defaults in the application code**.

---

## Quick Configuration

All configuration happens in **one place**: `compose.yaml` in the repository root.

### Essential Configuration

**IMPORTANT:** The default credentials are for **development only**. For any deployment beyond local testing, you **must** customize these values.

---

## Configuration Sections

### 1. Database Credentials

Located in the `smartran-studio-arangodb` service section:

```yaml
services:
  smartran-studio-arangodb:
    environment:
      - ARANGO_ROOT_PASSWORD=smartran-studio_dev_password  # CHANGE THIS!
      - ARANGO_NO_AUTH=0
```

**Required Changes for Production:**

1. **Change the password** to a strong, unique value:
   ```yaml
   - ARANGO_ROOT_PASSWORD=your_secure_password_here
   ```

2. **Update all other services** to use the same password:
   - `smartran-studio-sim-engine` → `ARANGO_PASSWORD`
   - `backend` → `ARANGO_PASSWORD`

**Security Note:** All three services MUST use the same password. The code validates that credentials are provided via environment variables and will refuse to start with missing values.

---

### 2. Database Name (Optional)

Default database name is `smartran-studio_db`. To customize:

```yaml
# In smartran-studio-arangodb service:
environment:
  - ARANGO_ROOT_PASSWORD=your_password
  # Database is auto-created on first connection

# In smartran-studio-sim-engine service:
environment:
  - ARANGO_DATABASE=your_custom_db_name  # Change this

# In backend service:
environment:
  - ARANGO_DATABASE=your_custom_db_name  # Must match above
```

**Note:** All services must use the **same database name**.

---

### 3. Service Names (Advanced)

If you want to rename services (e.g., for multi-tenant deployments), update these references:

```yaml
# 1. Rename the service
services:
  my-custom-sim-engine:  # Changed from smartran-studio-sim-engine
    container_name: my-custom-sim-engine
    # ... rest of config

  # 2. Update references in other services
  backend:
    environment:
      - SIONNA_API_URL=http://my-custom-sim-engine:8000  # Updated
      - ARANGO_HOST=http://my-custom-arangodb:8529  # If you renamed this too
```

---

## Configuration Validation

The application **validates** that all required environment variables are provided at startup. If any are missing, you'll see clear error messages:

```
ValueError: ARANGO_PASSWORD environment variable is required (set in compose.yaml)
ValueError: SIONNA_API_URL environment variable is required
```

This ensures:
- ✅ No hardcoded credentials in code
- ✅ Explicit configuration required
- ✅ Clear error messages if misconfigured
- ✅ Easy to customize for different environments

---

## Environment Variables Reference

### Database Configuration (3 services)

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `ARANGO_HOST` | Yes | Database service URL | `http://smartran-studio-arangodb:8529` |
| `ARANGO_USERNAME` | Yes | Database username | `root` |
| `ARANGO_PASSWORD` | Yes | Database password | `your_secure_password` |
| `ARANGO_DATABASE` | Yes | Database name | `smartran-studio_db` |

**Used by:**
- `smartran-studio-sim-engine`
- `backend`

**Set in `smartran-studio-arangodb`:**
- `ARANGO_ROOT_PASSWORD` (must match `ARANGO_PASSWORD` in other services)

### API Routing (backend only)

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `SIONNA_API_URL` | Yes | Simulation engine API URL | `http://smartran-studio-sim-engine:8000` |

**Used by:** `backend`

### GPU Configuration (sim-engine only)

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `CUDA_VISIBLE_DEVICES` | No | GPU device to use | `0` (first GPU) |
| `RAPIDS_NO_INITIALIZE` | No | Skip RAPIDS auto-init | `1` |

---

## Common Configuration Scenarios

### Scenario 1: Change Database Password

```yaml
# 1. Update arangodb service
smartran-studio-arangodb:
  environment:
    - ARANGO_ROOT_PASSWORD=MySecurePassword123!

# 2. Update sim-engine service
smartran-studio-sim-engine:
  environment:
    - ARANGO_PASSWORD=MySecurePassword123!  # Must match!

# 3. Update backend service
backend:
  environment:
    - ARANGO_PASSWORD=MySecurePassword123!  # Must match!
```

### Scenario 2: Multiple Deployments on Same Host

Use different ports and service names:

```yaml
# Instance 1 (default)
services:
  smartran-studio-arangodb:
    ports:
      - "8529:8529"
  smartran-studio-sim-engine:
    ports:
      - "8000:8000"
  backend:
    ports:
      - "8001:8001"
  frontend:
    ports:
      - "8080:80"

# Instance 2 (separate compose file)
services:
  smartran-studio-arangodb-2:
    ports:
      - "8539:8529"  # Different external port
  smartran-studio-sim-engine-2:
    ports:
      - "8010:8000"  # Different external port
  backend-2:
    ports:
      - "8011:8001"  # Different external port
  frontend-2:
    ports:
      - "8090:80"  # Different external port
```

### Scenario 3: Custom Database Name

```yaml
# All three services need the same database name
smartran-studio-sim-engine:
  environment:
    - ARANGO_DATABASE=my_project_db

backend:
  environment:
    - ARANGO_DATABASE=my_project_db
```

The database will be **auto-created** on first connection if it doesn't exist.

---

## Security Best Practices

### ✅ DO:
1. **Change the default password** before any non-local deployment
2. **Use strong passwords** (20+ characters, mixed case, numbers, symbols)
3. **Keep credentials in compose.yaml** (not in code, not in git)
4. **Use environment-specific compose files** (e.g., `compose.prod.yaml`)
5. **Restrict port access** using firewall rules if exposing to network
6. **Use Docker secrets** for production deployments
7. **Regularly rotate passwords** (requires updating all 3 services)

### ❌ DON'T:
1. **Don't commit custom passwords to git** (add `compose.prod.yaml` to `.gitignore`)
2. **Don't use default credentials** in production
3. **Don't expose port 8529** (ArangoDB) to public internet without firewall
4. **Don't hardcode credentials** in application code (we've prevented this)
5. **Don't share credentials** across different projects

---

## Production Deployment

For production, create a separate compose file:

```bash
# 1. Copy default compose
cp compose.yaml compose.prod.yaml

# 2. Edit with production credentials
nano compose.prod.yaml

# 3. Add to .gitignore
echo "compose.prod.yaml" >> .gitignore

# 4. Deploy with production config
docker compose -f compose.prod.yaml up -d
```

**compose.prod.yaml example:**

```yaml
version: '3.8'

services:
  smartran-studio-arangodb:
    environment:
      - ARANGO_ROOT_PASSWORD=${ARANGO_PASSWORD}  # Read from .env file
      - ARANGO_NO_AUTH=0
  
  smartran-studio-sim-engine:
    environment:
      - ARANGO_PASSWORD=${ARANGO_PASSWORD}  # Same value
      - ARANGO_DATABASE=${ARANGO_DATABASE}
  
  backend:
    environment:
      - ARANGO_PASSWORD=${ARANGO_PASSWORD}  # Same value
      - ARANGO_DATABASE=${ARANGO_DATABASE}
```

Then create `.env` file (also add to `.gitignore`):

```bash
ARANGO_PASSWORD=your_production_password_here
ARANGO_DATABASE=smartran_production
```

---

## Troubleshooting

### Error: "ARANGO_PASSWORD environment variable is required"

**Cause:** Missing or empty password in compose.yaml

**Fix:**
```yaml
environment:
  - ARANGO_PASSWORD=your_password_here  # Must not be empty
```

### Error: "Connection refused" or "Failed to connect to ArangoDB"

**Cause:** Mismatch between services or wrong credentials

**Fix:** Verify all three password values match:
1. `smartran-studio-arangodb` → `ARANGO_ROOT_PASSWORD`
2. `smartran-studio-sim-engine` → `ARANGO_PASSWORD`
3. `backend` → `ARANGO_PASSWORD`

### Error: "SIONNA_API_URL environment variable is required"

**Cause:** Missing API URL in backend service

**Fix:**
```yaml
backend:
  environment:
    - SIONNA_API_URL=http://smartran-studio-sim-engine:8000
```

Make sure the service name matches your sim-engine service name.

---

## Verification

After making configuration changes, verify everything works:

```bash
# 1. Restart services
docker compose down
docker compose up -d

# 2. Check logs for successful startup
docker compose logs smartran-studio-sim-engine | grep "Connected to ArangoDB"
docker compose logs backend | grep "Connected to database"

# 3. Test web interface
# Open http://localhost:8080 and run:
srs status

# 4. Test database access
# Open http://localhost:8529
# Login with your configured credentials
```

---

## See Also

- [Getting Started Guide](GETTING_STARTED.md)
- [Database Schema Reference](DATABASE_SCHEMA.md)
- [Development Guide](DEVELOPMENT.md)
- [Docker Compose Documentation](https://docs.docker.com/compose/)

---

**Last Updated:** November 2025  
**Security Review:** Recommended before production deployment

