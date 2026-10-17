# SCREENS.md — Screen Inventory & Design Decisions
> MIRA Retail · ARC Project · Reference for Kiro frontend generation

---

## ARIA App (Next.js) — 4 screens

### Screen 1: Login / Welcome
**Route:** `/login`  
**Purpose:** Customer authentication  
**Layout:** Centered card on `#f8fafc` background  
**Key elements:**
- MIRA Retail logo (color variant, large, centered)
- "ARIA grocery assistant active" badge in mira-50/mira-200
- Email + password form inputs
- Remember me checkbox + forgot password link
- Primary login button (full width, mira-600)
- Register link below
- Privacy note at bottom

**Design decisions:**
- Card width: 320px, border-radius: 14px
- No hero image — logo + badge carry the brand
- Light background (not dark) — customer-facing, welcoming

---

### Screen 2: Main Store — Browse mode
**Route:** `/` or `/shop`  
**Purpose:** Category browsing, product discovery, ARIA minimised  
**Layout:** Full-width nav + 3-column body (sidebar | grid | ARIA tab)

**Nav (48px, #0f172a):**
- Left: logo (light variant) + nav links (Grocery, Offers, Orders)
- Right: search box + store selector + cart button + avatar

**Category sidebar (200px, #f1f5f9):**
- 8 grocery categories with emoji + label
- Active state: mira-50 background, mira-600 text
- Halal toggle filter
- Budget range slider
- Store selector dropdown

**Product grid (fluid, #f8fafc):**
- 3-column responsive grid
- Product cards: white, 0.5px border, 8px radius
- Product image area: mira-50 tint background, emoji placeholder
- Product name (10px, slate-800), price (11px, mira-600)
- "Add to cart" button (full width, mira-600)
- Out of stock state: red-50 background, disabled button
- Discount badge: pulse-50 background, amber text

**ARIA minimised tab (44px strip, mira-600):**
- Sprout mark icon
- "ARIA" label rotated vertical
- Click to expand ARIA panel

---

### Screen 3: ARIA in Action — Chat open
**Route:** `/` (ARIA panel expanded)  
**Purpose:** Active ARIA session — cart building, reasoning visible  
**Layout:** Same as Screen 2 but ARIA panel replaces the minimised tab

**ARIA panel (280px, white):**

Header (mira-600):
- "ARIA — grocery assistant" title
- "Session active · Dubai Marina" subtitle

Chat thread:
- Agent bubbles: mira-50 bg, mira-100 border, 0 8px 8px 8px radius
- User bubbles: mira-600 bg, white text, 8px 0 8px 8px radius
- Thinking state: pulse-50 bg, amber border, spinner
- Reasoning chain: expandable, 3 step types:
  - THOUGHT: mira left border, mira-50 bg
  - ACTION: pulse left border, pulse-50 bg
  - OBSERVATION: slate border, slate-50 bg

Cart preview (mira-50):
- Item list with prices
- Running total
- Confirm order button

Input row:
- Text input (slate-100 bg)
- Send button (mira-600)

**Product grid changes:**
- Added items show mira-50 background + "✓ Added by ARIA" button state
- Substituted items labelled "(subst.)"
- Checking stock items show dashed border + spinner

---

### Screen 4: Order Confirmed
**Route:** `/order/confirmed`  
**Purpose:** Post-purchase confirmation  
**Layout:** Centered card on page background

**Card (380px):**
- Green checkmark circle icon (success-50 bg)
- Order number and store
- Order summary box (mira-50 bg):
  - Item count + subtotal
  - Discount applied (amber)
  - Delivery (free)
  - Total paid
- Delivery window card (slate-100 bg + truck icon)
- ARIA bridge note: "ARIA logged this session. If anything was unavailable, PULSE will flag it."
- Continue shopping button

---

## PULSE Dashboard (Streamlit) — 4 screens

### Screen 5: Manager Login
**Route:** Streamlit app root  
**Purpose:** Authenticated manager access  
**Layout:** Dark page (#0f172a) + centered white card

**Key differences from ARIA login:**
- Dark page background (operations context)
- "PULSE agent active · 3 alerts pending" badge (amber)
- "OPERATIONS DASHBOARD" tagline below logo
- Store selector dropdown added
- "Access dashboard" CTA (not "Sign in")
- Security notice at bottom

---

### Screen 6: Main Dashboard
**Route:** Streamlit main view  
**Purpose:** Overview of all operational alerts  
**Layout:** Dark nav + 2-column (sidebar | main)

**Dark nav (44px, #0f172a):**
- Logo (light) + "/ PULSE Operations" breadcrumb
- Live pill (pulse green)
- Last refresh timestamp
- Manager avatar

**Streamlit sidebar (200px, #f1f5f9):**
- Store selector
- Period selector (Last 48 hours)
- Refresh button (mira-600)
- Last updated timestamp
- Alert summary counts (stockouts / perishable / POs pending)

**Main area (#f1f5f9):**

Metric cards row (3 columns, white):
- Incidents (48h) + delta
- Revenue at risk (AED) in danger red + delta
- POs pending in amber + context

Alert cards (white, stacked):
- Stockout cards: 3px left border, danger red
- Perishable cards: 3px left border, amber
- Approved cards: 3px left border, success green
- Each card: header (title + AED impact) | body (root cause + evidence) | footer (approve/reject)

---

### Screen 7: Alert Detail — Stockout
**Route:** Streamlit on alert click  
**Purpose:** Full root cause + evidence + PO approval  
**Layout:** 2-column (detail | sidebar widgets)

**Left column:**
- Breadcrumb navigation
- Impact metrics row (3 cards: lost / at risk / recoverable)
- Root cause narrative with confidence badge
- Full evidence block (data sources, row counts, formula)
- PO details (product, quantity, urgency, supplier, justification)
- Human-in-loop disclaimer
- Approve / Reject buttons (full width)

**Right column:**
- Stockout prediction card (BigQuery ML output)
- Incident timeline card

---

### Screen 8: Perishable Discount Panel
**Route:** Streamlit perishable tab  
**Purpose:** Velocity-based discount proposal + approval  
**Layout:** 2-column (alert + approved | flow explainer + tiers)

**Left column:**
- Active perishable alert (amber left border):
  - 4-metric row (stock / days left / will expire / recoverable)
  - Discount recommendation box (pulse-50 bg)
  - Evidence block
  - Approve discount / Reject buttons
  - "Once approved, ARIA will surface this" note
- Approved alert (green left border, shows result)

**Right column:**
- "How discounts reach customers" — 5-step numbered flow
- Discount tiers reference card (3 / 2 / 1 days → 15% / 25% / 40%)

---

## Component states to implement

### Product card states
| State | Background | Border | Button |
|-------|-----------|--------|--------|
| Default | white | slate-200 | mira-600 "Add" |
| Hover | white | mira-200 | mira-600 "Add" |
| Added by ARIA | mira-50 | mira-200 | mira-700 "✓ Added" |
| Out of stock | danger-50 | danger-border | slate-300 disabled |
| Discounted | white | pulse-200 | pulse-500 "X% off" badge |

### Alert card states
| State | Left border | Background | CTA |
|-------|------------|-----------|-----|
| Stockout | danger red | white | Approve PO |
| Perishable | amber | white | Approve discount |
| Approved | success green | white | View result |
| Pending review | slate | white | Review |

### Button states
| State | Background | Color |
|-------|-----------|-------|
| Default | mira-600 | white |
| Hover | mira-700 | white |
| Disabled | slate-300 | slate-400 |
| Loading | mira-600 | white + spinner |

---

## Navigation flow

```
ARIA APP
Login → Main Store (browse) → [open ARIA] → ARIA in Action → Order Confirmed
                           → [click product] → (product quick view — future)

PULSE DASHBOARD  
Login → Main Dashboard → [click alert] → Alert Detail → [approve/reject]
                      → [perishable tab] → Perishable Panel → [approve/reject]
```

---

## Responsive notes

- ARIA app: minimum width 900px (3-column layout)
- Below 900px: ARIA panel hides to tab, sidebar collapses to top filter bar
- PULSE dashboard: minimum width 800px (Streamlit native)
- Both apps: desktop-first for hackathon, mobile is Phase 2

---

*MIRA Retail · Screen Inventory v1.0 · ARC Project · Pragmatic Engineers*
