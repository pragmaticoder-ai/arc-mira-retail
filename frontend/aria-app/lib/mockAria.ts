// lib/mockAria.ts
// Scripted ARIA responses for the demo, returning the exact Agent API
// contract shape (AriaChatResponse). Swapped for the real agent when
// ARIA_AGENT_URL is set. The scripted flow mirrors the README demo:
//   1. Sarah asks for weekly halal groceries, family of 4, AED 300
//   2. ARIA builds a cart; brown rice is out of stock
//   3. ARIA substitutes brown rice with basmati, within 20% price
//   4. ARIA applies the dairy saver promotion
//   5. Sarah confirms → order placed → session logged

import {
  AriaChatRequest,
  AriaChatResponse,
  CartItem,
  CartState,
  ReasoningStep,
} from './types'
import { getProductById } from './mockProducts'

const CONFIRM_PHRASES = ['confirm', 'yes', 'place order', 'go ahead', 'proceed']

function toCartItem(productId: string, quantity: number, opts?: { substituted?: boolean }): CartItem {
  const p = getProductById(productId)!
  const price = p.discount_active && p.discounted_price_aed ? p.discounted_price_aed : p.price_aed
  return {
    product_id: p.product_id,
    product_name: p.product_name,
    quantity,
    price_aed: price,
    aisle_ref: p.aisle_ref,
    in_stock: p.stock_quantity > 0 || !!opts?.substituted,
    substituted: opts?.substituted ?? false,
    discount_active: p.discount_active,
  }
}

// The cart ARIA assembles for the demo weekly-groceries request.
function buildDemoCart(): CartState {
  const items: CartItem[] = [
    toCartItem('milk_almarai_2l', 2),
    toCartItem('eggs_dozen', 1),
    toCartItem('chicken_whole_1kg', 2),
    toCartItem('rice_basmati_5kg', 1, { substituted: true }), // substituted for brown rice
    toCartItem('tomato_1kg', 2),
    toCartItem('onion_1kg', 1),
    toCartItem('banana_1kg', 2),
    toCartItem('bread_white_loaf', 2),
    toCartItem('oil_sunflower_1_8l', 1),
  ]
  const subtotal = items.reduce((sum, i) => sum + i.price_aed * i.quantity, 0)
  const discount = +(subtotal * 0.15).toFixed(2) // dairy saver 15%
  const newTotal = +(subtotal - discount).toFixed(2)
  return {
    items,
    total_aed: newTotal,
    promotion: {
      promotion_id: 'promo_dairy_saver',
      promotion_name: 'Dairy saver pack',
      discount_aed: discount,
      new_total_aed: newTotal,
    },
  }
}

const EMPTY_CART: CartState = { items: [], total_aed: 0, promotion: null }

function isConfirmation(message: string): boolean {
  const m = message.trim().toLowerCase()
  return CONFIRM_PHRASES.some((p) => m === p || m.startsWith(p))
}

export function mockAriaResponse(req: AriaChatRequest): AriaChatResponse {
  const message = req.message.trim().toLowerCase()

  // ── Confirmation → place order + log session ──────────────────────
  if (isConfirmation(message)) {
    const cart = buildDemoCart()
    const reasoning: ReasoningStep[] = [
      { type: 'THOUGHT', text: 'Customer confirmed with "yes". I can place the order now.' },
      { type: 'ACTION', text: 'place_order(customer_id, store_id, cart, promotion_id="promo_dairy_saver", total_aed)' },
      { type: 'OBSERVATION', text: 'Order ORD-20261017-0042 created, status=confirmed.' },
      { type: 'THOUGHT', text: 'Final step: log the session to the BigQuery bridge so PULSE can read it.' },
      { type: 'ACTION', text: 'log_session(... items_unavailable=[brown rice], substitutions=[brown rice→basmati] ...)' },
      { type: 'OBSERVATION', text: 'Session logged to arc_dataset.incidents. PULSE will pick this up.' },
    ]
    return {
      reply:
        'Order placed. Your 9 items total AED ' +
        cart.total_aed.toFixed(2) +
        ' after the Dairy saver discount. Estimated delivery today 6–8 PM. ' +
        'I noted that brown rice was out of stock — our ops team is alerted automatically.',
      cart,
      reasoning,
      order: {
        order_id: 'ORD-20261017-0042',
        status: 'confirmed',
        total_aed: cart.total_aed,
        estimated_delivery_window: 'Today, 6:00–8:00 PM',
      },
      session_logged: true,
    }
  }

  // ── Perishable discount surfacing (laban) ─────────────────────────
  if (message.includes('laban') || message.includes('discount') || message.includes('offer')) {
    const laban = getProductById('laban_almarai_1l')!
    const reasoning: ReasoningStep[] = [
      { type: 'ACTION', text: 'check_stock(product_id="laban_almarai_1l", store_id)' },
      { type: 'OBSERVATION', text: 'available=true, discount_active=true, 25% off, AED 6.00 (was AED 8.00).' },
      { type: 'THOUGHT', text: 'Discount is manager-approved (discount_active=true). I can surface it as a saving.' },
    ]
    return {
      reply:
        'Almarai Laban is on a 25% discount today — AED 6.00 instead of AED 8.00. Want me to add it to your cart?',
      cart: EMPTY_CART,
      reasoning,
      order: null,
      session_logged: false,
    }
  }

  // ── Default: weekly groceries cart build (the main demo path) ─────
  const cart = buildDemoCart()
  const reasoning: ReasoningStep[] = [
    { type: 'ACTION', text: 'get_customer_context(customer_id="sarah_123")' },
    { type: 'OBSERVATION', text: 'dietary_preference=halal, household_size=4, weekly_budget_aed=300, preferred_store=dubai_marina_01.' },
    { type: 'THOUGHT', text: 'Build a weekly halal cart for a family of 4 within AED 300.' },
    { type: 'ACTION', text: 'build_cart(goal="weekly groceries", dietary_preference="halal", budget_aed=300, household_size=4, store_id)' },
    { type: 'OBSERVATION', text: 'Cart built. Brown rice 500g is out of stock (stock_quantity=0).' },
    { type: 'THOUGHT', text: 'Brown rice unavailable — I must find a substitute before telling the customer.' },
    { type: 'ACTION', text: 'suggest_substitution(product_id="rice_brown_500g", dietary_preference="halal", max_price_aed=11.4)' },
    { type: 'OBSERVATION', text: 'Basmati Rice 5kg suggested — halal, in stock, similar grain staple, similarity 0.89.' },
    { type: 'ACTION', text: 'apply_promotion(cart, cart_total_aed, dietary_preference="halal")' },
    { type: 'OBSERVATION', text: 'Dairy saver pack applied: 15% off, saving AED ' + (cart.promotion?.discount_aed.toFixed(2) ?? '0') + '.' },
  ]
  return {
    reply:
      'I built your weekly halal cart for a family of 4. One note: brown rice was out of stock, ' +
      'so I swapped in India Gate Basmati 5kg — same staple, halal, and within budget. ' +
      'I also applied the Dairy saver pack (15% off), bringing your total to AED ' +
      cart.total_aed.toFixed(2) +
      ' of your AED 300 budget. Say "confirm" to place the order.',
    cart,
    reasoning,
    order: null,
    session_logged: false,
  }
}
