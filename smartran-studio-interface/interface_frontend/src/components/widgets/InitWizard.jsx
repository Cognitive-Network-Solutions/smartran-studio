import React, { useState, useEffect } from 'react'
import { executeCommand, apiRequest } from '../../utils/api'

/**
 * InitWizard - Full-screen interactive initialization wizard
 * Takes over the CLI view like htop/vim do in a terminal
 */
const WIZARD_STEPS = [
  { param: 'n_sites', label: 'Number of Sites', default: 10, type: 'number', description: 'Number of cell sites to create', min: 0 },
  { param: 'spacing', label: 'Site Spacing (m)', default: 500, type: 'number', description: 'Target inter-site spacing in meters', min: 1 },
  { param: 'seed', label: 'Random Seed', default: 7, type: 'number', description: 'Random seed for site placement and UE drop' },
  { param: 'site_height_m', label: 'Site Height (m)', default: 20, type: 'number', description: 'Height of cell sites in meters', min: 1 },
  { param: 'fc_hi_hz', label: 'High Band Frequency (Hz)', default: 2500e6, type: 'number', description: 'High band carrier frequency' },
  { param: 'tilt_hi_deg', label: 'High Band Tilt (°)', default: 9, type: 'number', description: 'Antenna tilt angle for high band' },
  { param: 'bs_rows_hi', label: 'High Band Rows', default: 8, type: 'number', description: 'Antenna array rows for high band', min: 1 },
  { param: 'bs_cols_hi', label: 'High Band Columns', default: 1, type: 'number', description: 'Antenna array columns for high band', min: 1 },
  { param: 'fc_lo_hz', label: 'Low Band Frequency (Hz)', default: 600e6, type: 'number', description: 'Low band carrier frequency' },
  { param: 'tilt_lo_deg', label: 'Low Band Tilt (°)', default: 9, type: 'number', description: 'Antenna tilt angle for low band' },
  { param: 'bs_rows_lo', label: 'Low Band Rows', default: 8, type: 'number', description: 'Antenna array rows for low band', min: 1 },
  { param: 'bs_cols_lo', label: 'Low Band Columns', default: 1, type: 'number', description: 'Antenna array columns for low band', min: 1 },
  { param: 'num_ue', label: 'Number of UEs', default: 30000, type: 'number', description: 'Number of user equipment to simulate', min: 1 },
  { param: 'box_pad_m', label: 'UE Box Padding (m)', default: 250, type: 'number', description: 'Padding around sites for UE drop area', min: 0 },
]

