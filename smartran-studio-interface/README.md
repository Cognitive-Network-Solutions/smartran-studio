# CNS Protostack Interface

A web-based CLI interface for interacting with the CNS Sionna RF simulation and future network sources.

## 🎯 Overview

The CNS Protostack Interface provides a command-line interface accessed through a web browser. It allows you to initialize simulations, query network topology, update cell configurations, run compute operations, and analyze results—all through an intuitive terminal interface.

### Architecture

```
Browser (localhost:8080)
    ↓
[Frontend Container - Nginx]
    ├─ Serves CLI web interface
    └─ Proxies /api/* to backend
         ↓
[Backend Container - FastAPI]
    └─ Processes CLI commands
         ↓
[Sionna Simulation API]
    └─ RF simulation engine
```

## 🚀 Quick Start

### Prerequisites
- Docker Desktop (Windows/Mac) or Docker Engine + Docker Compose (Linux)
- Running Sionna simulation (see `cns-meets-sionna/`)

### Start the Interface

```bash
# From cns-protostack-interface directory
docker compose up --build -d
```

**Access:** Open `http://localhost:8080` in your browser

### First Commands

```bash
# Check connection
cns status

# Initialize simulation with defaults
cns init --default

# Query cells
cns query cells

# Filter by band
cns query cells --band=H

# Update cell tilt
cns update cell 0 --tilt=12.0

# Run simulation
cns compute
```

## 📁 Repository Structure

```
cns-protostack-interface/
├── interface_frontend/        # Web-based CLI (Nginx)
│   ├── cli.js                # Terminal logic
│   ├── index.html            # UI layout
│   └── README.md             # CLI usage guide
├── interface_backend/         # Command processor (FastAPI)
│   ├── backend.py            # Main application
│   ├── commands/             # Command handlers
│   ├── config.yaml           # Network configuration
│   └── README.md             # Backend architecture
├── interface_db/              # ArangoDB for persistence
│   └── README.md             # Database setup guide
├── compose.yaml               # Docker orchestration
└── README.md                  # This file
```

## 📖 Documentation

- **[Frontend/CLI Guide](interface_frontend/README.md)** - All CLI commands, usage examples, workflows
- **[Backend Architecture](interface_backend/README.md)** - Backend structure, adding commands, API integration
- **[Database Setup](interface_db/README.md)** - ArangoDB configuration (future: state persistence)
- **[API Reference](API_RESPONSE_REFERENCE.md)** - Sionna API response formats

## 🐳 Docker Setup

### Network Configuration

The interface connects to the Sionna simulation via Docker networking:

```yaml
# cns-meets-sionna/compose.yaml creates the network
networks:
  cns-network:
    driver: bridge

# cns-protostack-interface/compose.yaml joins it
networks:
  cns-network:
    external: true
```

### Services

| Service | Container | Port | Purpose |
|---------|-----------|------|---------|
| Frontend | `cns-frontend` | 8080 | Web UI |
| Backend | `cns-backend` | 8001 | Command processor |
| Sionna | `cns-sionna-sim` | 8000 | Simulation API |
| ArangoDB | `cns-arangodb` | 8529 | Database (optional) |

### Common Commands

```bash
# Start services
docker compose up -d

# Rebuild after code changes
docker compose up --build -d

# View logs
docker compose logs -f backend

# Stop services
docker compose down
```

### Troubleshooting

**Backend connection issues:**
```bash
# Check if all containers are running
docker ps

# Test Sionna API directly
curl http://localhost:8000/

# Check backend logs
docker logs cns-backend
```

**Port conflicts:**
Edit `compose.yaml` and change port mappings:
```yaml
frontend:
  ports:
    - "3000:80"  # Change 8080 to 3000
```

## 🔧 Configuration

### Backend Configuration (`interface_backend/config.yaml`)

```yaml
networks:
  sim:
    name: "CNS Sionna Simulation"
    type: "simulation"
    api_url: "http://cns-sionna-sim:8000"  # Internal Docker network
    enabled: true

default_network: "sim"
```

**API URL Options:**
- `http://cns-sionna-sim:8000` - Both containers in Docker (recommended)
- `http://host.docker.internal:8000` - Backend in Docker, Sionna on host
- `http://localhost:8000` - Backend outside Docker

### Adding New Networks

Edit `config.yaml`:
```yaml
networks:
  staging:
    name: "Staging Environment"
    api_url: "https://staging-api.cns.network"
    enabled: true
```

Then connect:
```bash
cns connect staging
```

## 🎨 Features

✅ **Interactive Wizard** - Step-by-step simulation setup  
✅ **Flexible Queries** - Filter cells/sites with multiple criteria  
✅ **Bulk Updates** - Update multiple cells at once  
✅ **Beautiful Tables** - HTML tables with dark/light theme support  
✅ **Command History** - Scroll through previous commands  
✅ **Tab Completion** - Auto-complete based on command history  
✅ **Context-Sensitive Help** - `--help` on any command  
✅ **Strict Validation** - Clear error messages for invalid input  

## 💻 Development

### Local Development (Outside Docker)

**Start Backend:**
```bash
cd interface_backend
pip install -r requirements.txt
python backend.py
```

**Start Frontend:**
```bash
cd interface_frontend
python -m http.server 8080
```

**Access:** `http://localhost:8080`

### Adding New Commands

See [Backend Documentation](interface_backend/README.md#adding-new-commands) for details.

### Frontend Customization

See [Frontend Documentation](interface_frontend/README.md#customization) for theming and UI changes.

## 📊 Example Workflows

### Initialize and Explore

```bash
# Initialize with all defaults
cns init --default

# View topology
cns query sites
cns query cells

# Check UE configuration
cns query ues
```

### Tilt Optimization Study

```bash
# Query high-band cells
cns query cells --band=H

# Update all high-band cells
cns update cells query --band=H --update-tilt-deg=12.0

# Run simulation
cns compute

# Try different tilt
cns update cells query --band=H --update-tilt-deg=10.0
cns compute
```

### Site-Specific Configuration

```bash
# Query specific site
cns query cells --site-name=CNS0001A

# Update just that site
cns update cells query --site-name=CNS0001A --update-tilt-deg=11.0

# Update with wildcard
cns update cells query --site-name=CNS000* --band=H --update-tilt-deg=11.5
```

## 🔮 Future Enhancements

- [ ] State persistence with ArangoDB
- [ ] Measurement report caching
- [ ] Multi-network switching
- [ ] Authentication for production networks
- [ ] Result comparison and visualization
- [ ] Batch operations from files

## 📝 License

Cognitive Network Solutions Inc. - Internal Use

---

**Need help?** 
- CLI Commands: [Frontend README](interface_frontend/README.md)
- Backend Development: [Backend README](interface_backend/README.md)
- Check logs: `docker compose logs -f`
