'use client'

import { useEffect, useRef, useState } from 'react'
import { ProductCard } from '@/components/ProductCard'
import { CATEGORY_META } from '@/lib/categories'
import { useCart } from '@/context/CartContext'
import type { Category, CatalogFacets, CatalogPage } from '@/lib/types'

interface ProductGridProps {
  offersOnly: boolean
  category: Category | 'all'
  halalOnly: boolean
  maxBudget: number
  storeId: string
  search: string
  attributes: Record<string, string[]>
  inStock: boolean
  onFacets: (facets: CatalogFacets) => void
}

export function ProductGrid({ offersOnly, category, halalOnly, maxBudget, storeId, search, attributes, inStock, onFacets }: ProductGridProps) {
  const { productIds, items, addProduct, registerProducts } = useCart()
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(24)
  const [sort, setSort] = useState('name')
  const [data, setData] = useState<CatalogPage | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [debouncedSearch, setDebouncedSearch] = useState(search)
  const section = useRef<HTMLElement>(null)
  const filterKey = JSON.stringify({ offersOnly, category, halalOnly, maxBudget, storeId, search: debouncedSearch, attributes, inStock, sort, pageSize })
  const previousFilter = useRef(filterKey)

  useEffect(() => { const timer = setTimeout(() => setDebouncedSearch(search), 300); return () => clearTimeout(timer) }, [search])
  useEffect(() => {
    const controller = new AbortController()
    // A filter change requests page one immediately, avoiding stale-page flashes.
    const requestedPage = previousFilter.current === filterKey ? page : 1
    if (previousFilter.current !== filterKey) { previousFilter.current = filterKey; setPage(1) }
    const selected = { ...attributes, ...(halalOnly ? { halal: ['true'] } : {}) }
    const params = new URLSearchParams({ store_id: storeId, category, q: debouncedSearch, page: String(requestedPage), page_size: String(pageSize), sort, attributes: JSON.stringify(selected), in_stock: String(inStock), offers_only:String(offersOnly) })
    if (maxBudget > 0) params.set('max_price', String(maxBudget))
    async function load() {
      setLoading(true); setError('')
      try {
        const response = await fetch(`/api/aria/catalog?${params}`, { signal: controller.signal, cache: 'no-store' })
        const body = await response.json()
        if (!response.ok) throw new Error(body.error_message || 'Catalog unavailable')
        if (!Array.isArray(body.items)) throw new Error('Invalid catalog response')
        if (!controller.signal.aborted) {
          setData(body); registerProducts(body.items); onFacets(body.facets)
          section.current?.scrollTo({ top: 0 })
        }
      } catch (err) { if (!controller.signal.aborted) setError(err instanceof Error ? err.message : 'Catalog unavailable') }
      finally { if (!controller.signal.aborted) setLoading(false) }
    }
    void load()
    return () => controller.abort()
  }, [offersOnly, filterKey, page, category, halalOnly, maxBudget, storeId, debouncedSearch, attributes, inStock, sort, pageSize, onFacets, registerProducts])

  const label = offersOnly ? 'Approved offers' : CATEGORY_META.find(c => c.id === category)?.label || 'All groceries'
  return (
    <section ref={section} className="flex-1 overflow-y-auto bg-slate-50 p-lg" aria-busy={loading}>
      <div className="mb-md flex flex-wrap items-center justify-between gap-3">
        <div><h1 className="text-xl font-medium text-slate-800">{label}</h1><p className="text-sm text-slate-500">{data ? `${data.total.toLocaleString()} products` : 'Loading catalog…'}{search ? ` matching “${search}”` : ''}</p></div>
        <div className="flex gap-2 text-sm">
          <select aria-label="Sort products" className="rounded border p-2" value={sort} onChange={e => setSort(e.target.value)}>
            <option value="name">Name A–Z</option><option value="price_asc">Price: low to high</option><option value="price_desc">Price: high to low</option><option value="newest">Recently added</option>
          </select>
          <select aria-label="Products per page" className="rounded border p-2" value={pageSize} onChange={e => setPageSize(Number(e.target.value))}>
            {[24,48,96].map(n => <option key={n} value={n}>{n} per page</option>)}
          </select>
        </div>
      </div>

      <p className="mb-md text-xs text-slate-500">Discover the right pack, compare products and build your MIRA basket.</p>
      {error && <p role="alert" className="mb-md rounded bg-amber-50 p-md text-amber-800">{error}</p>}
      {loading ? <p role="status" className="py-10 text-slate-500">Loading products…</p> : data?.items.length ? <>
        <div className="grid grid-cols-2 gap-md md:grid-cols-3 xl:grid-cols-4">
          {data.items.map(product => <ProductCard key={product.product_id} product={product} quantity={items.find(item=>item.product_id===product.product_id)?.quantity || 0} added={productIds.has(product.product_id)} onAdd={addProduct} />)}
        </div>
        <nav aria-label="Product pagination" className="mt-6 flex flex-wrap items-center justify-center gap-3 pb-5">
          <button className="btn-secondary disabled:opacity-40" disabled={page <= 1} onClick={() => setPage(p => p-1)}>Previous</button>
          <label className="text-sm">Page <select aria-label="Page" className="mx-1 rounded border p-2" value={page} onChange={e => setPage(Number(e.target.value))}>{Array.from({ length: data.total_pages }, (_, i) => <option key={i+1} value={i+1}>{i+1}</option>)}</select> of {data.total_pages}</label>
          <button className="btn-secondary disabled:opacity-40" disabled={page >= data.total_pages} onClick={() => setPage(p => p+1)}>Next</button>
        </nav>
      </> : !error && <p className="py-10 text-slate-500">No products match. Try removing a filter or changing your search.</p>}
    </section>
  )
}
