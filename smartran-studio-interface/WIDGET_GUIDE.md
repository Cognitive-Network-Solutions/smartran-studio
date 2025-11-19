# CNS CLI Widget System - Complete Guide

## 📖 Overview

The CNS CLI features a **widget system** that allows full-screen interactive components to take over the CLI output area, similar to how `htop`, `vim`, or `top` work in a terminal. This brings the best of traditional CLI tools to the browser with modern web technologies.

### Key Features

- **Takes over output area** - Like `htop` in a terminal
- **Interactive UI** - Mouse + keyboard navigation
- **Load saved configs** - Quick initialization from saved states
- **Modern styling** - React + Tailwind + CSS variables
- **Theme-aware** - Automatic dark mode support

---

## 🚀 Quick Start

### Using the Init Widget

```bash
# Launch interactive wizard
cns init

# Or use flags to bypass widget
cns init --default                           # All defaults
cns init --config {"n_sites": 5, ...}       # Custom config
```

### Widget Controls

- **Enter**: Advance to next step / Submit
- **Escape**: Cancel and exit
- **← Previous**: Go back to previous step
- **📁 Load Saved**: Toggle saved configurations view
- **Click config**: Load saved configuration

---

## 🎨 Current Widget: Init Wizard

### Features

1. **Step-by-Step Configuration** (14 parameters)
   - Sites, spacing, frequencies, tilts, antennas, UEs
   - Defaults pre-filled
   - Real-time validation

2. **Load Saved Configurations**
   - Click "📁 Load Saved" button
   - Select from previously saved configs
   - One-click initialization

3. **Live Preview**
   - Shows configuration as you build it
   - Only displays values actually set
   - Updates when navigating back

4. **Progress Tracking**
   - Visual progress bar
   - Step X of Y counter
   - Percentage completion

### How It Works

```
User types: cns init
         ↓
Widget takes over output card
Input bar hides
         ↓
User configures parameters
OR selects saved config
         ↓
Widget submits to backend
         ↓
Widget closes, shows formatted result
Input bar returns
```

---

## 🏗️ Architecture

### Widget Lifecycle

1. **Launch**: CLI intercepts `cns init` command
2. **Activate**: `activeWidget` state set to 'init'
3. **Render**: Widget component renders in output card area
4. **Interact**: User completes wizard or loads config
5. **Submit**: Widget calls backend API
6. **Complete**: Widget calls `onComplete` callback
7. **Close**: CLI clears `activeWidget`, shows result

### Integration Points

**Frontend (`CLI.jsx`):**
```jsx
// Intercept command
if (command === 'init' && !hasFlags) {
  setActiveWidget('init')
  return
}

// Render widget in output card
{activeWidget === 'init' ? (
  <InitWizard onComplete={...} onCancel={...} />
) : (
  <pre>{outputs}</pre>
)}
```

**Widget (`InitWizard.jsx`):**
```jsx
// Complete
const handleSubmit = async (config) => {
  const result = await executeCommand(`init --config ${JSON.stringify(config)}`)
  onComplete(result, config)
}

// Cancel
const handleCancel = () => {
  onCancel()
}
```

---

## 📝 Response Formatting

Responses are formatted like `cns status` - structured sections, not JSON dumps:

```
✓ Simulation Initialized

Network Configuration:
  Sites:            10
  Cells:            60
  High Band Cells:  30
  Low Band Cells:   30
  UEs:              30,000

Site Layout:
  Spacing:          500 m
  Height:           20 m
  Seed:             7

High Band:
  Frequency:        2.5 GHz
  Tilt:             9°
  Antenna:          8x1
  Pattern:          38.901

Low Band:
  Frequency:        0.6 GHz
  Tilt:             9°
  Antenna:          8x1
  Pattern:          38.901

UE Configuration:
  Count:            30,000
  Box Padding:      250 m

Processing:
  Cells Chunk:      48
  UE Chunk:         500

Simulation ready! Try 'cns sim compute' to run your first calculation.
```

---

## 🔧 Creating New Widgets

### 1. Create Widget Component

```jsx
// interface_frontend/src/components/widgets/MyWidget.jsx
import React, { useState } from 'react'
import { executeCommand } from '../../utils/api'

export default function MyWidget({ onComplete, onCancel }) {
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async () => {
    setIsSubmitting(true)
    try {
      const result = await executeCommand('my-command')
      onComplete(result)
    } catch (err) {
      console.error(err)
    }
  }

  return (
    <div className="h-full w-full flex flex-col overflow-hidden">
      <div className="flex-1 flex flex-col overflow-hidden"
           style={{ backgroundColor: 'var(--color-surface)' }}>
        
        {/* Header */}
        <div className="shrink-0 px-8 py-6 border-b-2"
             style={{ 
               backgroundColor: 'var(--color-surface-elevated)',
               borderColor: 'var(--color-line)'
             }}>
          <h1 style={{ color: 'var(--color-ink)' }}>My Widget</h1>
        </div>

        {/* Content - Scrollable */}
        <div className="flex-1 overflow-y-auto px-8 py-8">
          {/* Your content */}
        </div>

        {/* Footer */}
        <div className="shrink-0 px-8 py-6 border-t-2"
             style={{ 
               backgroundColor: 'var(--color-surface-elevated)',
               borderColor: 'var(--color-line)'
             }}>
          <button onClick={handleSubmit}>Submit</button>
          <button onClick={onCancel}>Cancel</button>
        </div>
      </div>
    </div>
  )
}
```

