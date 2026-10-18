# MIRA Retail — Brand & Design System

> **Implementation status (October 18, 2026):** This file is a visual design
> reference. [SCREENS.md](SCREENS.md) describes the implemented local workflow;
> [ARC_SPEC.md](../../ARC_SPEC.md) defines product behavior. Planned layouts and
> model-related labels here do not establish working Google integration.
> Reference document for AI-assisted frontend generation (Kiro / Cursor / Copilot)
> Version 1.0 · ARC Project · Pragmatic Engineers

---

## 1. Brand identity

**Company:** MIRA Retail — a modern, AI-native UAE grocery chain  
**Tagline:** AI-native grocery  
**Logo name:** Sprout Pulse  
**Logo concept:** A fresh sprout (fresh grocery, organic, natural) with an amber heartbeat/pulse line running through it (AI agents working intelligently in the background). The sprout is green. The pulse is always amber. The two together = smart fresh retail.

### Logo SVG — the canonical mark

```svg
<!-- Full logo mark — use at 32px and above -->
<svg width="38" height="38" viewBox="0 0 38 38" fill="none" xmlns="http://www.w3.org/2000/svg">
  <!-- Stem -->
  <line x1="19" y1="34" x2="19" y2="17" stroke="#0a5c44" stroke-width="2.5" stroke-linecap="round"/>
  <!-- Left leaf — full opacity -->
  <path d="M19 21 C19 21 10 19 8 12 C12 9 19 14 19 21Z" fill="#0a5c44"/>
  <!-- Right leaf — 55% opacity for depth -->
  <path d="M19 21 C19 21 28 19 30 12 C26 9 19 14 19 21Z" fill="#0a5c44" opacity="0.55"/>
  <!-- Amber pulse line — always #c8891a regardless of variant -->
  <path d="M5 27 L8 27 L10 23 L12 31 L14.5 25 L17 27 L19 27 L21 27 L23.5 23 L26 31 L28 25 L30 27 L33 27"
    stroke="#c8891a" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
</svg>

<!-- Favicon mark — simplified for 16-32px -->
<svg width="32" height="32" viewBox="0 0 38 38" fill="none" xmlns="http://www.w3.org/2000/svg">
  <line x1="19" y1="34" x2="19" y2="17" stroke="#0a5c44" stroke-width="3.5" stroke-linecap="round"/>
  <path d="M19 21 C19 21 10 19 8 12 C12 9 19 14 19 21Z" fill="#0a5c44"/>
  <path d="M19 21 C19 21 28 19 30 12 C26 9 19 14 19 21Z" fill="#0a5c44" opacity="0.55"/>
  <path d="M7 27 L10 23 L13 31 L16 25 L19 27 L22 25 L25 31 L28 23 L31 27"
    stroke="#c8891a" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
</svg>
```

### Wordmark

```
MIRA — color: #0a5c44, weight: 600, tracking: -0.025em
Retail — color: #c8891a, weight: 600, tracking: -0.025em
Tagline — "AI-NATIVE GROCERY", color: #94a3b8, size: 9px, tracking: 0.10em
```

### Logo variants

