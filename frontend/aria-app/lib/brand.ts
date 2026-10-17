// brand.ts — MIRA Retail design tokens
// Logo: Sprout Pulse mark — fresh sprout (grocery) + amber heartbeat (AI agents)
// Import wherever brand values are needed in logic or dynamic styles

export const MIRA_COLORS = {
  primary: {
    50:  '#edf7f3',
    100: '#d0ece2',
    200: '#a3d9c6',
    300: '#6dbfa4',
    400: '#3a9e81',
    500: '#1e7d63',
    600: '#0a5c44',   // ← main primary
    700: '#094d3a',
    800: '#073d2e',
    900: '#052e22',
  },
  // Named "pulse" — the amber heartbeat line in the logo
  pulse: {
    50:  '#fef9ec',
    100: '#fdf0c8',
    200: '#fae08d',
    300: '#f6c94a',
    400: '#f2b020',
    500: '#c8891a',   // ← main accent / pulse line
    600: '#a36812',
    700: '#7d4d0e',
  },
  // UI surfaces
  nav:          '#0f172a',
  page:         '#f8fafc',
  sidebar:      '#f1f5f9',
  card:         '#ffffff',
  border:       '#e2e8f0',
  borderStrong: '#cbd5e1',
  // Text
  textPrimary:   '#1e293b',
  textSecondary: '#64748b',
  textMuted:     '#94a3b8',
  textOnDark:    '#ffffff',
  // Status
  success: '#16a34a',
  warning: '#d97706',
  danger:  '#dc2626',
  info:    '#0284c7',
  // Alert backgrounds
  perishableBg:     '#fef9ec',
  perishableBorder: '#fde68a',
  perishableText:   '#92400e',
  stockoutBg:       '#fef2f2',
  stockoutBorder:   '#fecaca',
  stockoutText:     '#991b1b',
} as const

export const MIRA_FONTS = {
  sans: "'Inter', system-ui, sans-serif",
  mono: "'JetBrains Mono', monospace",
} as const

export const MIRA_BRAND = {
  name:         'MIRA Retail',
  tagline:      'AI-native grocery',
  logo:         'Sprout Pulse — fresh sprout + amber heartbeat line',
  primaryColor: '#0a5c44',
  pulseColor:   '#c8891a',   // amber = the pulse/agents at work
} as const

// Streamlit theme — use in pulse-dashboard/.streamlit/config.toml
export const STREAMLIT_THEME = {
  primaryColor:             '#0a5c44',
  backgroundColor:          '#f8fafc',
  secondaryBackgroundColor: '#f1f5f9',
  textColor:                '#1e293b',
  font:                     'sans serif',
} as const
