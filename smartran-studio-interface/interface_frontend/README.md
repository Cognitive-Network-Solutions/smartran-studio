# CNS CLI - Frontend & Usage Guide

Web-based command-line interface for CNS network operations.

## 📁 Frontend Structure

```
interface_frontend/
├── index.html              # Main layout & structure
├── app.js                  # Application coordinator (routing, theme)
├── cli.js                  # CLI module (terminal logic)
├── styles.css              # Main styling
├── custom-styles.css       # Table styles & theme overrides
├── cnsLogo_darkmode.png    # Company logo (dark theme)
├── cnsLogo_lightmode.png   # Company logo (light theme)
├── nginx.conf              # Nginx configuration
├── Dockerfile.frontend     # Container definition
└── README.md               # This file
```

## 🎨 Features

✅ **Command History** - Scroll through with ↑/↓ arrows  
✅ **Tab Completion** - Smart completion from command history  
✅ **Dark/Light Themes** - Toggle with sun/moon icon  
✅ **HTML Tables** - Beautiful formatting for query results  
✅ **Smart Scrolling** - Tables scroll to top, commands to bottom  
✅ **Professional Branding** - Theme-aware CNS logos  

## 💻 CLI Commands Reference

### Connection Management

```bash
cns networks               # List available networks
cns connect <network>      # Connect to a network (e.g., sim)
cns status                 # Show connection status
cns help                   # Show all commands
```

### Simulation Initialization

#### Interactive Wizard
```bash
cns init
```
Walks through 14 configuration steps. Press Enter for defaults or type custom values.

#### Quick Init
```bash
cns init --default         # Use all defaults (fastest)
cns init --config {}       # Use all defaults (alternate)
```

#### Custom Init
```bash
cns init --config {"n_sites": 20, "spacing": 600.0, "num_ue": 50000}
```

**Available Parameters:**
- **Site Layout:** `n_sites`, `spacing`, `seed`, `jitter`, `site_height_m`
- **High Band:** `fc_hi_hz`, `tilt_hi_deg`, `bs_rows_hi`, `bs_cols_hi`, `antenna_pattern_hi`
- **Low Band:** `fc_lo_hz`, `tilt_lo_deg`, `bs_rows_lo`, `bs_cols_lo`, `antenna_pattern_lo`
- **UEs:** `num_ue`, `box_pad_m`
- **Chunking:** `cells_chunk`, `ue_chunk`

### Query Commands

#### Query Cells
```bash
cns query cells                           # All cells
cns query cells --band=H                  # High-band only
cns query cells --band=L                  # Low-band only
cns query cells --site-name=CNS0001A      # Specific site
cns query cells --site-name=CNS000*       # Wildcard match
cns query cells --tilt-min=9 --tilt-max=11  # Tilt range
cns query cells --fc-ghz-min=2.0 --fc-ghz-max=3.0  # Frequency range
cns query cells --bs-rows=8 --bs-cols=1   # Antenna config
```

**All Filter Options:**
- `--band=<H|L>` - Band identifier
- `--site-name=<name>` - Site name (supports * wildcard)
- `--sector-id=<0-2>` - Sector ID
- `--site-idx=<n>` - Site index
- `--tilt-min=<deg>` / `--tilt-max=<deg>` - Tilt range
- `--fc-ghz-min=<freq>` / `--fc-ghz-max=<freq>` - Frequency range
- `--bs-rows=<n>` / `--bs-cols=<n>` - Antenna array size
- `--limit=<n>` / `--offset=<n>` - Pagination

#### Query Sites
```bash
cns query sites            # List all sites
```

#### Query UEs
```bash
cns query ues              # Show UE configuration and results
```

### Update Commands

#### Update Single Cell
```bash
cns update cell <id> --tilt=12.0                    # Update tilt
cns update cell 5 --tilt=11.0 --power=3.0           # Multiple params
cns update cell 10 --rows=8 --cols=1                # Antenna config
```

**Update Parameters:**
- `--tilt=<deg>` - Tilt angle
- `--power=<dbm>` - TX power (dBm)
- `--rows=<n>` / `--cols=<n>` - Antenna array
- `--freq=<hz>` - Frequency (Hz)
- `--roll=<deg>` - Roll angle
- `--height=<m>` - Height (meters)

