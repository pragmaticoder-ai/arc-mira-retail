'use client'

// app/page.tsx — Main Store (Screen 2 + 3 from SCREENS.md)
// Full-width nav + 3-column body: category sidebar | product grid | ARIA panel.
// The ARIA panel is always expanded here (ARIA in Action). Browse and chat
// share cart state via CartContext.

import { useEffect, useState } from 'react'
import { useCart } from '@/context/CartContext'
import { NavBar } from '@/components/NavBar'
import { CategorySidebar } from '@/components/CategorySidebar'
import { ProductGrid } from '@/components/ProductGrid'
import { AriaPanel } from '@/components/AriaPanel'
import type { Category, Store, CatalogFacets } from '@/lib/types'

export default function StorePage() {
  const { reset } = useCart()
  const [storeId, setStoreId] = useState('')
  const [customerId, setCustomerId] = useState('')
  const [stores, setStores] = useState<Store[]>([])
  const [error, setError] = useState('')
  const [category, setCategory] = useState<Category | 'all'>('all')
  const [search, setSearch] = useState('')
  const [attributes, setAttributes] = useState<Record<string, string[]>>({})
  const [facets, setFacets] = useState<CatalogFacets>({})
  const [inStock, setInStock] = useState(false)
  const [halalOnly, setHalalOnly] = useState(false)
  const [maxBudget, setMaxBudget] = useState(0)

  useEffect(() => {
    let active = true
    fetch('/api/aria/bootstrap', { cache: 'no-store' })
      .then(async response => {
        if (!response.ok) throw new Error('Store setup is unavailable. Check the backend and database connection.')
        const data = await response.json()
        if (!data.customer?.customer_id || !Array.isArray(data.stores)) throw new Error('Invalid store setup response')
        if (active) {
          setCustomerId(data.customer.customer_id)
          setStoreId(data.default_store_id || data.customer.preferred_store)
          setStores(data.stores)
        }
      })
      .catch(error => { if (active) setError(error.message) })
    return () => { active = false }
  }, [])

  if (error) return <main className="p-8" role="alert">{error}</main>
  if (!customerId) return <main className="p-8">Loading your store…</main>

  return (
    <div className="flex h-screen flex-col overflow-hidden">
      <NavBar search={search} onSearch={setSearch} stores={stores} storeId={storeId} onStoreChange={(id) => { reset(); setStoreId(id) }} />
      <div className="flex flex-1 flex-col overflow-y-auto md:flex-row md:overflow-hidden">
        <CategorySidebar
          facets={facets}
          attributes={attributes}
          onAttributes={setAttributes}
          inStock={inStock}
          onInStock={setInStock}
          active={category}
          onSelect={setCategory}
          halalOnly={halalOnly}
          onHalalToggle={setHalalOnly}
          maxBudget={maxBudget}
          onBudgetChange={setMaxBudget}
        />
        <ProductGrid
          search={search}
          attributes={attributes}
          inStock={inStock}
          onFacets={setFacets}
          category={category}
          halalOnly={halalOnly}
          maxBudget={maxBudget}
          storeId={storeId}
        />
        <AriaPanel key={storeId} storeId={storeId} customerId={customerId} />
      </div>
    </div>
  )
}
