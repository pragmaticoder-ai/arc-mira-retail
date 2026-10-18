'use client'

// components/CartPreview.tsx
// Live cart within the ARIA panel (mira-50 bg). Item list, promotion saving,
// running total, confirm order button. Confirm triggers the order flow in AriaPanel.

import { useCart } from '@/context/CartContext'

interface CartPreviewProps {
  onConfirm: () => void
  confirming: boolean
}

export function CartPreview({ onConfirm, confirming }: CartPreviewProps) {
  const { items, total_aed, promotion, removeProduct, quoteId } = useCart()
  if (items.length === 0) return null

  return (
    <div className="border-t border-mira-100 bg-mira-50 p-md">
      <h3 className="mb-sm text-xs font-medium uppercase tracking-wide text-mira-800">
        Cart · {items.length} items
      </h3>
      <ul className="mb-sm flex max-h-40 flex-col gap-1 overflow-y-auto">
        {items.map((i) => (
          <li
            key={i.product_id}
            className="flex items-center justify-between text-sm text-slate-700"
          >
            <span className="flex-1 truncate">
              {i.quantity}× {i.product_name}
              {i.substituted && (
                <span className="ml-1 text-xs text-amber-600">(subst.)</span>
              )}
            </span>
            <span className="ml-2 tabular-nums text-slate-600">
              {(i.price_aed * i.quantity).toFixed(2)}
            </span>
            <button disabled={confirming} onClick={() => removeProduct(i.product_id)} aria-label={`Remove ${i.product_name}`} className="ml-2 text-xs text-slate-500">Remove</button>
          </li>
        ))}
      </ul>

      {promotion && (
        <div className="mb-sm flex items-center justify-between text-sm text-amber-700">
          <span>{promotion.promotion_name}</span>
          <span>-AED {promotion.discount_aed.toFixed(2)}</span>
        </div>
      )}

      <div className="mb-sm flex items-center justify-between border-t border-mira-100 pt-sm text-base font-medium text-slate-800">
        <span>Total</span>
        <span className="tabular-nums">AED {total_aed.toFixed(2)}</span>
      </div>

      <button
        type="button"
        onClick={onConfirm}
        disabled={confirming}
        className="btn-primary w-full"
      >
        {confirming ? 'Updating…' : quoteId ? 'Confirm order' : 'Review updated basket'}
      </button>
    </div>
  )
}
