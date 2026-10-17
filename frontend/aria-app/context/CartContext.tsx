'use client'

// context/CartContext.tsx
// Shared cart + ARIA session state. ProductGrid reads which items ARIA added
// (to show the "Added by ARIA" state); AriaPanel drives the cart as the agent
// builds it. State shape follows the Agent API contract (CartState).

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
} from 'react'
import type {
  AppliedPromotion,
  CartItem,
  CartState,
  OrderConfirmation,
} from '@/lib/types'
import { getProductById } from '@/lib/mockProducts'

interface CartContextValue {
  items: CartItem[]
  total_aed: number
  promotion: AppliedPromotion | null
  order: OrderConfirmation | null
  itemCount: number
  /** product_ids currently in the cart — used by ProductGrid for the added state. */
  productIds: Set<string>
  /** Replace the whole cart (ARIA build_cart / optimize / promotion results). */
  setCart: (cart: CartState) => void
  /** Manual add from the product grid. */
  addProduct: (productId: string, quantity?: number) => void
  removeProduct: (productId: string) => void
  setOrder: (order: OrderConfirmation | null) => void
  reset: () => void
}

const CartContext = createContext<CartContextValue | null>(null)

export function CartProvider({ children }: { children: React.ReactNode }) {
  const [items, setItems] = useState<CartItem[]>([])
  const [promotion, setPromotion] = useState<AppliedPromotion | null>(null)
  const [order, setOrderState] = useState<OrderConfirmation | null>(null)

  const recompute = useCallback(
    (next: CartItem[], promo: AppliedPromotion | null) => {
      const subtotal = next.reduce((s, i) => s + i.price_aed * i.quantity, 0)
      return promo ? promo.new_total_aed : +subtotal.toFixed(2)
    },
    [],
  )

  const setCart = useCallback((cart: CartState) => {
    setItems(cart.items)
    setPromotion(cart.promotion)
  }, [])

  const addProduct = useCallback((productId: string, quantity = 1) => {
    const p = getProductById(productId)
    if (!p) return
    setItems((prev) => {
      const existing = prev.find((i) => i.product_id === productId)
      if (existing) {
        return prev.map((i) =>
          i.product_id === productId
            ? { ...i, quantity: i.quantity + quantity }
            : i,
        )
      }
      const price =
        p.discount_active && p.discounted_price_aed
          ? p.discounted_price_aed
          : p.price_aed
      const item: CartItem = {
        product_id: p.product_id,
        product_name: p.product_name,
        quantity,
        price_aed: price,
        aisle_ref: p.aisle_ref,
        in_stock: p.stock_quantity > 0,
        substituted: false,
        discount_active: p.discount_active,
      }
      return [...prev, item]
    })
  }, [])

  const removeProduct = useCallback((productId: string) => {
    setItems((prev) => prev.filter((i) => i.product_id !== productId))
  }, [])

  const setOrder = useCallback((o: OrderConfirmation | null) => {
    setOrderState(o)
  }, [])

  const reset = useCallback(() => {
    setItems([])
    setPromotion(null)
    setOrderState(null)
  }, [])

  const total_aed = useMemo(
    () => recompute(items, promotion),
    [items, promotion, recompute],
  )
  const itemCount = useMemo(
    () => items.reduce((s, i) => s + i.quantity, 0),
    [items],
  )
  const productIds = useMemo(
    () => new Set(items.map((i) => i.product_id)),
    [items],
  )

  const value: CartContextValue = {
    items,
    total_aed,
    promotion,
    order,
    itemCount,
    productIds,
    setCart,
    addProduct,
    removeProduct,
    setOrder,
    reset,
  }

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>
}

export function useCart(): CartContextValue {
  const ctx = useContext(CartContext)
  if (!ctx) throw new Error('useCart must be used within CartProvider')
  return ctx
}
