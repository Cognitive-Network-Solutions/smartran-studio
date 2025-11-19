# Network Map Visualization Feature

## Overview

The Network Map tab provides a visual representation of your cellular network simulation, displaying cell towers with directional sectors on a Cartesian coordinate system.

## Features

### Visual Elements
- **Cell Sectors**: Displayed as pie-slice shapes showing antenna coverage direction
- **Color Coding**: 
  - Red (#FF6B6B) - High Band (H)
  - Teal (#4ECDC4) - Low Band (L)
- **Grid System**: Background grid with origin at (0, 0)
- **Scale Indicator**: Shows distance scale in meters

### Interactive Controls
- **Pan**: Click and drag to move around the map
- **Zoom**: 
  - Mouse wheel to zoom in/out
  - Zoom In/Out buttons in top-left corner
- **Cell Selection**: Click on any cell to view detailed information
- **Reset View**: Button to reset pan/zoom to default
- **Reload Data**: Refresh cell data from the simulation

### Right Panel Information
1. **Network Stats**: Total cell count and coordinate system info
2. **Band Legend**: Color key for different frequency bands
3. **Control Help**: Quick reference for map interactions
4. **Cell Details** (when selected): Shows detailed information about the clicked cell

## Technical Architecture

### Data Flow
```
Sionna API → Interface Backend (/map/cells) → Frontend Map View
```

### Backend Endpoint
- **URL**: `GET /api/map/cells`
- **Response Format**:
```json
{
  "cells": [
    {
      "cell_idx": 0,
      "cell_name": "CNS000-H-0",
      "site_name": "CNS000",
      "band": "H",
      "x": 100.5,
      "y": 200.3,
      "azimuth": 120.0,
      "tilt": 10.0,
      "frequency": 3500.0,
      "antenna_rows": 8,
      "antenna_cols": 8,
      "antenna_pattern": "38.901"
    }
  ],
  "count": 150,
  "coordinate_system": "cartesian",
  "origin": [0, 0]
}
```

### Frontend Components
- **map.js**: Main NetworkMap class handling rendering and interactions
- **map-styles.css**: Styling for map canvas and legend panel
- **app.js**: Integration with main application view system

## Visualization Details

### Sector Rendering
- **Sector Radius**: 50 meters (scales with zoom)
- **Beam Width**: 65° (±32.5° from azimuth)
- **Azimuth Convention**: 
  - 0° = North (up)
  - 90° = East (right)
  - 180° = South (down)
  - 270° = West (left)

### Coordinate System
- **Origin**: (0, 0) at center
- **X-axis**: Horizontal (positive = right)
- **Y-axis**: Vertical (positive = up)
- **Units**: Meters

## Usage

### Navigating to Map
1. Click "Network Map" in the left sidebar navigation
2. Map will automatically load and display all cells from the simulation

### Viewing Cell Details
1. Click on any cell sector or site marker
2. Cell details panel appears on the right showing:
   - Cell and Site names
   - Band and frequency
   - Position coordinates
   - Azimuth and tilt angles
   - Antenna configuration

### Best Practices
- Use mouse wheel zoom for precise control
- Click "Reset View" if you get lost
- Use "Reload Data" after making changes to the simulation
- The map auto-fits to show all cells on initial load

## Future Enhancements (Possible)
- [ ] UE (User Equipment) positions overlay
- [ ] Coverage heatmap
- [ ] Neighbor relations (connecting lines)
- [ ] Filter cells by band/site
- [ ] Export map as image
- [ ] 3D visualization toggle
- [ ] Signal strength visualization
- [ ] Real-time updates during simulation

