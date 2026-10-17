'use client'

// components/NavBar.tsx
// Dark top nav (#0f172a / slate-900) per BRAND.md. Light logo variant,
// search box, store selector, cart button with live count, avatar.

import { MiraLogo } from '@/components/MiraLogo'
import { useCart } from '@/context/CartContext'
import { MOCK_STORES } from '@/lib/mockData'

interface NavBarProps {
  storeId: string
  onStoreChange: (storeId: string) => void
}

export function NavBar({ storeId, onStoreChange }: NavBarProps) {
  const { itemCount } = useCart()

  return (
    <header className="flex h-14 items-center justify-between bg-slate-900 px-md">
      <div className="flex items-center gap-lg">
        <MiraLogo size="sm" variant="light" />
        <nav className="hidden items-center gap-md text-sm text-slate-300 md:flex">
          <a className="font-medium text-white" href="/">
            Grocery
          </a>
          <a className="hover:text-white" href="/#offers">
            Offers
          </a>
          <a className="hover:text-white" href="/#orders">
            Orders
          </a>
        </nav>
      </div>

      <div className="flex items-center gap-sm">
        <input
          type="search"
          placeholder="Search groceries"
          aria-label="Search groceries"
          className="hidden w-56 rounded-md border border-slate-700 bg-slate-800 px-3 py-1.5 text-sm text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-mira-600 sm:block"
        />
        <select
          value={storeId}
          onChange={(e) => onStoreChange(e.target.value)}
          aria-label="Select store"
          className="rounded-md border border-slate-700 bg-slate-800 px-2 py-1.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-mira-600"
        >
          {MOCK_STORES.map((s) => (
            <option key={s.store_id} value={s.store_id}>
              {s.store_name}
            </option>
          ))}
        </select>

        <button
          type="button"
          aria-label={`Cart, ${itemCount} items`}
          className="relative flex h-9 w-9 items-center justify-center rounded-md text-slate-200 hover:bg-slate-800"
        >
          <span aria-hidden="true">🛒</span>
          {itemCount > 0 && (
            <span className="absolute -right-1 -top-1 flex h-5 min-w-5 items-center justify-center rounded-full bg-amber-500 px-1 text-xs font-medium text-white">
              {itemCount}
            </span>
          )}
        </button>

        <div
          aria-hidden="true"
          className="flex h-9 w-9 items-center justify-center rounded-full bg-mira-600 text-sm font-medium text-white"
        >
          S
        </div>
      </div>
    </header>
  )
}
