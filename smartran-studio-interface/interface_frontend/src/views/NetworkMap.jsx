import React, { useState, useRef, useEffect, useCallback } from 'react'
import { getMapCells } from '../utils/api'

/**
 * NetworkMap Component
 * Interactive network visualization with Canvas and SVG rendering
 */
export default function NetworkMap() {
  // State
  const [cells, setCells] = useState([])
  const [selectedCell, setSelectedCell] = useState(null)
  const [hoveredCell, setHoveredCell] = useState(null)
  const [scale, setScale] = useState(1)
  const [offset, setOffset] = useState({ x: 0, y: 0 })
  const [isDragging, setIsDragging] = useState(false)
  const [lastMouse, setLastMouse] = useState({ x: 0, y: 0 })
  const [tooltip, setTooltip] = useState({ show: false, x: 0, y: 0, cell: null })
  
  // Refs
  const canvasRef = useRef(null)
  const svgRef = useRef(null)
  const containerRef = useRef(null)
  
  // Configuration
  const config = {
    sectorRadius: 50,
    sectorAngle: 65
  }

  // Dynamic color generation for any band identifier
  const getBandColor = useCallback((band) => {
    if (!band) return '#888888'
    
    // Predefined colors for common bands
    const knownColors = {
      'H': '#FF6B6B',  // Red
      'L': '#4ECDC4',  // Cyan
      'M': '#95E1D3',  // Green
      'U': '#FFB84D',  // Orange
      'X': '#A78BFA',  // Purple
    }
    
    if (knownColors[band]) return knownColors[band]
    
    // Generate color from band string (hash-based)
    let hash = 0
    for (let i = 0; i < band.length; i++) {
      hash = band.charCodeAt(i) + ((hash << 5) - hash)
    }
    
    // Convert to HSL for better color distribution
    const hue = Math.abs(hash % 360)
    const saturation = 65 + (Math.abs(hash >> 8) % 20)  // 65-85%
    const lightness = 55 + (Math.abs(hash >> 16) % 15)  // 55-70%
    
    return `hsl(${hue}, ${saturation}%, ${lightness}%)`
  }, [])

  // Coordinate transformations
  const worldToScreen = useCallback((x, y) => {
    const canvas = canvasRef.current
    if (!canvas) return { x: 0, y: 0 }
    
    const centerX = canvas.width / 2
    const centerY = canvas.height / 2
    
    return {
      x: centerX + (x + offset.x) * scale,
      y: centerY - (y + offset.y) * scale
    }
  }, [scale, offset])

  const screenToWorld = useCallback((screenX, screenY) => {
    const canvas = canvasRef.current
    if (!canvas) return { x: 0, y: 0 }
    
    const centerX = canvas.width / 2
    const centerY = canvas.height / 2
    
    return {
      x: (screenX - centerX) / scale - offset.x,
      y: -((screenY - centerY) / scale - offset.y)
    }
  }, [scale, offset])

  // Load cells data
  const loadCells = useCallback(async () => {
    try {
      const data = await getMapCells()
      setCells(data.cells || [])
      console.log(`Loaded ${data.cells?.length || 0} cells`)
    } catch (error) {
      console.error('Failed to load cells:', error)
      setCells([])
    }
  }, [])

  // Reset view
  const resetView = useCallback(() => {
    setScale(1)
    setOffset({ x: 0, y: 0 })
    setSelectedCell(null)
  }, [])

  // Zoom functions
  const zoomIn = useCallback(() => {
    setScale(prev => prev * 1.2)
  }, [])

  const zoomOut = useCallback(() => {
    setScale(prev => prev / 1.2)
  }, [])

  // Draw canvas background (grid, axes, labels)
  const drawCanvas = useCallback(() => {
    const canvas = canvasRef.current
    if (!canvas || canvas.width === 0 || canvas.height === 0) return
    
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    
    // Clear canvas
    ctx.fillStyle = '#ffffff'
    ctx.fillRect(0, 0, canvas.width, canvas.height)
    
    // Draw grid
    drawGrid(ctx)
    
    // Draw axes
    drawAxes(ctx)
    
    // Draw scale indicator
    drawScaleIndicator(ctx)
  }, [scale, offset, worldToScreen])

  const drawGrid = (ctx) => {
    const gridSpacing = 50 * scale
    const origin = worldToScreen(0, 0)
    
    ctx.strokeStyle = '#f1f5f9'
    ctx.lineWidth = 1
    
    // Vertical grid lines
    for (let x = origin.x % gridSpacing; x < canvasRef.current.width; x += gridSpacing) {
      ctx.beginPath()
      ctx.moveTo(x, 0)
      ctx.lineTo(x, canvasRef.current.height)
      ctx.stroke()
    }
    
    // Horizontal grid lines
    for (let y = origin.y % gridSpacing; y < canvasRef.current.height; y += gridSpacing) {
      ctx.beginPath()
      ctx.moveTo(0, y)
      ctx.lineTo(canvasRef.current.width, y)
      ctx.stroke()
    }
  }

  const drawAxes = (ctx) => {
    const origin = worldToScreen(0, 0)
    
    // Draw X and Y axes
    ctx.strokeStyle = '#cbd5e1'
    ctx.lineWidth = 1.5
    
    // X-axis
    ctx.beginPath()
    ctx.moveTo(0, origin.y)
    ctx.lineTo(canvasRef.current.width, origin.y)
    ctx.stroke()
    
    // Y-axis
    ctx.beginPath()
    ctx.moveTo(origin.x, 0)
    ctx.lineTo(origin.x, canvasRef.current.height)
    ctx.stroke()
    
    // Draw axis labels
    drawAxisLabels(ctx)
    
    // Draw origin marker
    ctx.fillStyle = '#94a3b8'
    ctx.beginPath()
    ctx.arc(origin.x, origin.y, 3, 0, Math.PI * 2)
    ctx.fill()
    
    // Label origin
    ctx.fillStyle = '#64748b'
    ctx.font = '10px sans-serif'
    ctx.fillText('0', origin.x + 6, origin.y - 6)
  }

  const drawAxisLabels = (ctx) => {
    const origin = worldToScreen(0, 0)
    const labelSpacing = 100
    
    const worldMin = screenToWorld(0, canvasRef.current.height)
    const worldMax = screenToWorld(canvasRef.current.width, 0)
    
    ctx.fillStyle = '#94a3b8'
    ctx.font = '10px sans-serif'
    ctx.textAlign = 'center'
    
    // X-axis labels
    const startX = Math.floor(worldMin.x / labelSpacing) * labelSpacing
    const endX = Math.ceil(worldMax.x / labelSpacing) * labelSpacing
    
    for (let x = startX; x <= endX; x += labelSpacing) {
      if (x === 0) continue
      
      const screen = worldToScreen(x, 0)
      
      ctx.strokeStyle = '#cbd5e1'
      ctx.lineWidth = 1
      ctx.beginPath()
      ctx.moveTo(screen.x, origin.y - 4)
      ctx.lineTo(screen.x, origin.y + 4)
      ctx.stroke()
      
      ctx.fillText(`${x}`, screen.x, origin.y + 16)
    }
    
    // Y-axis labels
    const startY = Math.floor(worldMin.y / labelSpacing) * labelSpacing
    const endY = Math.ceil(worldMax.y / labelSpacing) * labelSpacing
    
    ctx.textAlign = 'right'
    
    for (let y = startY; y <= endY; y += labelSpacing) {
      if (y === 0) continue
      
      const screen = worldToScreen(0, y)
      
      ctx.strokeStyle = '#cbd5e1'
      ctx.lineWidth = 1
      ctx.beginPath()
      ctx.moveTo(origin.x - 4, screen.y)
      ctx.lineTo(origin.x + 4, screen.y)
      ctx.stroke()
      
      ctx.fillText(`${y}`, origin.x - 8, screen.y + 4)
    }
  }

  const drawScaleIndicator = (ctx) => {
    const scaleBarLength = 100
    const scaleBarWorldLength = scaleBarLength / scale
    
    ctx.fillStyle = '#1e293b'
    ctx.font = '11px sans-serif'
    ctx.textAlign = 'left'
    ctx.fillText(`${scaleBarWorldLength.toFixed(0)} m`, 15, canvasRef.current.height - 30)
    
    ctx.strokeStyle = '#1e293b'
    ctx.lineWidth = 2
    ctx.beginPath()
    ctx.moveTo(10, canvasRef.current.height - 15)
    ctx.lineTo(10 + scaleBarLength, canvasRef.current.height - 15)
    ctx.stroke()
    
    ctx.beginPath()
    ctx.moveTo(10, canvasRef.current.height - 20)
    ctx.lineTo(10, canvasRef.current.height - 10)
    ctx.stroke()
    
    ctx.beginPath()
    ctx.moveTo(10 + scaleBarLength, canvasRef.current.height - 20)
    ctx.lineTo(10 + scaleBarLength, canvasRef.current.height - 10)
    ctx.stroke()
  }

  // Draw SVG sectors
  const drawSVG = useCallback(() => {
    const svg = svgRef.current
    const canvas = canvasRef.current
    if (!svg || !canvas || canvas.width === 0 || canvas.height === 0) return
    
    // Clear existing content
    while (svg.firstChild) {
      svg.removeChild(svg.firstChild)
    }
    
    // Group cells by site
    const siteMap = new Map()
    cells.forEach(cell => {
      const siteKey = `${cell.x},${cell.y}`
      if (!siteMap.has(siteKey)) {
        siteMap.set(siteKey, [])
      }
      siteMap.get(siteKey).push(cell)
    })
    
    // Draw each site
    siteMap.forEach(siteCells => {
      drawSite(siteCells)
    })
  }, [cells, scale, offset, selectedCell, worldToScreen])

  const drawSite = (siteCells) => {
    if (siteCells.length === 0) return
    
    const firstCell = siteCells[0]
    const pos = worldToScreen(firstCell.x, firstCell.y)
    
    // Group by azimuth
    const sectors = new Map()
    siteCells.forEach(cell => {
      if (!sectors.has(cell.azimuth)) {
        sectors.set(cell.azimuth, [])
      }
      sectors.get(cell.azimuth).push(cell)
    })
    
    // Draw all bands dynamically - sorted by frequency (higher freq = larger)
    sectors.forEach(cellsAtAzimuth => {
      // Sort by frequency descending (highest first, will be drawn largest)
      const sortedCells = [...cellsAtAzimuth].sort((a, b) => b.frequency - a.frequency)
      
      // Draw each band with size based on its frequency rank
      sortedCells.forEach((cell, idx) => {
        // Scale factor: highest freq = 1.3x, then 1.1x, 0.9x, 0.7x, etc.
        const sizeFactor = 1.3 - (idx * 0.2)
        const radius = config.sectorRadius * scale * Math.max(sizeFactor, 0.5)
        const color = getBandColor(cell.band)
        createSector(pos.x, pos.y, radius, cell.azimuth, config.sectorAngle, color, cell)
      })
    })
    
    // Draw site marker
    const marker = document.createElementNS('http://www.w3.org/2000/svg', 'circle')
    marker.setAttribute('cx', pos.x)
    marker.setAttribute('cy', pos.y)
    marker.setAttribute('r', 5)
    marker.setAttribute('fill', '#1e293b')
    marker.setAttribute('stroke', '#ffffff')
    marker.setAttribute('stroke-width', 2)
    marker.style.pointerEvents = 'none'
    svgRef.current.appendChild(marker)
  }

  const createSector = (centerX, centerY, radius, azimuthDeg, beamwidthDeg, color, cell) => {
    const azimuthRad = (azimuthDeg - 90) * Math.PI / 180
    const halfBeamRad = (beamwidthDeg / 2) * Math.PI / 180
    
    const startAngle = azimuthRad - halfBeamRad
    const endAngle = azimuthRad + halfBeamRad
    
    const startX = centerX + radius * Math.cos(startAngle)
    const startY = centerY + radius * Math.sin(startAngle)
    const endX = centerX + radius * Math.cos(endAngle)
    const endY = centerY + radius * Math.sin(endAngle)
    
    const largeArcFlag = (endAngle - startAngle) > Math.PI ? 1 : 0
    const pathData = [
      `M ${centerX} ${centerY}`,
      `L ${startX} ${startY}`,
      `A ${radius} ${radius} 0 ${largeArcFlag} 1 ${endX} ${endY}`,
      'Z'
    ].join(' ')
    
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path')
    path.setAttribute('d', pathData)
    path.setAttribute('class', 'sector')
    path.setAttribute('data-cell', cell.cell_name)
    
    const isSelected = cell === selectedCell
    const opacity = isSelected ? 0.85 : 0.7
    
    const hexToRgba = (hex, alpha) => {
      const r = parseInt(hex.slice(1, 3), 16)
      const g = parseInt(hex.slice(3, 5), 16)
      const b = parseInt(hex.slice(5, 7), 16)
      return `rgba(${r}, ${g}, ${b}, ${alpha})`
    }
    
    path.setAttribute('fill', hexToRgba(color, opacity))
    path.setAttribute('stroke', isSelected ? '#ffffff' : color)
    path.setAttribute('stroke-width', isSelected ? 2 : 1)
    
    // Event listeners
    path.addEventListener('mouseenter', (e) => {
      setHoveredCell(cell)
      const rect = svgRef.current.getBoundingClientRect()
      setTooltip({
        show: true,
        x: e.clientX - rect.left,
        y: e.clientY - rect.top,
        cell
      })
    })
    
    path.addEventListener('mouseleave', () => {
      setHoveredCell(null)
      setTooltip(prev => ({ ...prev, show: false }))
    })
    
    path.addEventListener('click', () => {
      setSelectedCell(cell)
    })
    
    svgRef.current.appendChild(path)
  }

  // Canvas interactions
  const handleWheel = useCallback((e) => {
    e.preventDefault()
    const zoomFactor = e.deltaY > 0 ? 0.9 : 1.1
    setScale(prev => Math.max(0.1, Math.min(10, prev * zoomFactor)))
  }, [])

  const handleMouseDown = useCallback((e) => {
    setIsDragging(true)
    setLastMouse({ x: e.clientX, y: e.clientY })
  }, [])

  const handleMouseMove = useCallback((e) => {
    if (!isDragging) return
    
    const dx = e.clientX - lastMouse.x
    const dy = e.clientY - lastMouse.y
    
    setOffset(prev => ({
      x: prev.x + dx / scale,
      y: prev.y - dy / scale
    }))
    
    setLastMouse({ x: e.clientX, y: e.clientY })
  }, [isDragging, lastMouse, scale])

  const handleMouseUp = useCallback(() => {
    setIsDragging(false)
  }, [])

  // Resize handler
  const resizeCanvas = useCallback(() => {
    const container = containerRef.current
    const canvas = canvasRef.current
    const svg = svgRef.current
    
    if (!container || !canvas || !svg) return
    
    const rect = container.getBoundingClientRect()
    const width = rect.width
    const height = rect.height
    
    // Only resize if dimensions are valid (component is visible)
    if (width <= 0 || height <= 0) return
    
    canvas.width = width
    canvas.height = height
    
    svg.setAttribute('width', width)
    svg.setAttribute('height', height)
    svg.setAttribute('viewBox', `0 0 ${width} ${height}`)
  }, [])

  // Effects
  useEffect(() => {
    loadCells()
  }, [loadCells])

  // Resize canvas on mount and window resize
  useEffect(() => {
    resizeCanvas()
    window.addEventListener('resize', resizeCanvas)
    return () => window.removeEventListener('resize', resizeCanvas)
  }, [resizeCanvas])

  // Redraw when state changes
  useEffect(() => {
    drawCanvas()
    drawSVG()
  }, [drawCanvas, drawSVG, scale, offset, cells, selectedCell])

  return (
    <div className="h-full w-full flex overflow-hidden">
      <div className="flex-1 relative" ref={containerRef}>
        <canvas
          ref={canvasRef}
          className="absolute inset-0 w-full h-full"
          style={{ 
            backgroundColor: '#ffffff',
            cursor: isDragging ? 'grabbing' : 'grab'
          }}
          onWheel={handleWheel}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
        />
        <svg ref={svgRef} className="absolute inset-0 w-full h-full pointer-events-none" style={{ zIndex: 10 }} />
              
        {/* Tooltip */}
        {tooltip.show && tooltip.cell && (
          <div 
            className="absolute z-50 px-3 py-2 rounded-lg shadow-lg text-sm pointer-events-none"
            style={{ 
              left: tooltip.x + 15, 
              top: tooltip.y + 15,
              backgroundColor: 'var(--color-surface)',
              color: 'var(--color-ink)',
              border: '1px solid var(--color-line)'
            }}
          >
            <div className="font-bold mb-1">{tooltip.cell.cell_name}</div>
            <div className="flex gap-2 text-xs" style={{ color: 'var(--color-text)' }}>
              <span className="font-medium">Site:</span>
              <span>{tooltip.cell.site_name}</span>
            </div>
            <div className="flex gap-2 text-xs" style={{ color: 'var(--color-text)' }}>
              <span className="font-medium">Band:</span>
              <span>{tooltip.cell.band}</span>
            </div>
            <div className="flex gap-2 text-xs" style={{ color: 'var(--color-text)' }}>
              <span className="font-medium">Azimuth:</span>
              <span>{tooltip.cell.azimuth}°</span>
            </div>
            <div className="flex gap-2 text-xs" style={{ color: 'var(--color-text)' }}>
              <span className="font-medium">Frequency:</span>
              <span>{tooltip.cell.frequency} MHz</span>
            </div>
          </div>
        )}
              
        {/* Controls */}
        <div className="absolute top-4 left-4 z-20 flex flex-col gap-2">
          <button 
            onClick={zoomIn} 
            title="Zoom In"
            className="p-3 rounded-lg shadow-md hover:shadow-lg transition-all"
            style={{ backgroundColor: 'var(--color-surface)', color: 'var(--color-ink)' }}
          >
            <i className="ri-zoom-in-line text-lg"></i>
          </button>
          <button 
            onClick={zoomOut} 
            title="Zoom Out"
            className="p-3 rounded-lg shadow-md hover:shadow-lg transition-all"
            style={{ backgroundColor: 'var(--color-surface)', color: 'var(--color-ink)' }}
          >
            <i className="ri-zoom-out-line text-lg"></i>
          </button>
          <button 
            onClick={resetView} 
            title="Reset View"
            className="p-3 rounded-lg shadow-md hover:shadow-lg transition-all"
            style={{ backgroundColor: 'var(--color-surface)', color: 'var(--color-ink)' }}
          >
            <i className="ri-refresh-line text-lg"></i>
          </button>
          <button 
            onClick={loadCells} 
            title="Reload Data"
            className="p-3 rounded-lg shadow-md hover:shadow-lg transition-all"
            style={{ backgroundColor: 'var(--color-surface)', color: 'var(--color-ink)' }}
          >
            <i className="ri-download-cloud-line text-lg"></i>
          </button>
        </div>
              
      </div>
      
      {/* Sidebar */}
      <div 
        className="w-80 border-l p-6 overflow-y-auto scrollbar-thin"
        style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-line)' }}
      >
        <div className="space-y-6">
          {/* Network Info Section */}
          <div>
            <h3 className="text-lg font-semibold mb-3" style={{ color: 'var(--color-ink)' }}>Network Map</h3>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span style={{ color: 'var(--color-muted)' }}>Total Cells:</span>
                <span className="font-semibold text-accent">{cells.length}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span style={{ color: 'var(--color-muted)' }}>System:</span>
                <span className="font-mono text-xs" style={{ color: 'var(--color-text)' }}>Cartesian (0,0)</span>
              </div>
            </div>
          </div>
          
          {/* Band Legend Section - Dynamic */}
          <div>
            <h3 className="text-lg font-semibold mb-3" style={{ color: 'var(--color-ink)' }}>Band Legend</h3>
            <div className="space-y-2">
              {(() => {
                // Get unique bands from cells
                const uniqueBands = [...new Set(cells.map(c => c.band).filter(Boolean))]
                  .sort((a, b) => {
                    // Sort alphabetically but keep H, L, M first
                    const priority = { 'H': 0, 'L': 1, 'M': 2 }
                    const aPri = priority[a] ?? 99
                    const bPri = priority[b] ?? 99
                    if (aPri !== bPri) return aPri - bPri
                    return a.localeCompare(b)
                  })
                
                if (uniqueBands.length === 0) {
                  return (
                    <div className="text-sm" style={{ color: 'var(--color-muted)' }}>
                      No cells to display
                    </div>
                  )
                }
                
                return uniqueBands.map(band => (
                  <div key={band} className="flex items-center gap-3">
                    <div className="w-4 h-4 rounded" style={{ background: getBandColor(band) }}></div>
                    <span className="text-sm font-medium" style={{ color: 'var(--color-text)' }}>
                      Band {band}
                    </span>
                  </div>
                ))
              })()}
            </div>
          </div>
          
          {/* Controls Section */}
          <div>
            <h3 className="text-lg font-semibold mb-3" style={{ color: 'var(--color-ink)' }}>Controls</h3>
            <div className="space-y-2">
              <div className="flex items-center gap-3 text-sm" style={{ color: 'var(--color-text)' }}>
                <i className="ri-mouse-line text-lg" style={{ color: 'var(--color-muted)' }}></i>
                <span>Drag to pan</span>
              </div>
              <div className="flex items-center gap-3 text-sm" style={{ color: 'var(--color-text)' }}>
                <i className="ri-scroll-to-bottom-line text-lg" style={{ color: 'var(--color-muted)' }}></i>
                <span>Scroll to zoom</span>
              </div>
              <div className="flex items-center gap-3 text-sm" style={{ color: 'var(--color-text)' }}>
                <i className="ri-cursor-line text-lg" style={{ color: 'var(--color-muted)' }}></i>
                <span>Click cell for info</span>
              </div>
            </div>
          </div>
          
          {/* Cell Details Section */}
          {selectedCell && (
            <div>
              <h3 className="text-lg font-semibold mb-3" style={{ color: 'var(--color-ink)' }}>Cell Details</h3>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span style={{ color: 'var(--color-muted)' }}>Name:</span>
                  <span className="font-medium" style={{ color: 'var(--color-text)' }}>{selectedCell.cell_name}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span style={{ color: 'var(--color-muted)' }}>Site:</span>
                  <span style={{ color: 'var(--color-text)' }}>{selectedCell.site_name}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span style={{ color: 'var(--color-muted)' }}>Band:</span>
                  <span className="font-semibold" style={{ color: 'var(--color-text)' }}>{selectedCell.band}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span style={{ color: 'var(--color-muted)' }}>Position:</span>
                  <span className="font-mono text-xs" style={{ color: 'var(--color-text)' }}>({selectedCell.x}, {selectedCell.y})</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span style={{ color: 'var(--color-muted)' }}>Azimuth:</span>
                  <span style={{ color: 'var(--color-text)' }}>{selectedCell.azimuth}°</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span style={{ color: 'var(--color-muted)' }}>Tilt:</span>
                  <span style={{ color: 'var(--color-text)' }}>{selectedCell.tilt}°</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span style={{ color: 'var(--color-muted)' }}>Frequency:</span>
                  <span style={{ color: 'var(--color-text)' }}>{selectedCell.frequency} MHz</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span style={{ color: 'var(--color-muted)' }}>Antenna:</span>
                  <span className="font-mono text-xs" style={{ color: 'var(--color-text)' }}>
                    {selectedCell.antenna_rows}×{selectedCell.antenna_cols} ({selectedCell.antenna_pattern})
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

