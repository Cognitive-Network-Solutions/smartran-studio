import React, { useState, useRef, useEffect } from 'react'
import { executeCommand } from '../utils/api'
import { renderResponse } from '../utils/renderers'
import InitWizard from '../components/widgets/InitWizard'

/**
 * CLI Component
 * Interactive command-line interface with history and tab completion
 */
const WELCOME_MESSAGE = {
  type: 'text', 
  content: `SmartRAN Studio CLI - Radio Access Network Simulation

Connected to: SmartRAN Studio Simulation Engine

Quick Start:
  srs status                    - Check simulation status
  srs init --default            - Initialize with all defaults
  srs init                      - Interactive wizard (step-by-step)
  srs query cells               - List all cells
  srs query cells --band H      - Query high-band cells
  srs help                      - Show all commands`
}

export default function CLI() {
  const [input, setInput] = useState('')
  // Load outputs from sessionStorage or use welcome message
  const [outputs, setOutputs] = useState(() => {
    const saved = sessionStorage.getItem('smartran-cli-outputs')
    return saved ? JSON.parse(saved) : [WELCOME_MESSAGE]
  })
  // Load command history from sessionStorage
  const [commandHistory, setCommandHistory] = useState(() => {
    const saved = sessionStorage.getItem('smartran-cli-history')
    return saved ? JSON.parse(saved) : []
  })
  const [historyIndex, setHistoryIndex] = useState(null) // null = at the newest (empty input)
  const [tabSuggestions, setTabSuggestions] = useState([])
  const [tabIndex, setTabIndex] = useState(0)
  const [isLoading, setIsLoading] = useState(false)
  const [isWizardMode, setIsWizardMode] = useState(false) // Track if in wizard/interactive mode
  const [activeWidget, setActiveWidget] = useState(null) // Active widget: 'init', null
  
  const inputRef = useRef(null)
  const outputRef = useRef(null)

  // Smart scroll: tables scroll to top, others to bottom
  useEffect(() => {
    if (outputRef.current && outputs.length > 0) {
      const lastOutput = outputs[outputs.length - 1]
      
      // If it's a table response, scroll to show the table at the top
      if (lastOutput.type === 'response' && lastOutput.content?.data?.response_type === 'table') {
        setTimeout(() => {
          const lastElement = outputRef.current.lastElementChild
          if (lastElement) {
            lastElement.scrollIntoView({ behavior: 'smooth', block: 'start' })
          }
        }, 100)
      } else {
        // For other output, scroll to bottom
        outputRef.current.scrollTop = outputRef.current.scrollHeight
      }
    }
  }, [outputs])

  // Focus input on mount and keep it focused
  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  // Keep input focused after output changes
  useEffect(() => {
    if (!isLoading) {
      inputRef.current?.focus()
    }
  }, [outputs, isLoading])

  // Persist outputs to sessionStorage
  useEffect(() => {
    sessionStorage.setItem('smartran-cli-outputs', JSON.stringify(outputs))
  }, [outputs])

  // Persist command history to sessionStorage
  useEffect(() => {
    sessionStorage.setItem('smartran-cli-history', JSON.stringify(commandHistory))
  }, [commandHistory])

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    const command = input.trim()
    
    // Handle clear command
    if (command.toLowerCase() === 'clear') {
      const clearMessage = { 
        type: 'text', 
        content: 'SmartRAN Studio CLI - Ready for commands...\n\nType "help" for available commands' 
      }
      setOutputs([clearMessage])
      sessionStorage.setItem('smartran-cli-outputs', JSON.stringify([clearMessage]))
      setInput('')
      setIsWizardMode(false) // Exit wizard mode
      return
    }

    // Check if this is init without --default or --config -> launch widget
    const normalizedCmd = command.toLowerCase().replace(/^(srs|smartran|cns)\s+/, '')
    if (normalizedCmd === 'init' || normalizedCmd.startsWith('init ')) {
      if (!normalizedCmd.includes('--default') && !normalizedCmd.includes('--config')) {
        // Launch the interactive widget
        // Add to command history immediately (even if cancelled)
        setCommandHistory(prev => [...prev, 'srs init'])
        setActiveWidget('init')
        setInput('')
        return
      }
    }

    // Add to history (but not empty wizard inputs)
    if (command) {
      setCommandHistory(prev => [...prev, command])
      setHistoryIndex(null) // Reset to newest
    }

    // Add command to output
    // In wizard mode with empty input, show a special indicator
    let displayCommand
    if (!command && isWizardMode) {
      displayCommand = '⏎ [Using default]'
    } else {
      displayCommand = command || ''
    }
    
    if (displayCommand) {
    setOutputs(prev => [...prev, { 
      type: 'command', 
      content: `${'═'.repeat(80)}\n> ${displayCommand}\n` 
    }])
    }

    // Show loading
    setIsLoading(true)
    setOutputs(prev => [...prev, { type: 'loading', content: 'Executing...' }])

    try {
      const response = await executeCommand(command)
      
      // Remove loading indicator
      setOutputs(prev => prev.filter(o => o.type !== 'loading'))

      // Handle clear screen marker
      if (response.result === '[CLEAR_SCREEN]') {
        const clearMessage = { 
          type: 'text', 
          content: 'SmartRAN Studio CLI - Ready for commands...\n\nType "help" for available commands' 
        }
        setOutputs([clearMessage])
        setIsWizardMode(false)
      } else {
        // Detect wizard mode from response
        const responseText = response.result || ''
        const isWizardResponse = responseText.includes('INITIALIZATION WIZARD') || 
                                 responseText.includes('Press Enter to use default') ||
                                 responseText.includes('[Step ') ||
                                 (isWizardMode && responseText.includes('→'))
        
        // Check for wizard completion
        const wizardCompleted = responseText.includes('✓ Simulation Initialized') || 
                               responseText.includes('Initialization cancelled')
        
        if (wizardCompleted) {
          setIsWizardMode(false)
        } else if (isWizardResponse) {
          setIsWizardMode(true)
        }
        
        // Add response to output
        setOutputs(prev => [...prev, { type: 'response', content: response }])
      }
    } catch (error) {
      // Remove loading indicator
      setOutputs(prev => prev.filter(o => o.type !== 'loading'))
      
      // Add error to output
      const errorMessage = `❌ Error: ${error.message}\n\nTroubleshooting:\n  1. Check if the backend is running (port 8001)\n  2. Check if the simulation API is running (port 8000)\n  3. Verify Docker containers are up: docker ps\n\nQuick fix:\n  docker-compose up -d`
      setOutputs(prev => [...prev, { type: 'error', content: errorMessage }])
    } finally {
      setIsLoading(false)
      setInput('')
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'ArrowUp') {
      e.preventDefault()
      navigateHistory(-1)
    } else if (e.key === 'ArrowDown') {
      e.preventDefault()
      navigateHistory(1)
    } else if (e.key === 'Tab') {
      e.preventDefault()
      handleTabCompletion()
    } else {
      // Reset tab suggestions and history navigation on any other key
      setTabSuggestions([])
      setTabIndex(0)
      // Don't reset historyIndex here - let onChange handle it
    }
  }

  const handleInputChange = (e) => {
    setInput(e.target.value)
    // Reset history index when user manually types
    if (historyIndex !== null) {
      setHistoryIndex(null)
    }
  }

  const navigateHistory = (direction) => {
    if (commandHistory.length === 0) return
    
    // UP arrow = -1 (go back in time, to older commands)
    // DOWN arrow = +1 (go forward in time, to newer commands)
    
    if (direction === -1) {
      // Arrow UP - go backwards in history
      if (historyIndex === null) {
        // Start from the newest command
        setHistoryIndex(commandHistory.length - 1)
        setInput(commandHistory[commandHistory.length - 1])
      } else if (historyIndex > 0) {
        // Go to older command
        const newIndex = historyIndex - 1
        setHistoryIndex(newIndex)
        setInput(commandHistory[newIndex])
      }
      // If already at oldest (index 0), stay there (no wrap)
    } else if (direction === 1) {
      // Arrow DOWN - go forwards in history
      if (historyIndex === null) {
        // Already at newest, do nothing (no wrap)
        return
      } else if (historyIndex < commandHistory.length - 1) {
        // Go to newer command
        const newIndex = historyIndex + 1
        setHistoryIndex(newIndex)
        setInput(commandHistory[newIndex])
      } else {
        // Reached newest, go back to empty input
        setHistoryIndex(null)
        setInput('')
      }
    }
  }

  const handleTabCompletion = () => {
    const currentInput = input.trim()
    
    // If cycling through suggestions
    if (tabSuggestions.length > 0) {
      const newIndex = (tabIndex + 1) % tabSuggestions.length
      setTabIndex(newIndex)
      setInput(tabSuggestions[newIndex])
      return
    }
    
    // Nothing typed yet
    if (!currentInput) return
    
    // Build suggestions from history
    const historyCommands = [...new Set(commandHistory.slice().reverse())]
    
    // Strategy 1: Exact prefix match
    let suggestions = historyCommands.filter(cmd => 
      cmd.toLowerCase().startsWith(currentInput.toLowerCase())
    )
    
    // Strategy 2: Word boundary matching
    if (suggestions.length === 0) {
      suggestions = historyCommands.filter(cmd => {
        const words = cmd.toLowerCase().split(/\s+/)
        const searchLower = currentInput.toLowerCase()
        return words.some(word => word.startsWith(searchLower))
      })
    }
    
    // Strategy 3: Partial match anywhere
    if (suggestions.length === 0) {
      suggestions = historyCommands.filter(cmd =>
        cmd.toLowerCase().includes(currentInput.toLowerCase())
      )
    }
    
    // Apply first suggestion
    if (suggestions.length > 0) {
      setTabSuggestions(suggestions)
      setTabIndex(0)
      setInput(suggestions[0])
      
      if (suggestions.length > 1) {
        console.log(`Tab completion: ${suggestions.length} matches. Press Tab again to cycle.`)
      }
    }
  }

  const handleWidgetComplete = (result, config) => {
    setActiveWidget(null)
    setIsWizardMode(false)
    
    // Add command and formatted response to output
    // (command already added to history when widget launched)
    setOutputs(prev => [...prev, 
      { type: 'command', content: `${'═'.repeat(80)}\n> srs init\n` },
      { type: 'response', content: result }
    ])
  }

  const handleWidgetCancel = () => {
    setActiveWidget(null)
    setIsWizardMode(false)
    
    // Add cancelled message
    setOutputs(prev => [...prev, { 
      type: 'text', 
      content: '❌ Initialization cancelled by user' 
    }])
  }

  const renderOutput = (output, index) => {
    switch (output.type) {
      case 'text':
        return <pre key={index}>{output.content}</pre>
      case 'command':
        return <pre key={index}>{output.content}</pre>
      case 'loading':
        return <pre key={index} className="loading">{output.content}</pre>
      case 'error':
        return <pre key={index}>{output.content}</pre>
      case 'response':
        return <div key={index}>{renderResponse(output.content)}</div>
      default:
        return <pre key={index}>{output.content}</pre>
    }
  }

  return (
    <div className="h-full w-full flex flex-col overflow-hidden p-6 gap-4">
      {/* Output Card - Shows normal output OR active widget */}
      <div 
        className="flex-1 overflow-hidden rounded-lg border-2 shadow-lg"
        style={{ 
          backgroundColor: 'var(--color-surface)',
          borderColor: activeWidget ? 'var(--color-accent)' : 'var(--color-line)'
        }}
      >
        {activeWidget === 'init' ? (
          // Widget takes over the output area (like htop)
          <InitWizard 
            onComplete={handleWidgetComplete}
            onCancel={handleWidgetCancel}
          />
        ) : (
          // Normal CLI output
          <pre 
            ref={outputRef}
            className="h-full overflow-y-auto px-8 py-6 font-mono text-sm scrollbar-thin cli-output"
            style={{ 
              color: 'var(--color-text)',
              backgroundColor: 'var(--color-surface)'
            }}
          >
            {outputs.map(renderOutput)}
          </pre>
        )}
      </div>

      {/* Input Bar - Hidden when widget is active */}
      {!activeWidget && (
        <div 
          className="shrink-0 rounded-lg border-2 shadow-lg"
          style={{ 
            backgroundColor: 'var(--color-surface)',
            borderColor: 'var(--color-accent)'
          }}
        >
          <form onSubmit={handleSubmit} className="flex items-center gap-3 px-6 py-4">
            <span className="text-accent font-bold text-xl">{isWizardMode ? '→' : '›'}</span>
            <input
              ref={inputRef}
              type="text"
              placeholder={isWizardMode ? "Press Enter for default, or type value..." : "Enter your command..."}
              autoComplete="off"
              autoFocus
              value={input}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              disabled={isLoading}
              className="flex-1 px-0 py-2 font-mono text-base bg-transparent border-0 outline-none"
              style={{ 
                color: 'var(--color-ink)'
              }}
            />
            {isWizardMode && (
              <span 
                className="px-3 py-1 text-xs font-semibold rounded"
                style={{
                  backgroundColor: 'rgba(6, 182, 212, 0.2)',
                  color: 'var(--color-info)',
                  border: '1px solid rgba(6, 182, 212, 0.4)'
                }}
                title="Initialization Wizard Active - Press Enter to use defaults"
              >
                ⚡ WIZARD
              </span>
            )}
          </form>
        </div>
      )}
    </div>
  )
}