### 2. Integrate in CLI

```jsx
// interface_frontend/src/views/CLI.jsx

// Import
import MyWidget from '../components/widgets/MyWidget'

// Intercept command in handleSubmit
if (command === 'my-command') {
  setCommandHistory(prev => [...prev, 'my-command'])
  setActiveWidget('my-widget')
  return
}

// Add handlers
const handleMyWidgetComplete = (result) => {
  setActiveWidget(null)
  setOutputs(prev => [...prev, 
    { type: 'command', content: `> my-command\n` },
    { type: 'response', content: result }
  ])
}

const handleMyWidgetCancel = () => {
  setActiveWidget(null)
  setOutputs(prev => [...prev, { 
    type: 'text', 
    content: 'Operation cancelled' 
  }])
}

// Render widget
{activeWidget === 'my-widget' ? (
  <MyWidget 
    onComplete={handleMyWidgetComplete}
    onCancel={handleMyWidgetCancel}
  />
) : activeWidget === 'init' ? (
  <InitWizard ... />
) : (
  <pre>{outputs}</pre>
)}
```

### 3. Styling Guidelines

**Use CSS Variables** (theme-aware):
```jsx
style={{
  backgroundColor: 'var(--color-surface)',
  color: 'var(--color-text)',
  borderColor: 'var(--color-line)'
}}
```

**Available Variables:**
- `--color-surface` - Main background
- `--color-surface-elevated` - Elevated surfaces (headers, footers)
- `--color-ink` - Primary text
- `--color-text` - Secondary text
- `--color-muted` - Disabled/muted text
- `--color-line` - Borders
- `--color-accent` - Primary accent (blue)
- `--color-success` - Success state (green)
- `--color-error` - Error state (red)
- `--color-warning` - Warning state (orange)
- `--color-info` - Info state (cyan)

---

## 🎯 Best Practices

### Layout

1. **Use flexbox** for three-panel layout (header/content/footer)
2. **Header**: `shrink-0` (fixed height)
3. **Content**: `flex-1 overflow-y-auto` (scrollable)
4. **Footer**: `shrink-0` (fixed height)

### Behavior

1. **Save to history** immediately when launching widget
2. **Handle Escape key** for cancellation
3. **Show loading states** during API calls
4. **Validate input** before submission
5. **Clear error states** when user corrects input

### Accessibility

1. **Keyboard navigation** - Support Enter, Escape, Tab
2. **Focus management** - Auto-focus important inputs
3. **Clear labels** - Descriptive text for all inputs
4. **Error messages** - Clear, actionable feedback

---

## 🧪 Testing

### Basic Tests

```bash
# Launch widget
cns init

# Check:
- [ ] Widget takes over output area
- [ ] Input bar hidden
- [ ] Border turns accent color
- [ ] Progress bar shows

# Navigate
[Enter through steps]

# Check:
- [ ] Values saved correctly
- [ ] Preview updates
- [ ] Progress bar updates

# Complete
[Finish wizard]

# Check:
- [ ] Widget closes
- [ ] Formatted response shows
- [ ] Input bar returns
- [ ] Command in history (up arrow)

# Cancel
cns init
[Press Escape]

# Check:
- [ ] Widget closes immediately
- [ ] "Cancelled" message
- [ ] Command in history
```

### Saved Configs Test

```bash
# Save a config
cns init --default
cns config save test-config

# Load via widget
cns init
[Click "📁 Load Saved"]

# Check:
- [ ] Saved configs list appears
- [ ] Config metadata shown
- [ ] Click config loads it
- [ ] Simulation initializes
```

---

## 📊 Comparison: Before & After

### Before (Text Wizard)
- ASCII box characters
- Linear flow only
- No preview
- Plain text output
- Command lost if cancelled

### After (Widget)
- Modern React UI
- Navigate back/forward freely
- Live configuration preview
- Structured, formatted output
- Command saved even if cancelled
- Load from saved configs

---

## 🔮 Future Widgets

With the framework in place, future widgets are easy to add:

1. **Site Placement Widget**
   - Interactive map
   - Click to place sites
   - Drag to move
   - Visual coverage preview

2. **Antenna Configuration Widget**
   - 3D antenna pattern visualization
   - Slider controls
   - Real-time pattern updates

3. **Query Builder Widget**
   - Drag-and-drop filters
   - Multi-select options
   - Preview result count

4. **Results Viewer Widget**
   - Interactive data exploration
   - Charts and visualizations
   - Export options

---

## 📝 File Structure

```
interface_frontend/
└── src/
    ├── components/
    │   └── widgets/
    │       └── InitWizard.jsx          # Init widget component
    ├── views/
    │   └── CLI.jsx                     # CLI with widget integration
    └── styles/
        └── index.css                   # Theme variables

interface_backend/
└── commands/
    └── initialization.py               # Backend init command
```

---

## 🎓 Summary

**What We Built:**
- Full-screen interactive widget system
- Init wizard with 14 configurable parameters
- Load saved configurations feature
- Structured response formatting
- Command history integration
- Modern, theme-aware UI

**How It Works:**
- Widgets take over output card (like htop)
- Input bar hides during widget
- Backend returns structured responses
- Frontend renders with framework styling

**Best of Both Worlds:**
- CLI speed and efficiency
- Modern web UI capabilities
- Traditional terminal feel
- Browser-native advantages

---

**The widget system is production-ready and extensible!** 🚀

