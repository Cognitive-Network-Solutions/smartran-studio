import React from 'react'

/**
 * Navigation Component
 * Sidebar navigation for switching between views
 */
export default function Navigation({ activeView, onViewChange }) {
  const navItems = [
    { id: 'cli', icon: 'ri-terminal-line', label: 'CLI' },
    { id: 'map', icon: 'ri-map-2-line', label: 'Network Map' },
  ]

  return (
    <nav className="flex flex-col gap-2">
      {navItems.map(item => (
        <a
          key={item.id}
          className={`
            flex items-center gap-3 px-4 py-3 rounded-lg transition-all cursor-pointer
            ${activeView === item.id 
              ? 'bg-accent text-white shadow-md' 
              : 'hover:bg-opacity-10 hover:bg-gray-500'
            }
          `}
          style={{
            color: activeView === item.id ? '#ffffff' : 'var(--color-sidebar-ink)'
          }}
          href="#"
          onClick={(e) => {
            e.preventDefault()
            onViewChange(item.id)
          }}
        >
          <i className={`${item.icon} text-xl`}></i>
          <span className="font-medium">{item.label}</span>
        </a>
      ))}
    </nav>
  )
}

