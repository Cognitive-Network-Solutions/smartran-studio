# 🚀 CLI Framework Quick Reference

## 📖 What Is This Framework?

**4 Simple Concepts:**

1. **Backend:** Use `@command` decorator → commands auto-register (no giant if/elif)
2. **Frontend:** Use `response_type` → automatic rendering (no string detection)
3. **CSS:** Use theme variables → automatic dark mode (no hardcoded colors)
4. **Widgets:** Full-screen React components → interactive CLI programs (like htop/vim)

---

## 📝 Adding a New Command

```python
# commands/my_command.py
from typing import List
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from framework import command, CommandResponse, ResponseType, ArgumentParser

@command(
    name="my command",                        # What user types: "cns my command"
    description="Short description",           # Shows in help list
    usage="cns my command [--flag value]",     # Usage hint
    response_type=ResponseType.SUCCESS         # Output type (colors/styling)
)
async def cmd_my_command(args: List[str]) -> CommandResponse:
    # 1. Parse arguments
    parser = ArgumentParser(valid_flags={
        'name': str,      # --name "value"
        'count': int,     # --count 42
        'enable': bool    # --enable
    })
    parsed_args, _ = parser.parse_arguments(args)
    
    # 2. Handle --help
    if parsed_args.help:
        return CommandResponse(
            content="Detailed help text...",
            response_type=ResponseType.TEXT
        )
    
    # 3. Do your business logic
    result = await api_request("GET", "/endpoint")
    
    # 4. Return response
    return CommandResponse(
        content="Success!",
        response_type=ResponseType.SUCCESS
    )
```

**Then import in `backend.py`:**
```python
from commands.my_command import cmd_my_command
```

**Done!** Type `cns my command` and it works.

---

## 🎨 Response Types

### Simple Text
```python
return CommandResponse(
    content="Plain text",
    response_type=ResponseType.TEXT
)
```

### Table
```python
from framework import TableData

return CommandResponse(
    content=TableData(
        headers=["Col1", "Col2", "Col3"],
        rows=[
            ["value1", "value2", "value3"],
            ["value4", "value5", "value6"]
        ]
    ),
    response_type=ResponseType.TABLE,
    header="Found 2 results"  # Optional header
)
```

### Error (Red)
```python
return CommandResponse(
    content="Something went wrong",
    response_type=ResponseType.ERROR,
    exit_code=1
)
```

### Success (Green)
```python
return CommandResponse(
    content="Operation completed!",
    response_type=ResponseType.SUCCESS
)
```

### Info (Blue)
```python
return CommandResponse(
    content="FYI: This is informational",
    response_type=ResponseType.INFO
)
```

### Warning (Yellow)
```python
return CommandResponse(
    content="Warning: Be careful",
    response_type=ResponseType.WARNING
)
```

### All Available Types
- `TEXT` - Plain text
- `TABLE` - Structured tables
- `JSON` - Syntax-highlighted JSON
- `ERROR` - Red error messages
- `SUCCESS` - Green success messages
- `INFO` - Blue informational
- `WARNING` - Yellow warnings
- `CODE` - Code blocks
- `PROGRESS` - Progress bars
- `LIST` - Formatted lists
- `INTERACTIVE` - Interactive prompts
- `CHART` - Visualizations

---

## 🔧 Argument Parser

### Define & Parse
```python
parser = ArgumentParser(valid_flags={
    'name': str,      # String value
    'count': int,     # Integer value
    'enable': bool,   # Boolean flag
    'ratio': float    # Float value
})

parsed_args, positional_args = parser.parse_arguments(args)

# Access parsed flags
name = parsed_args.name or "default"  # Provide default if not given
count = parsed_args.count or 0
enable = parsed_args.enable or False
```

### Supported Flag Formats
```bash
cns command --flag value
cns command --flag=value
cns command --flag-name "multi word"
cns command --enable           # Boolean (no value needed)
```

---

## 🎨 Frontend: Custom Renderer

```javascript
// renderer-registry.js - add in registerDefaultRenderers()

this.registerRenderer('my_type', (content, metadata) => {
    const div = document.createElement('div');
    div.className = 'cli-my-type';  // CSS class for styling
    div.textContent = content;       // Use textContent (XSS safe!)
    return div;
});
```

