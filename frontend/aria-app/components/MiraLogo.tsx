// components/MiraLogo.tsx
// MIRA Retail — Sprout Pulse mark
// Fresh sprout (grocery) + amber heartbeat line (AI agents at work)
// Use consistently across aria-app (Next.js) and pulse-dashboard (Streamlit)

interface MiraLogoProps {
  size?: 'sm' | 'md' | 'lg'
  variant?: 'color' | 'light' | 'dark'
  showTagline?: boolean
}

const sizes = {
  sm: { mark: 22, wordmark: 14, gap: 6 },
  md: { mark: 32, wordmark: 18, gap: 8 },
  lg: { mark: 44, wordmark: 24, gap: 10 },
}

export function MiraLogo({
  size = 'md',
  variant = 'color',
  showTagline = false,
}: MiraLogoProps) {
  const s = sizes[size]

  const stemColor   = variant === 'light' ? '#ffffff' : '#0a5c44'
  const leafColor   = variant === 'light' ? '#ffffff' : '#0a5c44'
  const pulseColor  = '#c8891a'   // amber — always, in all variants
  const wordPrimary = variant === 'light' ? '#ffffff'
    : variant === 'dark'  ? '#0f172a'
    : '#0a5c44'
  const taglineColor = variant === 'light'
    ? 'rgba(255,255,255,0.5)' : '#94a3b8'

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: s.gap }}>
      {/* Sprout Pulse mark */}
      <svg
        width={s.mark}
        height={s.mark}
        viewBox="0 0 38 38"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
      >
        {/* Stem */}
        <line
          x1="19" y1="34" x2="19" y2="17"
          stroke={stemColor}
          strokeWidth="2.5"
          strokeLinecap="round"
        />
        {/* Left leaf — full opacity */}
        <path
          d="M19 21 C19 21 10 19 8 12 C12 9 19 14 19 21Z"
          fill={leafColor}
        />
        {/* Right leaf — reduced opacity for depth */}
        <path
          d="M19 21 C19 21 28 19 30 12 C26 9 19 14 19 21Z"
          fill={leafColor}
          opacity="0.55"
        />
        {/* Amber pulse / heartbeat line — agents at work */}
        <path
          d="M5 27 L8 27 L10 23 L12 31 L14.5 25 L17 27 L19 27 L21 27 L23.5 23 L26 31 L28 25 L30 27 L33 27"
          stroke={pulseColor}
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
          fill="none"
        />
      </svg>

      {/* Wordmark */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
        <span style={{
          fontSize: s.wordmark,
          fontWeight: 600,
          color: wordPrimary,
          letterSpacing: '-0.025em',
          lineHeight: 1,
          fontFamily: 'Inter, system-ui, sans-serif',
        }}>
          MIRA
          <span style={{ color: '#c8891a' }}>Retail</span>
        </span>
        {showTagline && (
          <span style={{
            fontSize: 9,
            color: taglineColor,
            letterSpacing: '0.10em',
            lineHeight: 1,
            fontFamily: 'Inter, system-ui, sans-serif',
            marginTop: 2,
          }}>
            AI-NATIVE GROCERY
          </span>
        )}
      </div>
    </div>
  )
}

// Favicon SVG string — use in app/favicon.svg
export const MIRA_FAVICON_SVG = `
<svg width="32" height="32" viewBox="0 0 38 38" fill="none" xmlns="http://www.w3.org/2000/svg">
  <line x1="19" y1="34" x2="19" y2="17" stroke="#0a5c44" stroke-width="3.5" stroke-linecap="round"/>
  <path d="M19 21 C19 21 10 19 8 12 C12 9 19 14 19 21Z" fill="#0a5c44"/>
  <path d="M19 21 C19 21 28 19 30 12 C26 9 19 14 19 21Z" fill="#0a5c44" opacity="0.55"/>
  <path d="M7 27 L10 23 L13 31 L16 25 L19 27 L22 25 L25 31 L28 23 L31 27"
    stroke="#c8891a" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
</svg>`
