import React, { useState, useEffect } from 'react'
import Layout from './components/Layout'
import CLI from './views/CLI'
import NetworkMap from './views/NetworkMap'

/**
 * Main App Component
 * Manages view routing and global state
 */
export default function App() {
  // Load active view from sessionStorage or default to 'cli'
  const [activeView, setActiveView] = useState(() => {
    const saved = sessionStorage.getItem('cns-active-view')
    return saved || 'cli'
  })

  // Persist active view to sessionStorage
  useEffect(() => {
    sessionStorage.setItem('cns-active-view', activeView)
  }, [activeView])

  return (
    <Layout activeView={activeView} onViewChange={setActiveView}>
      {/* Keep all views mounted, just toggle visibility */}
      <div style={{ display: activeView === 'cli' ? 'block' : 'none', height: '100%', width: '100%' }}>
        <CLI />
      </div>
      <div style={{ display: activeView === 'map' ? 'block' : 'none', height: '100%', width: '100%' }}>
        <NetworkMap />
      </div>
    </Layout>
  )
}

