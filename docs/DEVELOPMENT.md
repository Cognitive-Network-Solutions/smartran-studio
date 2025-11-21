# Development Guide

SmartRAN Studio follows a **container-first, GPU-native** development philosophy.

## Container-First Development

### Philosophy

**Why Containers?**
- ✅ **Reproducible environments** - Everyone runs the exact same stack
- ✅ **GPU dependencies solved** - RAPIDS container includes CUDA, TensorFlow, cuDF, Sionna pre-configured
- ✅ **No local setup hell** - No fighting with CUDA/cuDNN/driver versions
- ✅ **Production-ready** - What you develop is what you deploy
- ✅ **Multi-service orchestration** - Database, backend, frontend, sim-engine all work together

### Local Development is NOT Supported for Sim-Engine

❌ **Don't try to run sim-engine locally** outside Docker

**Why?** Installing these dependencies locally is extremely difficult:
- CUDA 12.x + cuDNN
- TensorFlow 2.19 with CUDA support
- RAPIDS libraries (cuDF, cuML, cuGraph)  
- Sionna 1.1.0
- Proper GPU driver configuration
- Python 3.11 environment

**Instead**: Use the RAPIDS container which has all of this pre-configured and tested.

## GPU-Native Development

### Hardware Requirements

- **NVIDIA GPU** with CUDA support (Compute Capability 7.0+)
- **8GB+ GPU memory** recommended (4GB minimum)
- **NVIDIA Container Toolkit** installed

### Why GPU-Native?

SmartRAN Studio is designed from the ground up for GPU acceleration:
- **Sionna** uses TensorFlow for GPU-accelerated ray tracing
- **RAPIDS** provides GPU-accelerated data processing
- **Chunked computation** enables large-scale simulations on consumer GPUs

**Performance**: 10 sites, 60 cells, 30,000 UEs computed in ~5-10 seconds on RTX 4060 Laptop GPU

## Development Workflow

### 1. Start the Full Stack

```bash
# From repository root
docker compose up -d
```

**What starts**:
- Database (ArangoDB)
- Simulation Engine (GPU container)
- CLI Backend (with hot reload)
- Web Frontend (Nginx)

### 2. Making Changes

#### Sim-Engine Code Changes

Code is in: `smartran-studio-sim-engine/`

```bash
# Make your changes to Python files
# Rebuild and restart
docker compose up --build -d smartran-studio-sim-engine

# View logs
docker compose logs -f smartran-studio-sim-engine
```

**No hot reload** - Container rebuild required for changes.

#### Backend Code Changes

Code is in: `smartran-studio-interface/interface_backend/`

**Hot reload is enabled!** Changes to `backend.py` and `config.yaml` apply automatically.

```bash
# Make changes
# Just save - no rebuild needed

# View logs to see reload
docker compose logs -f backend
```

#### Frontend Code Changes

Code is in: `smartran-studio-interface/interface_frontend/`

**Option 1: Rebuild container** (production build)
```bash
docker compose up --build -d frontend
```

**Option 2: Local dev server** (faster iteration)
```bash
cd smartran-studio-interface/interface_frontend
npm install
npm run dev
# Access at http://localhost:5173
```

### 3. Viewing Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f smartran-studio-sim-engine
docker compose logs -f backend
docker compose logs -f frontend
```

### 4. Accessing Containers

```bash
# Sim-engine shell
docker exec -it smartran-studio-sim-engine bash

# Backend shell
docker exec -it smartran-studio-backend bash

# Run commands inside
docker exec -it smartran-studio-sim-engine python -c "import sionna; print(sionna.__version__)"
```

### 5. Database Access

Web UI: http://localhost:8529
- Username: `root`
- Password: `smartran-studio_dev_password`

### 6. API Testing

```bash
# Sim-engine API docs
open http://localhost:8000/docs

# Backend API
curl http://localhost:8001/

# Test command
curl -X POST http://localhost:8001/api/command \
  -H "Content-Type: application/json" \
  -d '{"command": "srs status"}'