**Then add CSS:**
```css
/* framework-renderer-styles.css */
.cli-my-type {
    background: var(--surface-elevated);  /* Use theme variables */
    color: var(--text-primary);
    padding: 1rem;
    border-radius: var(--radius-md);
}
```

---

## 🎨 Theme Variables (Available in CSS)

### Colors
```css
var(--text-primary)      /* Main text */
var(--text-secondary)    /* Muted text */
var(--surface)           /* Background */
var(--surface-elevated)  /* Raised background */
var(--border)            /* Border color */
var(--error)             /* Error color (auto-switches light/dark) */
var(--success)           /* Success color */
var(--info)              /* Info color */
var(--warning)           /* Warning color */
```

### Spacing
```css
var(--radius-sm)         /* Small border radius */
var(--radius-md)         /* Medium border radius */
var(--radius-lg)         /* Large border radius */
```

**All variables automatically adapt to light/dark mode!**

---

## ✅ Checklist: New Command

- [ ] Create `commands/your_command.py`
- [ ] Use `@command()` decorator
- [ ] Use `ArgumentParser` for flags
- [ ] Handle `--help` flag
- [ ] Choose appropriate `ResponseType`
- [ ] Import in `backend.py`
- [ ] Test: `cns your command`
- [ ] Test: `cns your command --help`

---

## 📦 Available Imports

```python
# Backend
from framework import (
    command,              # Decorator
    CommandResponse,      # Response model
    ResponseType,         # Enum of types
    TableData,            # Table data model
    ArgumentParser        # Argument parser
)
```

```javascript
// Frontend
import { rendererRegistry } from './renderer-registry.js';
```

---

## 🐛 Common Mistakes

### ❌ DON'T: Return HTML strings
```python
return CommandResponse(result='<table>...</table>')  # OLD WAY
```

### ✅ DO: Return structured data
```python
return CommandResponse(
    content=TableData(headers=[...], rows=[...]),
    response_type=ResponseType.TABLE
)
```

### ❌ DON'T: Manual argument parsing
```python
for arg in args:
    if arg.startswith('--'):  # Manual parsing
        key, value = arg[2:].split('=')
```

### ✅ DO: Use ArgumentParser
```python
parser = ArgumentParser(valid_flags={'key': str})
parsed_args, _ = parser.parse_arguments(args)
```

### ❌ DON'T: Hardcoded colors
```css
.my-class { color: #ff0000; }  /* Breaks in dark mode */
```

### ✅ DO: Use theme variables
```css
.my-class { color: var(--error); }  /* Auto dark mode */
```

---

## 🎨 Adding Interactive Widgets

**Widgets are full-screen React components that take over the CLI (like htop, vim, top).**

### Creating a Widget

```jsx
// components/widgets/MyWidget.jsx
export default function MyWidget({ onComplete, onCancel }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" 
         style={{ backgroundColor: 'rgba(0, 0, 0, 0.8)' }}>
      <div className="w-full max-w-4xl rounded-xl"
           style={{ 
             backgroundColor: 'var(--color-surface)',
             border: '2px solid var(--color-accent)'
           }}>
        {/* Your interactive UI */}
        <button onClick={() => onComplete(result)}>Done</button>
        <button onClick={onCancel}>Cancel (Esc)</button>
      </div>
    </div>
  )
}
```

### Integrating Widget

```jsx
// views/CLI.jsx

// 1. Import
import MyWidget from '../components/widgets/MyWidget'

// 2. Intercept command in handleSubmit
if (command === 'my-command') {
  setActiveWidget('my-widget')
  setInput('')
  return
}

// 3. Add handlers
const handleMyWidgetComplete = (result) => {
  setActiveWidget(null)
  setOutputs(prev => [...prev, { type: 'response', content: result }])
}

// 4. Render widget
{activeWidget === 'my-widget' && (
  <MyWidget onComplete={handleMyWidgetComplete} onCancel={...} />
)}
```

**📖 For detailed widget documentation, see: `docs/WIDGET_SYSTEM.md`**

---

## 📚 Examples

**See working examples in:**
- `commands/connection.py` - Simple commands (help, status)
- `commands/query.py` - Table commands (query cells, sites, ues)
- `components/widgets/InitWizard.jsx` - Full-screen interactive widget

---

**That's it! Framework = 4 things: @command decorator, response types, theme variables, and widgets.** 🎯
