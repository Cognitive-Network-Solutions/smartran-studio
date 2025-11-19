import React from 'react'

/**
 * Renderer utilities for CLI output
 * Converts backend responses into React components
 */

export function renderResponse(response) {
  const responseType = response.data?.response_type || 'text'
  const content = responseType === 'table' && response.data?.table_data 
    ? response.data.table_data 
    : response.result
  const metadata = response.data?.metadata

  switch (responseType) {
    case 'text':
      return <pre>{content}</pre>
    
    case 'table':
      return renderTable(content, metadata)
    
    case 'error':
      return (
        <div className="cli-error">
          {!content.includes('❌') && <span className="error-icon">❌ </span>}
          <span>{content}</span>
        </div>
      )
    
    case 'success':
      return (
        <div className="cli-success">
          {!content.includes('✓') && <span className="success-icon">✓ </span>}
          <span>{content}</span>
        </div>
      )
    
    case 'info':
      return <div className="cli-info">{content}</div>
    
    case 'warning':
      return <div className="cli-warning">{content}</div>
    
    case 'json':
      return (
        <pre className="json-output">
          {typeof content === 'string' 
            ? content 
            : JSON.stringify(JSON.parse(content), null, 2)
          }
        </pre>
      )
    
    case 'code':
      return (
        <pre className="code-output" data-language={metadata?.language}>
          <code className={metadata?.language ? `language-${metadata.language}` : ''}>
            {content}
          </code>
        </pre>
      )
    
    case 'list':
      return renderList(content, metadata)
    
    case 'progress':
      return renderProgress(content, metadata)
    
    case 'chart':
      return (
        <div className="chart-container">
          <div className="chart-title">{metadata?.title || 'Chart'}</div>
          <div className="chart-placeholder">
            <i className="ri-bar-chart-line"></i>
            <p>Chart rendering not yet implemented</p>
          </div>
        </div>
      )
    
    case 'interactive':
      return (
        <div className="cli-interactive">
          <pre>{content}</pre>
        </div>
      )
    
    default:
      return <pre>{content}</pre>
  }
}

function renderTable(content, metadata) {
  if (typeof content === 'object' && content.headers && content.rows) {
    return (
      <div>
        {content.title && (
          <div style={{ marginBottom: '0.5rem', fontWeight: '600' }}>
            {content.title}
          </div>
        )}
        <table className="cli-table">
          <thead>
            <tr>
              {content.headers.map((header, i) => (
                <th key={i}>{header}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {content.rows.map((row, i) => (
              <tr key={i}>
                {row.map((cell, j) => (
                  <td key={j}>{cell}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        {content.footer && (
          <div style={{ marginTop: '0.5rem', color: 'var(--muted)' }}>
            {content.footer}
          </div>
        )}
      </div>
    )
  }
  
  return <pre>{typeof content === 'string' ? content : JSON.stringify(content)}</pre>
}

function renderList(content, metadata) {
  const items = content.split('\n').filter(line => line.trim())
  const isNumbered = metadata?.numbered || false
  
  return (
    <div className="cli-list">
      {items.map((item, index) => (
        <div key={index} className="cli-list-item">
          <span className="cli-list-bullet">
            {isNumbered ? `${index + 1}.` : '•'}
          </span>
          <span>{item}</span>
        </div>
      ))}
    </div>
  )
}

function renderProgress(content, metadata) {
  const percentage = metadata?.percentage || 0
  
  return (
    <div className="cli-progress">
      <div className="cli-progress-label">
        <span>{metadata?.label || 'Progress'}</span>
        <span>{percentage}%</span>
      </div>
      <div className="cli-progress-bar">
        <div 
          className={`cli-progress-fill ${metadata?.animated ? 'animated' : ''}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}

