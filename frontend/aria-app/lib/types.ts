// lib/types.ts
// Types mirror DATA_MODEL.md (AlloyDB) and AGENT_CONTRACTS.md exactly.
// Keep these field names identical to the backend so mock data drops into
// the real agent response with no reshaping.

export type DietaryPreference = 'halal' | 'vegetarian' | 'vegan' | 'none'

export type Category =
  | 'dairy'
  | 'grains'
  | 'halal_meat'
  | 'vegetables'
  | 'fruits'
  | 'beverages'
  | 'snacks'
  | 'condiments'

// ── inventory table (DATA_MODEL.md §1) ──────────────────────────────
export interface Product {
  image_url?: string | null
  images?: string[]
  description?: string
  attributes?: Record<string, string>
  unit_type?: string
  source_category?: string
  product_id: string
  product_name: string
  category: Category
  brand: string
  price_aed: number
  dietary_flags: string // comma-separated: "halal,vegetarian"
  store_id: string
  aisle_ref: string
  stock_quantity: number
  reorder_threshold: number
  supplier_id: string
  // Perishable discount surfacing (ARIA system prompt + PULSE discount tool)
  discount_active: boolean
  discount_pct?: number
  discounted_price_aed?: number
  is_perishable: boolean
  expiry_date?: string // ISO date
}

// ── customer_profiles table (DATA_MODEL.md §1) ──────────────────────
export interface CustomerProfile {
  customer_id: string
  name: string
  email: string
  dietary_preference: DietaryPreference
  household_size: number
  weekly_budget_aed: number
  preferred_store: string
}

// ── stores table ────────────────────────────────────────────────────
export interface Store {
  store_id: string
  store_name: string
  area: string
  city: string
}

// ── promotions table (DATA_MODEL.md §1) ─────────────────────────────
export interface Promotion {
  promotion_id: string
  name: string
  description: string
  category: string
  dietary_filter: string | null
  discount_pct: number
  min_cart_aed: number
  valid_from: string
  valid_until: string
  is_active: boolean
}

// ── build_cart response item (AGENT_CONTRACTS.md #3) ────────────────
export interface CartItem {
  product_id: string
  product_name: string
  quantity: number
  price_aed: number
  aisle_ref: string
  in_stock: boolean
  substituted?: boolean
  discount_active?: boolean
}

export interface AppliedPromotion {
  promotion_id: string
  promotion_name: string
  discount_aed: number
  new_total_aed: number
}

// ── Agent API contract: POST /aria/chat ─────────────────────────────
export type ReasoningStepType = 'THOUGHT' | 'ACTION' | 'OBSERVATION'

export interface ReasoningStep {
  type: ReasoningStepType
  text: string
}

export interface CartState {
  items: CartItem[]
  total_aed: number
  promotion: AppliedPromotion | null
  quote_id?: string | null
}

export interface OrderConfirmation {
  order_id: string
  status: string
  total_aed: number
  estimated_delivery_window: string
}

export interface AriaChatRequest {
  session_id: string
  customer_id: string
  store_id: string
  message: string
}

export interface DemandSignal {
  product_id: string
  product_name: string
  outcome: 'satisfied' | 'compromise' | 'rejected' | 'abandoned' | 'fulfilled' | 'unknown'
  evidence: string
  certainty: string
}
export interface SubstitutionOffer {
  product_id: string
  product_name: string
  substitute_product_id: string | null
  substitute_name: string | null
  outcome: string
}
export interface AriaChatResponse {
  cart_changed?: boolean
  session_id: string
  quote_id: string | null
  demand_signals: DemandSignal[]
  substitution_offers: SubstitutionOffer[]
  mode: string
  reply: string
  cart: CartState
  reasoning: ReasoningStep[]
  order: OrderConfirmation | null
  session_logged: boolean
}

// ── Chat UI message model ───────────────────────────────────────────
export interface ChatMessage {
  id: string
  role: 'aria' | 'user'
  text: string
  reasoning?: ReasoningStep[]
  thinking?: boolean
}

export type CatalogFacets = Record<string, { value: string; count: number }[]>
export interface CatalogPage {
  items: Product[]
  total: number
  page: number
  page_size: number
  total_pages: number
  facets: CatalogFacets
  price_range: { min: number; max: number }
}
