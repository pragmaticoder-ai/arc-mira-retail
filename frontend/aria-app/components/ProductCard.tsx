'use client'

// components/ProductCard.tsx
// Product card with all states from SCREENS.md / BRAND.md:
//   default · added-by-ARIA (mira-50) · out-of-stock (danger) · discounted (amber badge)

import { CATEGORY_META } from '@/lib/mockProducts'
import type { Product } from '@/lib/types'

interface ProductCardProps {
  product: Product
  added: boolean
  onAdd: (productId: string) => void
}

export function ProductCard({ product, added, onAdd }: ProductCardProps) {
  const outOfStock = product.stock_quantity <= 0
  const discounted = product.discount_active && product.discounted_price_aed != null
  const emoji = CATEGORY_META.find((c) => c.id === product.category)?.emoji ?? '🛒'

  const borderState = outOfStock
    ? 'border-red-200 bg-red-50'
    : added
      ? 'border-mira-200 bg-mira-50'
      : discounted
        ? 'border-amber-200 bg-white'
        : 'border-slate-200 bg-white hover:border-mira-200'

  return (
    <div className={`flex flex-col rounded-md border p-md transition-colors ${borderState}`}>
      <div className="relative mb-sm flex h-20 items-center justify-center rounded bg-mira-50 text-3xl">
        <span aria-hidden="true">{emoji}</span>
        {discounted && (
          <span className="badge-warning absolute right-1 top-1">
            {product.discount_pct}% off
          </span>
        )}
        {outOfStock && (
          <span className="badge-danger absolute right-1 top-1">Out of stock</span>
        )}
      </div>

      <h3 className="mb-0.5 line-clamp-2 text-sm font-medium text-slate-800">
        {product.product_name}
      </h3>
      <p className="mb-sm text-xs text-slate-400">Aisle {product.aisle_ref}</p>

      <div className="mt-auto flex items-center justify-between">
        <div className="flex items-baseline gap-1">
          {discounted ? (
            <>
              <span className="text-sm font-medium text-amber-600">
                AED {product.discounted_price_aed!.toFixed(2)}
              </span>
              <span className="text-xs text-slate-400 line-through">
                {product.price_aed.toFixed(2)}
              </span>
            </>
          ) : (
            <span className="text-sm font-medium text-mira-600">
              AED {product.price_aed.toFixed(2)}
            </span>
          )}
        </div>
      </div>

      <button
        type="button"
        disabled={outOfStock}
        onClick={() => onAdd(product.product_id)}
        className={
          outOfStock
            ? 'mt-sm w-full cursor-not-allowed rounded-md bg-slate-200 px-4 py-2 text-sm font-medium text-slate-400'
            : added
              ? 'mt-sm w-full rounded-md bg-mira-700 px-4 py-2 text-sm font-medium text-white'
              : 'btn-primary mt-sm w-full'
        }
      >
        {outOfStock ? 'Unavailable' : added ? '✓ Added by ARIA' : 'Add to cart'}
      </button>
    </div>
  )
}
