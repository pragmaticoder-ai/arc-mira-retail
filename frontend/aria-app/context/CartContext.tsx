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
  useEffect,
  useState,
} from 'react'
import type {
  AppliedPromotion,
  Product,
  CartItem,
  CartState,
  OrderConfirmation,
} from '@/lib/types'

interface CartContextValue {
  items: CartItem[]
  catalog: Product[]
  setCatalog: (products: Product[]) => void
  registerProducts: (products: Product[]) => void
  quoteId: string | null
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
  setQuantity: (productId: string, quantity: number) => void
  hydrated: boolean
  setOrder: (order: OrderConfirmation | null) => void
  reset: () => void
}

const CartContext = createContext<CartContextValue | null>(null)

export function CartProvider({ children }: { children: React.ReactNode }) {
  const [catalog, setCatalog] = useState<Product[]>([])
  const [quoteId, setQuoteId] = useState<string | null>(null)
  const [hydrated, setHydrated] = useState(false)
  const [items, setItems] = useState<CartItem[]>([])
  const [promotion, setPromotion] = useState<AppliedPromotion | null>(null)
  const [order, setOrderState] = useState<OrderConfirmation | null>(null)

  useEffect(() => {
    try {
      const saved = JSON.parse(sessionStorage.getItem('arc-checkout') || 'null')
      if (Array.isArray(saved?.items)) {
        setItems(saved.items); setPromotion(saved.promotion || null); setOrderState(saved.order || null); setQuoteId(saved.quoteId || null); setCatalog(Array.isArray(saved.catalog) ? saved.catalog : [])
      }
    } catch { /* A corrupt local snapshot starts a fresh basket. */ }
    setHydrated(true)
  }, [])
  useEffect(() => {
    if (hydrated) sessionStorage.setItem('arc-checkout', JSON.stringify({ items, promotion, order, quoteId, catalog: catalog.filter(p=>items.some(i=>i.product_id===p.product_id)) }))
  }, [hydrated, items, promotion, order, quoteId, catalog])

  const registerProducts = useCallback((products: Product[]) => {
    setCatalog(previous => {
      const merged = new Map(previous.map(p => [p.product_id, p]))
      products.forEach(p => merged.set(p.product_id, p))
      return Array.from(merged.values()).slice(-2000)
    })
  }, [])

  const recompute = useCallback(
    (next: CartItem[], promo: AppliedPromotion | null) => {
      const subtotal = next.reduce((s, i) => s + i.price_aed * i.quantity, 0)
      return +Math.max(0, subtotal - (promo?.discount_aed ?? 0)).toFixed(2)
    },
    [],
  )

  const setCart = useCallback((cart: CartState) => {
    setItems(cart.items)
    setPromotion(cart.promotion)
    setQuoteId(cart.quote_id ?? null)
  }, [])

  const addProduct = useCallback((productId: string, quantity = 1) => {
    const p = catalog.find((product) => product.product_id === productId)
    if (!p || quantity <= 0 || p.stock_quantity < quantity) return
    setPromotion(null)
    setQuoteId(null)
    setItems((prev) => {
      const existing = prev.find((i) => i.product_id === productId)
      if (existing) {
        if (existing.quantity + quantity > p.stock_quantity) return prev
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
  }, [catalog])

  const removeProduct = useCallback((productId: string) => {
    setPromotion(null)
    setQuoteId(null)
    setItems((prev) => prev.filter((i) => i.product_id !== productId))
  }, [])

  const setQuantity = useCallback((productId: string, quantity: number) => {
    if (!Number.isInteger(quantity) || quantity < 0 || quantity > 1000) return
    if (quantity === 0) { removeProduct(productId); return }
    const product = catalog.find(p=>p.product_id===productId)
    if (!product || quantity > product.stock_quantity) return
    setItems(prev=>prev.map(item=>item.product_id===productId ? {...item,quantity} : item))
    setPromotion(null); setQuoteId(null)
  }, [catalog, removeProduct])

  const setOrder = useCallback((o: OrderConfirmation | null) => {
    setOrderState(o)
  }, [])

  const reset = useCallback(() => {
    setItems([])
    setPromotion(null)
    setOrderState(null)
    setQuoteId(null)
    sessionStorage.removeItem('arc-checkout')
    Object.keys(sessionStorage).filter(key=>key.startsWith('arc-aria-')).forEach(key=>sessionStorage.removeItem(key))
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
    catalog, setCatalog, registerProducts, quoteId,
    total_aed,
    promotion,
    order,
    itemCount,
    productIds,
    setCart,
    addProduct,
    removeProduct, setQuantity, hydrated,
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
