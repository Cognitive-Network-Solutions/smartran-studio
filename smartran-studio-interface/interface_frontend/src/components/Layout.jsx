import React, { useState, useEffect } from 'react'
import Navigation from './Navigation'
import logoDark from '../assets/cnsLogo_darkmode.png'
import logoLight from '../assets/cnsLogo_lightmode.png'

/**
 * Layout Component
 * Main application layout with topbar, sidebar, and content area
 */
export default function Layout({ children, activeView, onViewChange }) {
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('theme') || 'dark'
  })

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('theme', theme)
  }, [theme])

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark')
  }

  const viewTitles = {
    cli: 'Command Line Interface',
    map: 'Network Map Visualization'
  }

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden" style={{ backgroundColor: 'var(--color-viewport-bg)' }}>
      {/* Topbar */}
      <div 
        className="flex items-center justify-between h-16 px-6 border-b shrink-0"
        style={{ 
          backgroundColor: 'var(--color-topbar-bg)',
          borderColor: 'var(--color-line)',
          color: 'var(--color-topbar-ink)'
        }}
      >
        <div className="flex items-center gap-4">
          <img 
            src={theme === 'dark' ? logoDark : logoLight} 
            alt="CNS Logo" 
            className="h-8 w-auto" 
          />
          <div className="flex items-center gap-3">
            <span className="text-sm font-bold tracking-wider" style={{ color: 'var(--color-accent)' }}>CNS</span>
            <span className="text-gray-400">|</span>
            <h1 className="text-lg font-semibold">{viewTitles[activeView] || 'Interface'}</h1>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button 
            className="p-2 rounded-lg hover:bg-opacity-10 hover:bg-gray-500 transition-colors" 
            title="Toggle Theme"
            onClick={toggleTheme}
          >
            <i className={`text-xl ${theme === 'dark' ? 'ri-sun-line' : 'ri-moon-line'}`}></i>
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <div 
          className="w-64 border-r shrink-0 flex flex-col"
          style={{ 
            backgroundColor: 'var(--color-sidebar)',
            borderColor: 'var(--color-line)'
          }}
        >
          <div className="flex-1 p-4">
            <Navigation activeView={activeView} onViewChange={onViewChange} />
          </div>
          {/* Copyright in sidebar bottom */}
          <div 
            className="px-4 py-3 border-t text-xs"
            style={{ 
              borderColor: 'var(--color-line)',
              color: 'var(--color-muted)'
            }}
          >
            <div className="flex items-center gap-1">
              <i className="ri-copyright-line"></i>
              <span>2025 Cognitive Network Solutions</span>
            </div>
          </div>
        </div>

        {/* Views Container */}
        <div 
          className="flex-1 overflow-hidden"
          style={{ backgroundColor: 'var(--color-bg)' }}
        >
          {children}
        </div>
      </div>
    </div>
  )
}