```

## Docker Compose Architecture

### Services

```yaml
services:
  smartran-studio-arangodb:     # Database
    ports: ["8529:8529"]
    
  smartran-studio-sim-engine:   # Simulation (GPU)
    ports: ["8000:8000"]
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia       # GPU access
              count: all
              capabilities: [gpu]
    
  backend:                       # CLI Backend
    ports: ["8001:8001"]
    volumes:                     # Hot reload
      - ./backend.py:/app/backend.py
      - ./config.yaml:/app/config.yaml
    
  frontend:                      # Web UI
    ports: ["8080:80"]
```

### Network

All services on `smartran-studio-network` Docker bridge:
- Internal DNS: Services reach each other by name
- Example: `backend` calls `http://smartran-studio-sim-engine:8000`

### Volumes

**Persistent**:
- `smartran_arango_data` - Database files
- `smartran_arango_apps` - ArangoDB apps

**Development Mounts**:
- Backend: `backend.py`, `config.yaml` (hot reload)

## Testing

### Unit Tests

```bash
# Sim-engine
docker exec -it smartran-studio-sim-engine pytest tests/

# Backend
docker exec -it smartran-studio-backend pytest tests/
```

### Integration Tests

```bash
# Full stack must be running
docker compose up -d

# Run integration tests
docker exec -it smartran-studio-backend pytest tests/integration/
```

### Manual Testing

Use the web CLI at http://localhost:8080:
```bash
srs init --default
srs query cells
srs sim compute --name="test"
```

## Debugging

### GPU Not Detected

```bash
# Check NVIDIA Container Toolkit
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi

# Check sim-engine GPU access
docker exec -it smartran-studio-sim-engine nvidia-smi
```

### Container Won't Start

```bash
# Check logs
docker compose logs smartran-studio-sim-engine

# Common issues:
# - GPU driver mismatch
# - NVIDIA Container Toolkit not installed
# - Port already in use
```

### Database Connection Errors

```bash
# Check database is running
docker ps | grep arangodb

# Check backend can reach database
docker exec -it smartran-studio-backend ping smartran-studio-arangodb

# Check logs
docker compose logs smartran-studio-arangodb
```

### Hot Reload Not Working

```bash
# Check volume mounts
docker inspect smartran-studio-backend | grep Mounts -A 10

# Restart backend
docker compose restart backend
```

## Building for Production

### Build All Images

```bash
docker compose build
```

### Build Specific Service

```bash
docker compose build smartran-studio-sim-engine
docker compose build backend
docker compose build frontend
```

### Push to Registry

```bash
# Tag images
docker tag smartran-studio-sim-engine:latest myregistry/smartran-studio-sim-engine:latest

# Push
docker push myregistry/smartran-studio-sim-engine:latest
```

## Performance Optimization

### GPU Memory

If you hit GPU memory limits:

1. **Reduce chunk sizes** in initialization:
   ```bash
   srs init --config '{"cells_chunk": 32, "ue_chunk": 500}'
   ```

2. **Monitor GPU usage**:
   ```bash
   docker exec -it smartran-studio-sim-engine nvidia-smi
   ```

3. **Reduce UE count**:
   ```bash
   srs init --config '{"num_ue": 10000}'
   ```

### Container Resources

Limit container resources in `docker-compose.yaml`:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

## Contributing

### Code Style

- **Python**: Follow PEP 8
- **JavaScript**: Prettier + ESLint configured
- **Commits**: Conventional commits format

### Pull Request Process

1. Fork repository
2. Create feature branch
3. Make changes in containers
4. Test locally with Docker Compose
5. Push and create PR
6. CI will build and test containers

### CI/CD

GitHub Actions builds Docker images on:
- Pull requests
- Pushes to main
- Tagged releases

## Troubleshooting

### "No space left on device"

Clean Docker:
```bash
docker system prune -a
docker volume prune
```

### Port already in use

```bash
# Find what's using port 8000
sudo lsof -i :8000

# Change ports in docker-compose.yaml
ports:
  - "8001:8000"  # Host:Container
```

### Slow builds

Use BuildKit:
```bash
export DOCKER_BUILDKIT=1
docker compose build
```

## Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/)
- [RAPIDS Documentation](https://docs.rapids.ai/)
- [Sionna Documentation](https://nvlabs.github.io/sionna/)