#### Update Multiple Cells (Query-Based)
```bash
cns update cells query --band=H --update-tilt-deg=12.0
cns update cells query --site-name=CNS0001A --update-tilt-deg=11.0 --update-tx-rs-power-dbm=3.0
cns update cells query --site-name=CNS000* --band=H --update-tilt-deg=11.5
cns update cells query --sector-id=0 --update-tilt-deg=10.0
```

**Query Criteria (filters):**
- `--band`, `--site-name`, `--sector-id`, `--tilt-min`, `--tilt-max`

**Update Parameters (changes):**
- `--update-tilt-deg=<deg>` - New tilt angle
- `--update-tx-rs-power-dbm=<dbm>` - New TX power
- `--update-bs-rows=<n>` / `--update-bs-cols=<n>` - New antenna array

### Simulation Operations

#### Compute
```bash
cns compute                           # Run simulation
cns compute --threshold=-115.0        # Custom RSRP threshold
cns compute --label-mode=sector       # Different label mode
```

**Options:**
- `--threshold=<dbm>` - RSRP threshold (default: -120.0)
- `--label-mode=<name|idx>` - Label mode (default: name)

#### Drop UEs
```bash
cns drop ues 50000                    # Drop 50K UEs (default layout)
cns drop ues 50000 --layout=box --box-pad=300  # Box layout
cns drop ues 20000 --layout=disk --radius=1000 # Disk layout
cns drop ues 30000 --seed=42          # With specific seed
```

**Options:**
- `--layout=<box|disk>` - Layout type
- `--box-pad=<m>` - Box padding (meters)
- `--radius=<m>` - Disk radius (meters)
- `--height=<m>` - UE height (meters)
- `--seed=<n>` - Random seed

### Other Commands

```bash
cns clear                  # Clear terminal output
cns <command> --help       # Show help for any command
```

## 📋 Example Workflows

### Workflow 1: Initialize and Explore
```bash
cns status                 # Check connection
cns init --default         # Initialize with defaults
cns query sites            # View all sites
cns query cells            # View all cells
cns compute                # Run simulation
cns query ues              # Check results
```

### Workflow 2: Tilt Optimization Study
```bash
# Query current high-band cells
cns query cells --band=H

# Update all high-band cells to 10°
cns update cells query --band=H --update-tilt-deg=10.0

# Run compute
cns compute

# Try different tilt
cns update cells query --band=H --update-tilt-deg=12.0
cns compute

# Compare results (manually for now)
```

### Workflow 3: Site-Specific Configuration
```bash
# Query specific site
cns query cells --site-name=CNS0001A

# Update just that site
cns update cells query --site-name=CNS0001A --update-tilt-deg=11.0 --update-tx-rs-power-dbm=3.0

# Update all sites matching pattern
cns update cells query --site-name=CNS000* --band=H --update-tilt-deg=11.5

# Run compute
cns compute
```

### Workflow 4: UE Scaling Study
```bash
# Start with 10K UEs
cns drop ues 10000
cns compute

# Scale to 30K
cns drop ues 30000
cns compute

# Scale to 50K
cns drop ues 50000
cns compute

# Compare results
cns query ues
```

## 🎨 Customization

### Changing API URL

The frontend calls the backend at `/api/command` (proxied by nginx).

To change the backend URL, edit `cli.js`:

```javascript
export class CLI {
  constructor(apiUrl = '/api/command') {
    this.apiUrl = apiUrl;
  }
}
```

### Theming

**Logo Switching:**
Logos automatically switch with theme via CSS in `custom-styles.css`:

```css
[data-theme="light"] .brand-logo {
  content: url('cnsLogo_lightmode.png');
}

[data-theme="dark"] .brand-logo {
  content: url('cnsLogo_darkmode.png');
}
```

**Table Styling:**
Tables use `.cli-table` class, styled in `custom-styles.css`:
- Light mode: Blue headers, white rows
- Dark mode: Blue headers, dark gray rows
- Both: Hover effects, alternating row colors

### Adding Custom Styles

Add to `custom-styles.css`:

```css
/* Your custom styles */
.cli-output {
  font-size: 15px;  /* Adjust output font size */
}

.cli-table th {
  background-color: #your-color;  /* Custom header color */
}
```

## 🔧 Terminal Features

### Command History
- **↑ Arrow** - Previous command
- **↓ Arrow** - Next command
- History persists during session