| Variant | Background | Stem/leaf color | Pulse | Wordmark |
|---------|-----------|-----------------|-------|----------|
| Color (default) | Light (#f8fafc, #fff) | #0a5c44 | #c8891a | MIRA=#0a5c44, Retail=#c8891a |
| Light (reversed) | Dark (#0f172a, #0a5c44) | #ffffff | #c8891a | MIRA=#ffffff, Retail=#c8891a |
| Dark | White background | #0f172a | #c8891a | MIRA=#0f172a, Retail=#c8891a |

### Logo rules

- Minimum size: 20px mark height
- Clear space: equal to the mark height on all sides
- Never stretch, rotate, recolor the mark
- The pulse line is ALWAYS amber (#c8891a) — never changes across variants
- Never place the color variant on a dark background
- Never place the light variant on a light background

---

## 2. Color palette

### Primary — deep teal green

| Token | Hex | Usage |
|-------|-----|-------|
| `mira-50` | `#edf7f3` | Tinted backgrounds, selected states, ARIA message bubbles |
| `mira-100` | `#d0ece2` | Hover states on light surfaces, borders |
| `mira-200` | `#a3d9c6` | Borders, dividers, badge outlines |
| `mira-300` | `#6dbfa4` | Disabled primary elements |
| `mira-400` | `#3a9e81` | Secondary icons |
| `mira-500` | `#1e7d63` | Hover state for primary buttons |
| `mira-600` | `#0a5c44` | **PRIMARY** — buttons, active nav, links, checkboxes |
| `mira-700` | `#094d3a` | Active/pressed state for primary buttons |
| `mira-800` | `#073d2e` | Dark text on light primary tints |
| `mira-900` | `#052e22` | Darkest — headings on tinted backgrounds |

### Pulse (accent) — warm amber

Named "pulse" to match the logo mark and the PULSE agent.

| Token | Hex | Usage |
|-------|-----|-------|
| `pulse-50` | `#fef9ec` | Perishable alert backgrounds |
| `pulse-100` | `#fdf0c8` | Discount badge backgrounds |
| `pulse-200` | `#fae08d` | Highlight borders |
| `pulse-300` | `#f6c94a` | Warning icons |
| `pulse-400` | `#f2b020` | Promotion tags |
| `pulse-500` | `#c8891a` | **ACCENT** — promotions, discounts, perishable alerts, logo pulse line |
| `pulse-600` | `#a36812` | Hover state on amber buttons |
| `pulse-700` | `#7d4d0e` | Dark text on amber backgrounds |

### Neutral — cool slate

| Token | Hex | Usage |
|-------|-----|-------|
| `slate-50` | `#f8fafc` | **ARIA app page background** |
| `slate-100` | `#f1f5f9` | **PULSE dashboard page background**, category sidebar |
| `slate-200` | `#e2e8f0` | Default borders, dividers |
| `slate-300` | `#cbd5e1` | Disabled borders |
| `slate-400` | `#94a3b8` | Placeholder text, muted icons |
| `slate-500` | `#64748b` | Secondary text, captions |
| `slate-600` | `#475569` | Body text |
| `slate-700` | `#334155` | Strong body text |
| `slate-800` | `#1e293b` | Headings, primary text |
| `slate-900` | `#0f172a` | **Nav background**, darkest text |

### Status colors

| Role | Hex | Usage |
|------|-----|-------|
| Success | `#16a34a` | Order confirmed, discount approved, in stock |
| Warning | `#d97706` | Low stock threshold approaching |
| Danger | `#dc2626` | Out of stock, order failed |
| Info | `#0284c7` | Informational notices |

### Alert color sets

**Perishable alert** (PULSE dashboard + ARIA discount surfacing):
- Background: `#fef9ec`
- Border: `#fde68a`
- Text: `#92400e`

**Stockout alert** (PULSE dashboard):
- Background: `#fef2f2`
- Border: `#fecaca`
- Text: `#991b1b`

**Approved / success state**:
- Background: `#edf7f3`
- Border: `#a3d9c6`
- Text: `#073d2e`

---

## 3. Backgrounds

This is the most important section for layout generation.

### Rule: never use brand green as a page background

Green (`#0a5c44`) appears only on interactive elements. Page backgrounds are always neutral.

### ARIA customer app (Next.js)

| Element | Color | Hex |
|---------|-------|-----|
| Page / outer background | `slate-50` | `#f8fafc` |
| Nav bar | `slate-900` | `#0f172a` |
| Category sidebar | `slate-100` | `#f1f5f9` |
| Product grid area | `slate-50` | `#f8fafc` |
| Product cards | White | `#ffffff` |
| ARIA panel background | White | `#ffffff` |
| ARIA panel header | `mira-600` | `#0a5c44` |
| ARIA message (agent) | `mira-50` | `#edf7f3` |
| ARIA message (user) | `mira-600` | `#0a5c44` |
| Cart preview background | `mira-50` | `#edf7f3` |
| Input fields | White | `#ffffff` |
| Modal / drawer | White | `#ffffff` |

### PULSE manager dashboard (Streamlit)

| Element | Color | Hex |
|---------|-------|-----|
| Page / outer background | `slate-100` | `#f1f5f9` |
| Streamlit sidebar | `slate-100` | `#f1f5f9` |
| Alert cards | White | `#ffffff` |
| Metric cards | White | `#ffffff` |
| Perishable alert | `pulse-50` | `#fef9ec` |
| Stockout alert | Red-50 | `#fef2f2` |
| Approved state | `mira-50` | `#edf7f3` |
| Evidence expander | `slate-50` | `#f8fafc` |
| Reasoning chain steps | Varies by type (see Section 7) | — |

---

## 4. Typography

**Font family:** Inter (Google Fonts)  
**Load:** `https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap`  
**Fallback:** `system-ui, -apple-system, sans-serif`  
**One family only** — weight and size do the hierarchy work.

### Type scale

| Name | Size | Weight | Line height | Usage |
|------|------|--------|-------------|-------|
| `xs` | 11px | 400 | 16px | Metadata, badges, timestamps |
| `sm` | 13px | 400 | 20px | Secondary text, captions, table data |
| `base` | 15px | 400 | 24px | Body text, product descriptions |
| `lg` | 17px | 500 | 28px | Card titles, section headings |
| `xl` | 20px | 500 | 30px | Page section headers |
| `2xl` | 24px | 600 | 32px | Page titles |
| `3xl` | 30px | 600 | 38px | Hero numbers (revenue lost, AED impact) |

### Text colors

| Role | Color | Hex |
|------|-------|-----|
| Primary (headings, important) | `slate-800` | `#1e293b` |
| Body | `slate-600` | `#475569` |
| Secondary / supporting | `slate-500` | `#64748b` |
| Muted / placeholder | `slate-400` | `#94a3b8` |
| On dark (nav, primary buttons) | White | `#ffffff` |
| Link / accent | `mira-600` | `#0a5c44` |
| Amber / pulse | `pulse-500` | `#c8891a` |

### Rules

- Sentence case everywhere — never ALL CAPS in body content
- Taglines and badge labels only use uppercase with `letter-spacing: 0.08em`
- Never use font-weight 700 — 600 is the maximum
- Line length max 72 characters for body text

---

## 5. Spacing & layout

### Spacing scale

| Token | Value | Usage |
|-------|-------|-------|
| `xs` | 4px | Icon gaps, tight internal padding |
| `sm` | 8px | Component internal gaps |
| `md` | 16px | Card padding, section gaps |
| `lg` | 24px | Between cards, section spacing |
| `xl` | 32px | Page section separation |
| `2xl` | 48px | Major section breaks |

### Border radius

| Token | Value | Usage |
|-------|-------|-------|
| `sm` | 4px | Badges, pills, small chips |
| Default | 6px | Buttons, inputs, small cards |
| `md` | 8px | Standard cards, modals |
| `lg` | 12px | Large panels, drawers |
| `full` | 9999px | Pills, avatars, round buttons |

### Borders

- Default hairline: `0.5px solid #e2e8f0`
- Strong: `0.5px solid #cbd5e1`
- Focus ring: `0 0 0 3px rgba(10,92,68,0.25)` (mira-600 at 25% opacity)
- No decorative shadows — functional only

### ARIA app layout (Next.js — 3 columns)

```
┌─────────────────────────────────────────────────────────┐
│  NAV — #0f172a — 56px height                            │
├───────────┬──────────────────────────┬──────────────────┤
│ SIDEBAR   │ PRODUCT GRID             │ ARIA PANEL       │
│ 200px     │ fluid                    │ 340px            │
│ #f1f5f9   │ #f8fafc                  │ #ffffff          │
│           │                          │                  │
│ Categories│ Product cards — #ffffff  │ Chat thread      │
│ Filters   │ 3-col grid               │ Cart preview     │
│ Store sel │ In-stock / out-of-stock  │ Send input       │
└───────────┴──────────────────────────┴──────────────────┘
```

### PULSE dashboard layout (Streamlit — 2 sections)

```
┌──────────────┬──────────────────────────────────────────┐
│ SIDEBAR      │ MAIN AREA                                │
│ 240px        │ fluid                                    │
│ #f1f5f9      │ #f1f5f9                                  │
│              │                                          │
│ Store select │ ┌─────────────────────────────────────┐  │
│ Date filter  │ │ METRIC CARDS (3 cols) — #ffffff     │  │
│ Refresh btn  │ └─────────────────────────────────────┘  │
│ Last updated │ ┌─────────────────────────────────────┐  │
│              │ │ ALERT CARDS — #ffffff               │  │
│              │ │ Ranked by AED impact                │  │
│              │ └─────────────────────────────────────┘  │
│              │ ┌─────────────────────────────────────┐  │
│              │ │ LOOKER STUDIO EMBED — iframe        │  │
│              │ └─────────────────────────────────────┘  │
└──────────────┴──────────────────────────────────────────┘
```

---

## 6. Components

### Buttons

```css
/* Primary — main CTA */
background: #0a5c44;
color: #ffffff;
padding: 8px 16px;
border-radius: 6px;
font-size: 13px;
font-weight: 500;
border: none;
hover: background #094d3a;
focus: box-shadow 0 0 0 3px rgba(10,92,68,0.25);

/* Secondary — supporting action */
background: #ffffff;
color: #0a5c44;
border: 0.5px solid #a3d9c6;
hover: background #edf7f3;

/* Accent / promotion — discounts, offers */
background: #c8891a;
color: #ffffff;
hover: background #a36812;

/* Danger — cancel, reject */
background: #ffffff;
color: #dc2626;
border: 0.5px solid #fecaca;
hover: background #fef2f2;

/* Ghost — low emphasis */
background: transparent;
color: #64748b;
border: 0.5px solid #e2e8f0;
hover: background #f1f5f9;
```

### Cards

```css
/* Standard product / content card */
background: #ffffff;
border: 0.5px solid #e2e8f0;
border-radius: 8px;
padding: 16px;

/* Hover state */
border-color: #a3d9c6;

/* Alert card — perishable */
background: #fef9ec;
border: 0.5px solid #fde68a;
border-radius: 8px;
padding: 16px;

/* Alert card — stockout */
background: #fef2f2;
border: 0.5px solid #fecaca;
border-radius: 8px;
padding: 16px;

/* Alert card — approved/success */
background: #edf7f3;
border: 0.5px solid #a3d9c6;
border-radius: 8px;
padding: 16px;
```

### Badges / pills

```css
/* Halal badge */
background: #edf7f3; color: #073d2e;
border: 0.5px solid #a3d9c6;
padding: 2px 8px; border-radius: 9999px;
font-size: 11px; font-weight: 500;

/* Discount badge */
background: #fef9ec; color: #92400e;
border: 0.5px solid #fde68a;

/* Out of stock badge */
background: #fef2f2; color: #991b1b;
border: 0.5px solid #fecaca;

/* In stock badge */
background: #f0fdf4; color: #15803d;
border: 0.5px solid #bbf7d0;

/* ARIA badge (agent indicator) */
background: #0a5c44; color: #ffffff;
padding: 2px 8px; border-radius: 9999px;
font-size: 11px; font-weight: 500;

/* PULSE badge */
background: #c8891a; color: #ffffff;
```

### Form inputs

```css
background: #ffffff;
border: 0.5px solid #e2e8f0;
border-radius: 6px;
padding: 8px 12px;
font-size: 13px;
color: #1e293b;
placeholder-color: #94a3b8;
focus: border-color transparent; box-shadow: 0 0 0 3px rgba(10,92,68,0.25);
```

---

## 7. ARIA chat interface

### Message bubbles

```css
/* Agent (ARIA) message */
background: #edf7f3;
border: 0.5px solid #d0ece2;
border-radius: 0 8px 8px 8px;   /* flat top-left = comes from left */
padding: 12px 16px;
font-size: 13px;
color: #073d2e;
max-width: 85%;

/* User message */
background: #0a5c44;
border-radius: 8px 0 8px 8px;   /* flat top-right = comes from right */
padding: 12px 16px;
font-size: 13px;
color: #ffffff;
max-width: 85%;
align-self: flex-end;

/* Thinking / loading state */
background: #fef9ec;
border: 0.5px solid #fde68a;
border-radius: 8px;
padding: 8px 12px;
font-size: 12px;
color: #92400e;
```

### Reasoning chain (ReAct steps)

```css
/* THOUGHT step */
border-left: 3px solid #0a5c44;
background: #edf7f3;
padding: 6px 12px;
border-radius: 0 4px 4px 0;
font-size: 11px;
color: #073d2e;

/* ACTION step */
border-left: 3px solid #c8891a;
background: #fef9ec;
padding: 6px 12px;
border-radius: 0 4px 4px 0;
font-size: 11px;
color: #92400e;

/* OBSERVATION step */
border-left: 3px solid #cbd5e1;
background: #f8fafc;
padding: 6px 12px;
border-radius: 0 4px 4px 0;
font-size: 11px;
color: #64748b;
```

---

## 8. PULSE dashboard components

### Metric cards (3 per row)

```
┌──────────────────┐
│ Incidents today  │  ← label: slate-500, 12px
│ 23               │  ← value: slate-800, 30px, weight 600
│ ↑ 8 vs yesterday │  ← delta: danger red if up, success green if down
└──────────────────┘
background: #ffffff
border: 0.5px solid #e2e8f0
border-radius: 8px
padding: 16px
```

### Alert card structure

```
┌─────────────────────────────────────────────────────┐
│ HEADER — border-bottom: 0.5px solid #f1f5f9         │
│ ⚠ Product name · Store · X incidents               │
│ AED [impact] at risk                                │
├─────────────────────────────────────────────────────┤
│ BODY                                                │
│ Root cause — [High/Medium/Low confidence]           │
│ ▼ Evidence (expandable)                             │
│   Data source · row count · date range             │
├─────────────────────────────────────────────────────┤
│ FOOTER                                              │
│ [✅ Approve PO]          [❌ Reject]                │
└─────────────────────────────────────────────────────┘

Stockout card: border-left: 4px solid #dc2626
Perishable card: border-left: 4px solid #c8891a
Approved card: border-left: 4px solid #16a34a
```

### PO approval buttons

```css
/* Approve */
background: #0a5c44; color: #ffffff;
padding: 8px 20px; border-radius: 6px;
font-weight: 500; font-size: 13px;

/* Reject */
background: #ffffff; color: #dc2626;
border: 0.5px solid #fecaca;
padding: 8px 20px; border-radius: 6px;
```

---

## 9. Tailwind class reference

Generated from `tailwind.config.ts`. Use these classes directly in JSX:

```
Colors:
  mira-50 mira-100 mira-200 mira-600 mira-700 mira-800 mira-900
  (as bg-, text-, border- prefixes)

Backgrounds:
  bg-slate-50    → ARIA page background
  bg-slate-100   → PULSE page, sidebar
  bg-white       → cards, panels
  bg-slate-900   → nav bar
  bg-mira-600    → primary buttons, ARIA panel header
  bg-mira-50     → ARIA messages, cart preview
  bg-pulse-50    → perishable alerts

Text:
  text-slate-800 → headings
  text-slate-600 → body
  text-slate-500 → secondary
  text-slate-400 → muted / placeholder
  text-mira-600  → links, active states
  text-pulse-500 → amber / promotions

Borders:
  border-slate-200 → default
  border-mira-200  → primary tinted
  border-pulse-200 → amber tinted

Shadows:
  shadow-card  → product cards
  shadow-panel → drawers, modals
  shadow-focus → focus rings (mira-600 at 25%)
```

---

## 10. Streamlit theming (PULSE dashboard)

Place at `frontend/pulse-dashboard/.streamlit/config.toml`:

```toml
[theme]
primaryColor             = "#0a5c44"
backgroundColor          = "#f1f5f9"
secondaryBackgroundColor = "#ffffff"
textColor                = "#1e293b"
font                     = "sans serif"
```

For custom components beyond Streamlit defaults, use `st.markdown()` with inline CSS referencing the hex values above.

---

## 11. Kiro / AI agent implementation instructions

When generating frontend code using this brand document:

1. **Import Inter from Google Fonts** — add to `app/layout.tsx` head
2. **Use `tailwind.config.ts`** tokens — never hardcode hex values in JSX; use Tailwind classes
3. **Use `globals.css` component classes** — `btn-primary`, `btn-secondary`, `btn-accent`, `card`, `bubble-aria`, `bubble-user`, `alert-perishable`, `alert-stockout`, `reasoning-step`
4. **Use `MiraLogo` component** — never recreate the SVG inline in pages; import from `components/MiraLogo.tsx`
5. **Use `brand.ts` constants** — for any dynamic styling that can't use Tailwind classes
6. **Nav is always `#0f172a`** — use `logo variant="light"` on nav
7. **Page backgrounds** — ARIA app: `bg-slate-50`, PULSE dashboard: `bg-slate-100`
8. **Cards are always white** — `bg-white` with `border border-slate-200`
9. **Primary buttons use `btn-primary`** — never inline the green color
10. **Amber is for promotions, discounts, perishable alerts only** — not for general UI accents
11. **The pulse line in the logo is always amber** — never change it programmatically
12. **Auto-refresh** — PULSE dashboard uses a timed `st.fragment` (10 seconds by default); inventory and decision state comes from shared local storage

---

*MIRA Retail Brand System v1.0 · ARC Project · Pragmatic Engineers · AI Builder Cup 2026*
