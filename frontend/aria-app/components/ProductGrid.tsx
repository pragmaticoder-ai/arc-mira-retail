'use client'

// components/ProductGrid.tsx
// Responsive product grid (slate-50 area). Filters by category, halal, and
// max price. Reads cart.productIds to show the "Added by ARIA" state.

import { useMemo } from 'react'
import { ProductCard } from '@/components/ProductCard'
import { useCart } from '@/context/CartContext'
import { MOCK_PRODUCTS } from '@/lib/mockProducts'
import type { Category } from '@/lib/types'

interface ProductGridProps {
  category: Category | 'all'
  halalOnly: boolean
  maxBudget: number
  storeId: string
}

export function ProductGrid({
  category,
  halalOnly,
  maxBudget,
  storeId,
}: ProductGridProps) {
  const { productIds, addProduct } = useCart()

  const products = useMemo(() => {
    return MOCK_PRODUCTS.filter((p) => {
      if (p.store_id !== storeId) return false
      if (category !== 'all' && p.category !== category) return false
      if (halalOnly && !p.dietary_flags.includes('halal')) return false
      const effectivePrice =
        p.discount_active && p.discounted_price_aed
          ? p.discounted_price_aed
          : p.price_aed
      if (maxBudget > 0 && effectivePrice > maxBudget) return false
      return true
    })
  }, [category, halalOnly, maxBudget, storeId])

  return (
    <section className="flex-1 overflow-y-auto bg-slate-50 p-lg">
      <div className="mb-md flex items-baseline justify-between">
        <h1 className="text-xl font-medium text-slate-800">
          {category === 'all' ? 'All groceries' : category.replace('_', ' ')}
        </h1>
        <span className="text-sm text-slate-400">{products.length} items</span>
      </div>

      {products.length === 0 ? (
        <p className="text-sm text-slate-500">
          No products match these filters at this store.
        </p>
      ) : (
        <div className="grid grid-cols-2 gap-md md:grid-cols-3 xl:grid-cols-4">
          {products.map((p) => (
            <ProductCard
              key={p.product_id}
              product={p}
              added={productIds.has(p.product_id)}
              onAdd={addProduct}
            />
          ))}
        </div>
      )}
    </section>
  )
}
