# SmartRAN Studio

**GPU-accelerated 5G/6G radio access network simulation platform with container-first architecture**

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-required-2496ED?logo=docker)](https://www.docker.com/)
[![NVIDIA](https://img.shields.io/badge/NVIDIA-GPU%20Required-76B900?logo=nvidia)](https://developer.nvidia.com/cuda-zone)

SmartRAN Studio is a modern RAN simulation platform designed for network planning, optimization, and research. Built on NVIDIA Sionna, it provides a web-based CLI interface for RF propagation simulation with production-ready Docker deployment.

## ✨ Key Features

- 🐳 **Container-First Development** - Complete stack runs in Docker with zero local setup
- 🚀 **GPU-Native Architecture** - Built for NVIDIA GPUs from the ground up using Sionna + TensorFlow
- 🎮 **Web-Based CLI** - Terminal-style interface accessible from any browser
- ⚡ **Fast Computation** - 30,000 UEs across 60 cells computed in ~5-10 seconds
- 📊 **Flexible Topology** - Dynamic site/cell management with per-cell antenna configuration
- 💾 **State Management** - Save/load configurations, persistent measurement snapshots
- 🔧 **Production Ready** - Microservices architecture with orchestrated Docker Compose deployment

## 🏗️ Architecture

```
┌─────────────┐
│   Browser   │ ← Access web CLI at localhost:8080
└──────┬──────┘
       │
┌──────▼───────────────────────────────────────┐
│  Frontend (React + Vite)                     │
│  • Terminal-style CLI                        │
│  • Command history & autocomplete            │
│  • Interactive wizards                       │
└──────┬───────────────────────────────────────┘
       │
┌──────▼───────────────────────────────────────┐
│  Backend (FastAPI)                           │
│  • Command processing                        │
│  • Session management                        │
│  • Configuration save/load                   │
└──┬────────────────────────┬──────────────────┘
   │                        │
   │                  ┌─────▼──────┐
   │                  │  Database  │
   │                  │ (ArangoDB) │
   │                  └────────────┘
   │
┌──▼──────────────────────────────────────────┐
│  Simulation Engine (GPU Container)          │
│  • NVIDIA Sionna RF simulation              │
│  • TensorFlow + CUDA acceleration           │
│  • Multi-cell propagation                   │
│  • RSRP computation                          │
└─────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- **Docker** & **Docker Compose**
- **NVIDIA GPU** with 8GB+ VRAM
- **NVIDIA Container Toolkit** ([install guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html))

**Verify GPU access:**
```bash
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi
```

### 1. Clone & Start

```bash
git clone <repository-url>
cd smartran-studio
docker-compose up -d
```

This starts all services:
- 🌐 **Web UI**: http://localhost:8080
- 🔌 **Sim Engine API**: http://localhost:8000
- 🔌 **Backend API**: http://localhost:8001
- 💾 **Database UI**: http://localhost:8529

### 2. Initialize Simulation

Open http://localhost:8080 and run:

```bash
srs init --default
```

Creates a simulation with:
- 10 sites with dual-band cells (2.5 GHz + 600 MHz)
- 30,000 UEs distributed in a box layout
- Ready for immediate use

### 3. Run Commands

```bash
# Check status
srs status

# Query network
srs query cells
srs query sites

# Update configuration
srs update cell 0 --tilt=12.0

# Run simulation
srs sim compute --name="baseline"

# Save configuration
srs config save baseline
```

### 4. Stop

```bash
docker-compose down
```

## 📖 Documentation

- **[Getting Started](docs/GETTING_STARTED.md)** - Complete setup guide
- **[CLI Reference](docs/CLI_REFERENCE.md)** - All available commands
- **[Architecture](docs/ARCHITECTURE.md)** - System design and components
- **[Development](docs/DEVELOPMENT.md)** - Container-first development guide

## 🎯 Use Cases

### Network Planning
- Site placement optimization
- Coverage analysis
- Interference assessment
- Capacity planning

### Research & Development
- Algorithm testing
- Antenna configuration studies
- Propagation model validation
- Multi-cell coordination

### Education
- RAN fundamentals
- RF propagation visualization
- Network simulation training
- Docker + GPU deployment learning

## 🔧 Technology Stack

### Core Simulation
- **[NVIDIA Sionna 1.1.0](https://nvlabs.github.io/sionna/)** - Ray-tracing RF simulator
- **TensorFlow 2.19** - GPU computation backend
- **RAPIDS** - GPU-accelerated data processing
- **3GPP TR 38.901** - Urban Macro (UMa) channel model

### Microservices
- **FastAPI** - REST APIs (Python 3.11)
- **React 18 + Vite** - Frontend framework
- **ArangoDB 3.11** - Multi-model database
- **Docker Compose** - Service orchestration

### Infrastructure
- **RAPIDS Container** - Pre-configured GPU environment
- **NVIDIA Container Toolkit** - GPU access in Docker
- **Nginx** - Frontend web server

## 🐳 Container-First Philosophy

**Why containers?**
- ✅ Reproducible environments across all systems
- ✅ GPU dependencies (CUDA, TensorFlow, RAPIDS) pre-configured
- ✅ No local setup complexity
- ✅ Production-ready deployment
- ✅ Service isolation and orchestration

**GPU-Native Design:**
- Built for NVIDIA GPUs from the ground up
- Uses RAPIDS container with all dependencies included
- Optimized for consumer GPUs (8GB+ VRAM)
- Chunked computation for memory efficiency

## 📊 Performance

**Typical Performance** (RTX 4060 Laptop GPU):
- **Network**: 10 sites, 60 cells, 30,000 UEs
- **Compute Time**: ~5-10 seconds
- **GPU Memory**: ~4-5 GB

**Scalability**:
- Automatic chunking for large networks
- Tested with 50,000+ UEs
- Configurable memory usage

## 🛠️ Development

### Container-First Workflow

All development happens in containers:

```bash
# Make code changes
# Rebuild affected service
docker-compose up --build -d smartran-studio-sim-engine

# Backend has hot reload - no rebuild needed
# Frontend can use local dev server for faster iteration
cd smartran-studio-interface/interface_frontend
npm run dev
```

See **[Development Guide](docs/DEVELOPMENT.md)** for details.

### Project Structure

```
smartran-studio/
├── docker-compose.yaml          # Complete stack orchestration
├── docs/                        # Documentation
├── smartran-studio-sim-engine/  # GPU simulation engine
│   ├── api/                     # FastAPI endpoints
│   ├── simulation/              # Sionna simulation core
│   ├── analysis/                # Beampattern tools
│   └── db/                      # Database persistence
└── smartran-studio-interface/   # Web interface
    ├── interface_frontend/      # React CLI
    ├── interface_backend/       # Command processor
    └── interface_db/            # Database setup
```

## 📋 Command Reference

### Simulation Management
```bash
srs init [--default]              # Initialize simulation
srs status                        # Show simulation status
srs sim compute --name=<name>     # Run RF computation
```

### Network Queries
```bash
srs query cells [--band=H|L|M]    # List/filter cells
srs query sites                   # List all sites
srs query ues                     # Show UE distribution
```

### Configuration
```bash
srs update cell <id> --tilt=<deg>       # Update cell
srs update cells query --band=H ...     # Bulk update
srs site add --x=<m> --y=<m>            # Add site
srs cell add --site=<name> --sector=<n> # Add cell
```

### State Management
```bash
srs config save <name>         # Save configuration
srs config load <name>         # Restore configuration
srs config list                # List saved configs
srs snapshot list              # List simulation results
```

See **[CLI Reference](docs/CLI_REFERENCE.md)** for complete command list.

## 🤝 Contributing

Contributions are welcome! SmartRAN Studio follows container-first development:

1. Fork the repository
2. Create feature branch
3. Make changes and test in Docker
4. Submit pull request

All development and testing happens in containers - no local GPU setup required for contributing to non-simulation components.

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

**Third-Party Software:** This project uses several open-source components and NVIDIA technologies. See [NOTICE.md](NOTICE.md) for complete attribution and licensing information.

## 🙏 Acknowledgments

This project builds upon excellent open-source software and industry standards:

### Core Technologies
- **[NVIDIA Sionna](https://nvlabs.github.io/sionna/)** - Link-level simulator for 6G physical layer research (Apache 2.0)
- **[TensorFlow](https://www.tensorflow.org/)** - Machine learning framework for GPU computation (Apache 2.0)
- **[NVIDIA RAPIDS](https://rapids.ai/)** - GPU-accelerated data science libraries (Apache 2.0)
- **[ArangoDB](https://www.arangodb.com/)** - Multi-model database for state management (Apache 2.0)

### NVIDIA Infrastructure
- **NVIDIA Container Toolkit** - GPU access in Docker containers
- **NVIDIA CUDA** - Parallel computing platform
- **RAPIDS Container Images** - Pre-configured GPU environment

### Standards
- **[3GPP TR 38.901](https://www.3gpp.org/)** - Channel model specifications for 5G/6G

**Special Thanks:** To the NVIDIA Sionna team for creating an accessible, GPU-native RF simulation framework that makes projects like this possible.

For detailed license information and copyright notices, please see [NOTICE.md](NOTICE.md).

## 📬 Contact

For questions, issues, or contributions, please open a GitHub issue.

---

**Built with ❤️ for the wireless community**

*Container-first • GPU-native • Production-ready*
