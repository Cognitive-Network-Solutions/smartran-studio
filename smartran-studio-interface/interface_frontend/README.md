# Frontend - Web CLI Interface

React-based terminal-style interface for SmartRAN Studio.

## Technology Stack

- **React 18** - UI framework
- **Vite** - Build tool & dev server
- **TailwindCSS** - Styling
- **Nginx** - Production web server

## Features

- Terminal-style CLI interface
- Command history (up/down arrows)
- Session persistence (survives page refresh)
- Interactive initialization wizard
- Response rendering (tables, JSON, text)
- Auto-scrolling and pagination

## Structure

```
interface_frontend/
├── src/
│   ├── App.jsx              # Main app component
│   ├── main.jsx             # React entry point
│   ├── views/
│   │   ├── CLI.jsx          # CLI terminal component
│   │   └── NetworkMap.jsx   # Future: network visualization
│   ├── components/
│   │   ├── Layout.jsx       # App layout
│   │   ├── Navigation.jsx   # Top navigation
│   │   └── widgets/
│   │       └── InitWizard.jsx  # Initialization wizard
│   ├── utils/
│   │   ├── api.js           # Backend API client
│   │   └── renderers.jsx    # Response renderers
│   └── styles/
│       └── index.css        # Global styles
├── index.html               # HTML entry point
├── vite.config.js           # Vite configuration
├── tailwind.config.js       # TailwindCSS config
├── Dockerfile.frontend      # Production Dockerfile
└── nginx.conf               # Nginx configuration
```

## Development

### Docker (Recommended)

Frontend is served via Nginx in Docker:

```bash
# From repository root
docker compose up -d frontend
```

Access at: http://localhost:8080

For code changes, rebuild:
```bash
docker compose up --build -d frontend
```

### Local Dev Server (Optional)

Useful for faster frontend-only development:

```bash
npm install
npm run dev
```

Access at: http://localhost:5173

**Note**: Backend must be running (Docker or local) at http://localhost:8001

### Build for Production

```bash
npm run build
```

Output in `dist/` directory

## Environment

The frontend connects to the backend at:
- **Development**: http://localhost:8001 (hardcoded in `api.js`)
- **Production**: Same-origin requests to `/api/`

## Key Components

### `CLI.jsx`

Main terminal interface:
- Command input with history
- Output rendering
- Session persistence
- Widget launching

### `InitWizard.jsx`

Interactive initialization wizard:
- Step-by-step configuration
- Form validation
- Preview and submit

### `renderers.jsx`

Response formatters:
- Table rendering (with auto-scrolling)
- JSON pretty-printing
- Plain text formatting
- Error highlighting

## Session Persistence

Uses `sessionStorage` to persist:
- Command history (`smartran-cli-history`)
- Output history (`smartran-cli-outputs`)

Survives page refresh but not browser close.

## Styling

TailwindCSS with custom configuration:
- Terminal theme (dark mode)
- Monospace fonts
- Table styling
- Responsive design

## Future Enhancements

- Network topology map view
- Real-time simulation monitoring
- Cell coverage visualization
- Performance metrics dashboard

## License

See main repository LICENSE file.
