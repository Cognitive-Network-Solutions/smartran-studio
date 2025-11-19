/**
 * API Client Utility
 * Centralized API communication with better error handling and configuration
 */

const API_BASE_URL = '/api'

class APIError extends Error {
  constructor(message, status, data) {
    super(message)
    this.name = 'APIError'
    this.status = status
    this.data = data
  }
}

/**
 * Make an API request
 * @param {string} endpoint - API endpoint (e.g., '/command', '/map/cells')
 * @param {object} options - Fetch options
 * @returns {Promise<any>} Response data
 */
export async function apiRequest(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`
  
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  }
  
  try {
    const response = await fetch(url, config)
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new APIError(
        errorData.message || `HTTP ${response.status}: ${response.statusText}`,
        response.status,
        errorData
      )
    }
    
    return await response.json()
  } catch (error) {
    if (error instanceof APIError) {
      throw error
    }
    
    // Network or other errors
    throw new APIError(
      error.message || 'Network error - please check your connection',
      0,
      { originalError: error }
    )
  }
}

/**
 * Execute a CLI command
 * @param {string} command - Command string
 * @returns {Promise<object>} Command response
 */
export async function executeCommand(command) {
  return apiRequest('/command', {
    method: 'POST',
    body: JSON.stringify({ command }),
  })
}

/**
 * Get map cells data
 * @returns {Promise<object>} Map cells data
 */
export async function getMapCells() {
  return apiRequest('/map/cells', {
    method: 'GET',
  })
}

/**
 * Get simulation status
 * @returns {Promise<object>} Status data
 */
export async function getStatus() {
  return executeCommand('status')
}

