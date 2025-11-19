/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class', // Enable class-based dark mode
  theme: {
    extend: {
      colors: {
        // Light theme colors
        'light': {
          'viewport-bg': '#f9fafb',
          'bg': '#f9fafb',
          'surface': '#ffffff',
          'bg-secondary': '#f3f4f6',
          'topbar-bg': '#ffffff',
          'topbar-ink': '#111827',
          'sidebar': '#ffffff',
          'sidebar-ink': '#6b7280',
          'ink': '#111827',
          'text': '#374151',
          'muted': '#9ca3af',
          'line': '#e5e7eb',
          'border-light': '#f3f4f6',
        },
        // Dark theme colors
        'dark': {
          'viewport-bg': '#0f172a',
          'bg': '#0f172a',
          'surface': '#1e293b',
          'bg-secondary': '#334155',
          'topbar-bg': '#1e293b',
          'topbar-ink': '#f1f5f9',
          'sidebar': '#1e293b',
          'sidebar-ink': '#94a3b8',
          'ink': '#f1f5f9',
          'text': '#cbd5e1',
          'muted': '#64748b',
          'line': '#334155',
          'border-light': '#1e293b',
        },
        // Semantic colors (same for both themes)
        'accent': '#2563eb',
        'accent-hover': '#1d4ed8',
        'success': '#16a34a',
        'warning': '#f59e0b',
        'error': '#dc2626',
        'info': '#06b6d4',
      },
      fontFamily: {
        'sans': ['Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        'sm': '0 1px 2px 0 rgb(0 0 0 / 0.05)',
        'md': '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
        'lg': '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
      },
    },
  },
  plugins: [],
}