export default function InitWizard({ onComplete, onCancel }) {
  const [currentStep, setCurrentStep] = useState(0)
  const [config, setConfig] = useState({})
  const [inputValue, setInputValue] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState(null)
  const [showSavedConfigs, setShowSavedConfigs] = useState(false)
  const [savedConfigs, setSavedConfigs] = useState([])
  const [loadingConfigs, setLoadingConfigs] = useState(false)

  const step = WIZARD_STEPS[currentStep]
  const progress = ((currentStep / WIZARD_STEPS.length) * 100).toFixed(0)

  // Fetch saved configs when toggling view
  useEffect(() => {
    if (showSavedConfigs && savedConfigs.length === 0) {
      fetchSavedConfigs()
    }
  }, [showSavedConfigs])

  const fetchSavedConfigs = async () => {
    setLoadingConfigs(true)
    try {
      const result = await executeCommand('config list')
      // Parse the response to extract configs
      // For now, we'll call the API directly for structured data
      const response = await apiRequest('/command', {
        method: 'POST',
        body: JSON.stringify({ command: 'config list' })
      })
      
      // If response has table data, parse it
      if (response.data?.table_data) {
        const configs = response.data.table_data.rows.map(row => ({
          name: row[0],
          created: row[1],
          sites: row[2],
          cells: row[3],
          ues: row[4],
          bands: row[5],
          description: row[6]
        }))
        setSavedConfigs(configs)
      }
    } catch (err) {
      console.error('Error fetching configs:', err)
      setSavedConfigs([])
    } finally {
      setLoadingConfigs(false)
    }
  }

  const handleLoadConfig = async (configName) => {
    setIsSubmitting(true)
    try {
      const result = await executeCommand(`config load ${configName}`)
      onComplete(result, {})  // Config loaded via backend
    } catch (err) {
      setError(err.message)
      setIsSubmitting(false)
    }
  }

  // Initialize input with default value
  useEffect(() => {
    if (step) {
      setInputValue(step.default.toString())
    }
  }, [currentStep])

  const handleNext = () => {
    const value = inputValue === '' ? step.default : parseFloat(inputValue)
    
    // Validation
    if (isNaN(value)) {
      setError('Please enter a valid number')
      return
    }
    if (step.min !== undefined && value < step.min) {
      setError(`Value must be at least ${step.min}`)
      return
    }
    
    setError(null)
    setConfig(prev => ({ ...prev, [step.param]: value }))
    
    if (currentStep < WIZARD_STEPS.length - 1) {
      setCurrentStep(prev => prev + 1)
    } else {
      // Final step - submit
      handleSubmit({ ...config, [step.param]: value })
    }
  }

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(prev => prev - 1)
      setError(null)
    }
  }

  const handleSubmit = async (finalConfig) => {
    setIsSubmitting(true)
    try {
      const result = await executeCommand(`init --config ${JSON.stringify(finalConfig)}`)
      onComplete(result, finalConfig)
    } catch (err) {
      setError(err.message)
      setIsSubmitting(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !isSubmitting) {
      handleNext()
    } else if (e.key === 'Escape') {
      onCancel()
    }
  }

  return (
    <div className="h-full w-full flex flex-col overflow-hidden">
      
      {/* Main Widget Container - No border, parent has it */}
      <div className="flex-1 flex flex-col overflow-hidden"
           style={{ 
             backgroundColor: 'var(--color-surface)'
           }}>
        
        {/* Header */}
        <div className="shrink-0 px-8 py-6 border-b-2"
             style={{ 
               backgroundColor: 'var(--color-surface-elevated)',
               borderColor: 'var(--color-line)'
             }}>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-4">
              <h1 className="text-2xl font-bold" style={{ color: 'var(--color-ink)' }}>
                🚀 CNS Simulation Initialization
              </h1>
              <button
                onClick={() => setShowSavedConfigs(!showSavedConfigs)}
                className="px-3 py-1 text-sm rounded-lg font-medium transition-colors"
                style={{
                  backgroundColor: showSavedConfigs ? 'var(--color-accent)' : 'rgba(37, 99, 235, 0.1)',
                  color: showSavedConfigs ? 'white' : 'var(--color-accent)',
                  border: `1px solid ${showSavedConfigs ? 'var(--color-accent)' : 'rgba(37, 99, 235, 0.3)'}`
                }}
              >
                {showSavedConfigs ? '← Back to Wizard' : '📁 Load Saved'}
              </button>
            </div>
            <button
              onClick={onCancel}
              className="px-4 py-2 rounded-lg text-sm font-medium transition-colors"
              style={{
                backgroundColor: 'rgba(220, 38, 38, 0.1)',
                color: 'var(--color-error)',
                border: '1px solid rgba(220, 38, 38, 0.3)'
              }}
            >
              ✕ Cancel (Esc)
            </button>
          </div>
          
          {/* Progress Bar - Only show in wizard mode */}
          {!showSavedConfigs && (
            <div>
              <div className="flex justify-between text-sm mb-2" style={{ color: 'var(--color-muted)' }}>
                <span>Step {currentStep + 1} of {WIZARD_STEPS.length}</span>
                <span>{progress}% Complete</span>
              </div>
              <div className="h-2 rounded-full overflow-hidden"
                   style={{ backgroundColor: 'var(--color-line)' }}>
                <div 
                  className="h-full transition-all duration-300"
                  style={{ 
                    width: `${progress}%`,
                    backgroundColor: 'var(--color-accent)'
                  }}
                />
              </div>
            </div>
          )}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-8 py-8">
          {isSubmitting ? (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-16 w-16 border-4"
                   style={{ 
                     borderColor: 'var(--color-line)',
                     borderTopColor: 'var(--color-accent)'
                   }} />
              <p className="mt-4 text-lg" style={{ color: 'var(--color-text)' }}>
                {showSavedConfigs ? 'Loading configuration...' : 'Initializing simulation...'}
              </p>
            </div>
          ) : showSavedConfigs ? (
            // Saved Configs View
            <div>
              <h2 className="text-xl font-semibold mb-4" style={{ color: 'var(--color-ink)' }}>
                📁 Saved Configurations
              </h2>
              <p className="text-sm mb-6" style={{ color: 'var(--color-muted)' }}>
                Select a configuration to load and initialize the simulation.
              </p>

              {loadingConfigs ? (
                <div className="text-center py-8">
                  <div className="inline-block animate-spin rounded-full h-12 w-12 border-4"
                       style={{ 
                         borderColor: 'var(--color-line)',
                         borderTopColor: 'var(--color-accent)'
                       }} />
                  <p className="mt-4" style={{ color: 'var(--color-text)' }}>
                    Loading configurations...
                  </p>
                </div>
              ) : savedConfigs.length === 0 ? (
                <div className="text-center py-12 rounded-lg"
                     style={{ 
                       backgroundColor: 'var(--color-surface-elevated)',
                       border: '1px solid var(--color-line)'
                     }}>
                  <p className="text-lg mb-2" style={{ color: 'var(--color-text)' }}>
                    No saved configurations found
                  </p>
                  <p className="text-sm" style={{ color: 'var(--color-muted)' }}>
                    Complete the wizard to create your first configuration,<br />
                    then use "cns config save &lt;name&gt;" to save it.
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {savedConfigs.map((cfg, idx) => (
                    <div
                      key={idx}
                      onClick={() => handleLoadConfig(cfg.name)}
                      className="p-4 rounded-lg border-2 cursor-pointer transition-all"
                      style={{
                        backgroundColor: 'var(--color-surface-elevated)',
                        borderColor: 'var(--color-line)',
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.borderColor = 'var(--color-accent)'
                        e.currentTarget.style.backgroundColor = 'rgba(37, 99, 235, 0.05)'
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.borderColor = 'var(--color-line)'
                        e.currentTarget.style.backgroundColor = 'var(--color-surface-elevated)'
                      }}
                    >
                      <div className="flex justify-between items-start mb-2">
                        <h3 className="text-lg font-semibold" style={{ color: 'var(--color-ink)' }}>
                          {cfg.name}
                        </h3>
                        <span className="text-xs px-2 py-1 rounded"
                              style={{
                                backgroundColor: 'rgba(37, 99, 235, 0.1)',
                                color: 'var(--color-accent)'
                              }}>
                          Click to load
                        </span>
                      </div>
                      <div className="space-y-1 text-sm mb-2">
                        <div className="flex justify-between">
                          <span style={{ color: 'var(--color-muted)' }}>Sites:</span>
                          <span style={{ color: 'var(--color-text)' }}>{cfg.sites}</span>
                        </div>
                        <div className="flex justify-between">
                          <span style={{ color: 'var(--color-muted)' }}>Cells:</span>
                          <span style={{ color: 'var(--color-text)' }}>{cfg.cells}</span>
                        </div>
                        <div className="flex justify-between">
                          <span style={{ color: 'var(--color-muted)' }}>UEs:</span>
                          <span style={{ color: 'var(--color-text)' }}>{cfg.ues}</span>
                        </div>
                        <div className="flex justify-between">
                          <span style={{ color: 'var(--color-muted)' }}>Bands:</span>
                          <span style={{ color: 'var(--color-text)' }}>{cfg.bands || 'N/A'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span style={{ color: 'var(--color-muted)' }}>Created:</span>
                          <span style={{ color: 'var(--color-text)' }}>{cfg.created}</span>
                        </div>
                      </div>
                      {cfg.description && (
                        <p className="text-sm italic" style={{ color: 'var(--color-muted)' }}>
                          {cfg.description}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            // Wizard View
            <>
              {/* Step Info */}
              <div className="mb-8">
                <h2 className="text-xl font-semibold mb-2" style={{ color: 'var(--color-ink)' }}>
                  {step.label}
                </h2>
                <p className="text-sm" style={{ color: 'var(--color-muted)' }}>
                  {step.description}
                </p>
              </div>

              {/* Input */}
              <div className="mb-8">
                <label className="block text-sm font-medium mb-2" style={{ color: 'var(--color-text)' }}>
                  Enter value (default: {step.default})
                </label>
                <input
                  type="text"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyDown={handleKeyPress}
                  autoFocus
                  className="w-full px-4 py-3 rounded-lg text-lg font-mono border-2 outline-none transition-colors"
                  style={{
                    backgroundColor: 'var(--color-surface)',
                    borderColor: error ? 'var(--color-error)' : 'var(--color-line)',
                    color: 'var(--color-ink)'
                  }}
                  placeholder={step.default.toString()}
                />
                {error && (
                  <p className="mt-2 text-sm" style={{ color: 'var(--color-error)' }}>
                    ⚠️ {error}
                  </p>
                )}
              </div>

              {/* Configuration Preview - Only show values actually set */}
              {Object.keys(config).length > 0 && (
                <div className="rounded-lg p-4 mb-6"
                     style={{ 
                       backgroundColor: 'var(--color-surface-elevated)',
                       border: '1px solid var(--color-line)'
                     }}>
                  <h3 className="text-sm font-semibold mb-3" style={{ color: 'var(--color-text)' }}>
                    📋 Configuration So Far
                  </h3>
                  <div className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm font-mono">
                    {Object.entries(config).map(([key, value]) => {
                      const stepInfo = WIZARD_STEPS.find(s => s.param === key)
                      return (
                        <div key={key} className="flex justify-between">
                          <span style={{ color: 'var(--color-muted)' }}>{stepInfo?.label}:</span>
                          <span style={{ color: 'var(--color-accent)' }}>{value}</span>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer - Navigation */}
        {!isSubmitting && (
          <div className="shrink-0 px-8 py-6 border-t-2 flex justify-between"
               style={{ 
                 backgroundColor: 'var(--color-surface-elevated)',
                 borderColor: 'var(--color-line)'
               }}>
            <button
              onClick={handlePrevious}
              disabled={currentStep === 0}
              className="px-6 py-3 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              style={{
                backgroundColor: 'var(--color-surface)',
                color: 'var(--color-text)',
                border: '1px solid var(--color-line)'
              }}
            >
              ← Previous
            </button>
            
            <button
              onClick={handleNext}
              className="px-6 py-3 rounded-lg font-medium transition-colors"
              style={{
                backgroundColor: 'var(--color-accent)',
                color: 'white',
                border: '1px solid var(--color-accent)'
              }}
            >
              {currentStep === WIZARD_STEPS.length - 1 ? '✓ Initialize' : 'Next →'}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

