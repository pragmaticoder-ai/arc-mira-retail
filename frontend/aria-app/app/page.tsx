'use client'

// app/page.tsx — Main Store (Screen 2 + 3 from SCREENS.md)
// Full-width nav + 3-column body: category sidebar | product grid | ARIA panel.
// The ARIA panel is always expanded here (ARIA in Action). Browse and chat
// share cart state via CartContext.

import { useState } from 'react'
import { NavBar } from '@/components/NavBar'
import { CategorySidebar } from '@/components/CategorySidebar'
import { ProductGrid } from '@/components/ProductGrid'
import { AriaPanel } from '@/components/AriaPanel'
import { DEFAULT_CUSTOMER } from '@/lib/mockData'
import type { Category } from '@/lib/types'

export default function StorePage() {
  const [storeId, setStoreId] = useState(DEFAULT_CUSTOMER.preferred_store)
  const [category, setCategory] = useState<Category | 'all'>('all')
  const [halalOnly, setHalalOnly] = useState(false)
  const [maxBudget, setMaxBudget] = useState(0)

  return (
    <div className="flex h-screen flex-col overflow-hidden">
      <NavBar storeId={storeId} onStoreChange={setStoreId} />
      <div className="flex flex-1 overflow-hidden">
        <CategorySidebar
          active={category}
          onSelect={setCategory}
          halalOnly={halalOnly}
          onHalalToggle={setHalalOnly}
          maxBudget={maxBudget}
          onBudgetChange={setMaxBudget}
        />
        <ProductGrid
          category={category}
          halalOnly={halalOnly}
          maxBudget={maxBudget}
          storeId={storeId}
        />
        <AriaPanel storeId={storeId} customerId={DEFAULT_CUSTOMER.customer_id} />
      </div>
    </div>
  )
}
