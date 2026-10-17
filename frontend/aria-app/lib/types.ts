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

export interface AriaChatResponse {
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
