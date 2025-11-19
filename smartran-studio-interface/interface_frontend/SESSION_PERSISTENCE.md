# Session Persistence

## Overview

The CNS Interface now maintains a **persistent session** across tab switches and page refreshes (within the same browser session).

## How It Works

### 1. View Persistence (Tab Switching)
All views stay **mounted** but hidden when you switch tabs:

```jsx
// Views never unmount - just toggle visibility
<div style={{ display: activeView === 'cli' ? 'block' : 'none' }}>
  <CLI />
</div>
<div style={{ display: activeView === 'map' ? 'block' : 'none' }}>
  <NetworkMap />
</div>
```

**Benefits:**
- ✅ CLI output persists when you switch to Map and back
- ✅ Map state (zoom, pan, selections) persists when you switch to CLI and back
- ✅ No re-initialization on tab switch
- ✅ Feels like one continuous session

### 2. Session Storage (Page Refresh)
CLI state is saved to browser's `sessionStorage`:

```javascript
// Auto-save on every change
useEffect(() => {
  sessionStorage.setItem('cns-cli-outputs', JSON.stringify(outputs))
}, [outputs])

useEffect(() => {
  sessionStorage.setItem('cns-cli-history', JSON.stringify(commandHistory))
}, [commandHistory])

// Auto-load on component mount
const [outputs, setOutputs] = useState(() => {
  const saved = sessionStorage.getItem('cns-cli-outputs')
  return saved ? JSON.parse(saved) : [WELCOME_MESSAGE]
})
```

**Benefits:**
- ✅ CLI output survives page refresh (F5)
- ✅ Command history preserved
- ✅ Automatic - no user action needed
- ✅ Clears when you close the tab/browser

## User Experience

### Switching Tabs
1. Execute commands in CLI (e.g., `query cells`)
2. Switch to Network Map
3. View your cells on the map
4. **Switch back to CLI** → All your output is still there!
5. Use arrow keys to recall previous commands

### Refreshing Page
1. Execute commands in CLI
2. Press F5 or refresh browser
3. **All output and history restored**
4. Continue where you left off

### Starting Fresh
To clear your session:
- Type `clear` or `cns clear` in CLI
- Close the browser tab (clears sessionStorage)
- Open in new tab/window

## Technical Details

### sessionStorage vs localStorage

We use `sessionStorage` instead of `localStorage`:

| Feature | sessionStorage | localStorage |
|---------|---------------|--------------|
| Lifetime | Browser tab/window | Forever (until cleared) |
| Scope | Single tab | All tabs |
| Our Choice | ✅ Yes | ❌ No |

**Why sessionStorage?**
- Each workspace session is independent
- Doesn't clutter browser storage
- Natural "session" concept
- Automatically cleans up

### What's Persisted

**CLI:**
- ✅ All command output
- ✅ Command history (arrow up/down)
- ✅ Welcome message
- ❌ Current input text (intentionally - starts fresh)

**Network Map:**
- ✅ Pan position
- ✅ Zoom level
- ✅ Selected cell
- ✅ Loaded cell data
(Persists through tab switches via component staying mounted)

## Storage Keys

```javascript
// CLI outputs
'cns-cli-outputs' → JSON array of output objects

// CLI command history
'cns-cli-history' → JSON array of command strings
```

## Memory Management

- **Size**: Typical session < 1MB (well within 5-10MB limit)
- **Cleanup**: Automatic on tab close
- **Clear**: Use `clear` command or refresh with new session

## Benefits

1. **Natural Workflow**
   - Check CLI status
   - View on map
   - Back to CLI seamlessly

2. **No Lost Work**
   - Accidental refresh? No problem
   - Quick switch between views
   - Continuous context

3. **Better UX**
   - Feels like desktop app
   - One session, multiple views
   - Professional behavior

## Future Enhancements

Potential additions:
- [ ] Save/load named sessions
- [ ] Export session history
- [ ] Session sharing (via URL)
- [ ] Cross-tab sync (if needed)

---

**Note**: This is browser session persistence, not database persistence. Closing all tabs will clear the session data.

