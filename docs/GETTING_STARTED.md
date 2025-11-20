# Getting Started with SmartRAN Studio

SmartRAN Studio is a GPU-accelerated radio access network (RAN) simulation platform for 5G/6G network planning and optimization.

## Prerequisites

- **Docker** & **Docker Compose** installed
- **NVIDIA GPU** with CUDA support (8GB+ VRAM recommended)
- **NVIDIA Container Toolkit** installed ([installation guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html))
- 16GB+ system RAM

### Verify NVIDIA Container Toolkit

Test GPU access in Docker:
```bash
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi
```

If this works, you're ready to run SmartRAN Studio!

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd smartran-studio
```

### 2. Start All Services

From the root directory:

```bash
docker-compose up -d
```

This starts 4 services:
- **Database** (ArangoDB) - Port 8529
- **Simulation Engine** - Port 8000  
- **CLI Backend** - Port 8001
- **Web Frontend** - Port 8080

### 3. Access the Web Interface

Open your browser to: **http://localhost:8080**

You'll see the SmartRAN Studio CLI interface.

### 4. Initialize a Simulation

In the CLI, run:

```bash
srs init --default
```

This creates a default simulation with:
- 10 sites with dual-band cells (2.5 GHz + 600 MHz)
- 30,000 UEs distributed in a box layout
- Configured for immediate use

### 5. Check Status

```bash
srs status
```

### 6. Query the Network

```bash
# List all cells
srs query cells

# List all sites
srs query sites

# Query specific band
srs query cells --band=H
```

### 7. Run a Simulation

```bash
srs sim compute --name="baseline"
```

This computes RSRP (Reference Signal Received Power) for all UE-cell pairs and saves the results as a snapshot.

## Next Steps

- **CLI Reference**: See `docs/CLI_REFERENCE.md` for all available commands
- **API Documentation**: See `docs/API_REFERENCE.md` for direct API access
- **Architecture**: See `docs/ARCHITECTURE.md` to understand the system design
- **Development**: See `docs/DEVELOPMENT.md` for development setup

## Stopping Services

```bash
docker-compose down
```

To remove volumes (database data):

```bash
docker-compose down -v
```

