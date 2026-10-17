import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './pages/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // ── MIRA Retail brand palette ──────────────────────────────
        // Primary: deep teal-green — distinctive, not generic supermarket green
        mira: {
          50:  '#edf7f3',
          100: '#d0ece2',
          200: '#a3d9c6',
          300: '#6dbfa4',
          400: '#3a9e81',
          500: '#1e7d63',
          600: '#0a5c44',   // PRIMARY — nav, buttons, active states
          700: '#094d3a',
          800: '#073d2e',
          900: '#052e22',
          950: '#021a13',
        },
        // Accent: warm amber — promotions, discounts, perishable alerts
        amber: {
          50:  '#fef9ec',
          100: '#fdf0c8',
          200: '#fae08d',
          300: '#f6c94a',
          400: '#f2b020',
          500: '#c8891a',   // ACCENT — promotions, CTAs, highlights
          600: '#a36812',
          700: '#7d4d0e',
          800: '#5c380b',
          900: '#3a2408',
        },
        // Neutrals: cool slate — backgrounds, borders, text
        slate: {
          50:  '#f8fafc',   // page background
          100: '#f1f5f9',   // sidebar background
          200: '#e2e8f0',   // borders
          300: '#cbd5e1',   // disabled borders
          400: '#94a3b8',   // placeholder text
          500: '#64748b',   // secondary text
          600: '#475569',   // body text
          700: '#334155',   // strong text
          800: '#1e293b',   // headings
          900: '#0f172a',   // nav background, darkest text
          950: '#020617',
        },
        // Status colors
        success: '#16a34a',
        warning: '#d97706',
        danger:  '#dc2626',
        info:    '#0284c7',
      },

      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },

      fontSize: {
        // Tight type scale — disciplined hierarchy
        'xs':   ['11px', { lineHeight: '16px', letterSpacing: '0.02em' }],
        'sm':   ['13px', { lineHeight: '20px' }],
        'base': ['15px', { lineHeight: '24px' }],
        'lg':   ['17px', { lineHeight: '28px' }],
        'xl':   ['20px', { lineHeight: '30px', fontWeight: '500' }],
        '2xl':  ['24px', { lineHeight: '32px', fontWeight: '500' }],
        '3xl':  ['30px', { lineHeight: '38px', fontWeight: '600' }],
      },

      borderRadius: {
        'sm':  '4px',
        DEFAULT: '6px',
        'md':  '8px',
        'lg':  '12px',
        'xl':  '16px',
        'full': '9999px',
      },

      spacing: {
        // Named spacing — use these instead of arbitrary values
        'xs':  '4px',
        'sm':  '8px',
        'md':  '16px',
        'lg':  '24px',
        'xl':  '32px',
        '2xl': '48px',
        '3xl': '64px',
      },

      boxShadow: {
        // Subtle, functional shadows only — no decorative elevation
        'card':   '0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04)',
        'panel':  '0 4px 12px rgba(0,0,0,0.08)',
        'focus':  '0 0 0 3px rgba(10,92,68,0.25)',   // mira-600 focus ring
        'none':   'none',
      },

      // Layout breakpoints
      screens: {
        'sm':  '640px',
        'md':  '768px',
        'lg':  '1024px',
        'xl':  '1280px',
        '2xl': '1440px',
      },
    },
  },
  plugins: [],
}

export default config
