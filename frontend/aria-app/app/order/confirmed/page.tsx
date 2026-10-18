'use client'

// app/order/confirmed/page.tsx — Screen 4: Order Confirmed (SCREENS.md)
// Centered card. Success icon, order summary, delivery window, and the
// ARIA→PULSE bridge note that sets up the operations half of the demo.

import Link from 'next/link'
import { useCart } from '@/context/CartContext'

export default function OrderConfirmedPage() {
  const { order, items, total_aed, promotion, reset } = useCart()

  if (!order) return <main className="flex min-h-screen items-center justify-center bg-slate-50 p-md"><div className="text-center"><h1 className="text-xl">No confirmed order</h1><Link href="/" onClick={reset} className="btn-primary mt-md block">Return to the store</Link></div></main>

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 p-md">
      <div className="w-[400px] rounded-lg border border-slate-200 bg-white p-lg shadow-card">
        <div className="mb-md flex flex-col items-center gap-sm text-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-full bg-green-50 text-2xl text-green-600">
            ✓
          </div>
          <h1 className="text-xl font-medium text-slate-800">Order confirmed</h1>
          <p className="text-sm text-slate-500">
            {order ? (
              <>
                Order <span className="font-medium text-slate-700">{order.order_id}</span> · MIRA Dubai Marina
              </>
            ) : (
              'MIRA Dubai Marina'
            )}
          </p>
        </div>

        <div className="mb-md rounded-md bg-mira-50 p-md text-sm">
          <div className="mb-1 flex justify-between text-slate-600">
            <span>{items.length} items</span>
            <span className="tabular-nums">
              AED {(promotion ? total_aed + promotion.discount_aed : total_aed || 0).toFixed(2)}
            </span>
          </div>
          {promotion && (
            <div className="mb-1 flex justify-between text-amber-700">
              <span>{promotion.promotion_name}</span>
              <span>-AED {promotion.discount_aed.toFixed(2)}</span>
            </div>
          )}
          <div className="mb-1 flex justify-between text-slate-600">
            <span>Delivery</span>
            <span className="text-green-600">Free</span>
          </div>
          <div className="flex justify-between border-t border-mira-100 pt-sm text-base font-medium text-slate-800">
            <span>Order total</span>
            <span className="tabular-nums">AED {(order?.total_aed ?? total_aed).toFixed(2)}</span>
          </div>
        </div>

        <div className="mb-md flex items-center gap-2 rounded-md bg-slate-100 p-md text-sm text-slate-600">
          <span aria-hidden="true" className="text-lg">🚚</span>
          <span>
            Delivery {order.estimated_delivery_window}
          </span>
        </div>

        <div className="mb-md rounded-md border border-amber-200 bg-amber-50 p-md text-sm text-amber-800">
          This is a local prototype order. ARIA recorded this session and its original product preferences. If anything was unavailable, PULSE will flag
          it to the store manager automatically.
        </div>

        <Link href="/orders" className="btn-secondary mb-md block w-full text-center">View my orders</Link>
        <Link href="/" onClick={reset} className="btn-primary block w-full text-center">
          Continue shopping
        </Link>
      </div>
    </main>
  )
}