### Tab Completion
- Type partial command and press **Tab**
- Completes based on command history
- Smart matching:
  - Prefix match (highest priority)
  - Word boundary match
  - Partial match

### Output Rendering
- **Plain text** - Rendered in `<pre>` tags
- **HTML tables** - Rendered as actual HTML with styling
- **Mixed content** - Text and tables can coexist

### Scrolling
- **Regular output** - Scrolls to bottom
- **Tables** - Scrolls to top of table (so headers are visible)

## 📊 Table Format

### Query Cells Output

| Idx | Site ID | Cell ID | Band | Azimuth | Freq(MHz) | Tilt | Antenna Array | Pattern |
|-----|---------|---------|------|---------|-----------|------|---------------|---------|
| 0 | CNS0001A | HCNS0001A1 | H | 318.0° | 2500.0 | 9.0° | 8x1 | 38.901 |

**Columns:**
- **Idx** - Cell index
- **Site ID** - Site name
- **Cell ID** - Cell name (unique identifier)
- **Band** - H (high) or L (low)
- **Azimuth** - Antenna direction
- **Freq(MHz)** - Frequency in MHz
- **Tilt** - Downtilt angle
- **Antenna Array** - rows×cols
- **Pattern** - Antenna pattern model

### Query Sites Output

| Idx | Site ID | Cells | X | Y | Height(m) |
|-----|---------|-------|---|---|-----------|
| 0 | CNS0001A | 6 | -218.6 | 169.6 | 20.0 |

## 🐛 Troubleshooting

### Commands Not Executing

**Check backend:**
```bash
docker compose logs backend
```

**Test backend directly:**
```bash
curl http://localhost:8001/
```

### Table Not Rendering

- Check browser console for errors
- Verify response contains `<table>` HTML
- Check `custom-styles.css` is loaded

### Theme Not Switching

- Check that `data-theme` attribute changes in HTML
- Verify logo files exist
- Check CSS selectors in `custom-styles.css`

### Tab Completion Not Working

- Press Tab after typing partial command
- Ensure you've run commands first (builds history)
- Check browser console for JS errors

## 🚀 Development

### Run Locally (Outside Docker)

```bash
cd interface_frontend
python -m http.server 8080
```

Open `http://localhost:8080`

**Note:** Backend must be running separately (see [Backend README](../interface_backend/README.md))

### Modify CLI Logic

Edit `cli.js`:
- `executeCommand()` - Command execution
- `handleTabCompletion()` - Tab completion logic
- `appendToOutput()` - Output rendering

### Modify UI

Edit `index.html`:
- Layout structure
- Navigation items
- Branding elements

### Add New View/Tab

1. Create new module (e.g., `dashboard.js`)
2. Import in `app.js`
3. Add navigation item in `index.html`

See root [README.md](../README.md#adding-new-tabsviews) for details.

## 📝 Technical Details

### Output Rendering Logic

```javascript
appendToOutput(outputElement, content, className = '') {
  if (content.includes('<table')) {
    // Split text and tables
    const parts = content.split(/(<table.*?<\/table>)/s);
    parts.forEach(part => {
      if (part.includes('<table')) {
        // Render table as HTML
        const wrapper = document.createElement('div');
        wrapper.innerHTML = part;
        outputElement.appendChild(wrapper.firstChild);
      } else if (part.trim()) {
        // Render text in <pre>
        const pre = document.createElement('pre');
        pre.textContent = part.trim();
        outputElement.appendChild(pre);
      }
    });
  } else {
    // Plain text output
    const pre = document.createElement('pre');
    pre.textContent = content;
    outputElement.appendChild(pre);
  }
}
```

### Command Parsing

Frontend sends raw command string to backend:
```javascript
const response = await fetch(this.apiUrl, {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({command: fullCommand})
});
```

Backend parses and routes:
- Removes `cns` prefix (optional)
- Lowercases command verb
- Preserves argument case
- Routes to appropriate handler

## 🔮 Future Enhancements

- [ ] Syntax highlighting for commands
- [ ] Clickable table rows (drill-down)
- [ ] Export tables to CSV
- [ ] Command aliasing
- [ ] Saved command snippets
- [ ] Multi-tab terminal
- [ ] Result visualization (charts/graphs)

---

**For backend development, see:** [Backend README](../interface_backend/README.md)  
**For Docker setup, see:** [Root README](../README.md)

