'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'
import type { OrderRecord, Store } from '@/lib/types'

export default function OrdersPage() {
  const [data,setData]=useState<{items:OrderRecord[];total:number;total_pages:number}|null>(null)
  const [stores,setStores]=useState<Store[]>([])
  const [page,setPage]=useState(1)
  const [refresh,setRefresh]=useState(0)
  const [loading,setLoading]=useState(true)
  const [error,setError]=useState('')
  useEffect(()=>{
    const controller=new AbortController()
    fetch('/api/aria/bootstrap',{signal:controller.signal,cache:'no-store'}).then(r=>r.json()).then(d=>{if(Array.isArray(d.stores))setStores(d.stores)}).catch(()=>{})
    return()=>controller.abort()
  },[])
  useEffect(()=>{
    const controller=new AbortController()
    setLoading(true);setError('')
    fetch(`/api/aria/orders?page=${page}`,{signal:controller.signal,cache:'no-store'}).then(async r=>{
      const d=await r.json()
      if(!r.ok)throw new Error(d.error_message || 'Unable to load orders')
      setData(d)
    }).catch(e=>{if(!controller.signal.aborted)setError(e.message)}).finally(()=>{if(!controller.signal.aborted)setLoading(false)})
    return()=>controller.abort()
  },[page,refresh])
  return <main className="mx-auto min-h-screen max-w-5xl p-5 md:p-10">
    <nav className="mb-6 flex justify-between text-sm text-mira-700"><Link href="/">← Back to groceries</Link><Link href="/cart">View basket</Link></nav>
    <div className="flex items-center justify-between"><h1 className="text-2xl font-medium">My orders</h1><button disabled={loading} className="btn-secondary" onClick={()=>setRefresh(n=>n+1)}>Refresh</button></div>
    <p className="mt-2 text-sm text-slate-500">Confirmed orders from your MIRA stores.</p>
    {error && <p role="alert" className="mt-5 rounded bg-amber-50 p-4 text-amber-800">{error}</p>}
    {loading?<p role="status" className="mt-6">Loading your orders…</p>:!error && (data?.items.length?<>
      <div className="mt-6 space-y-5">{data.items.map(order=><article key={order.order_id} className="rounded-lg border bg-white p-5">
        <div className="flex flex-wrap items-start justify-between gap-3"><div><h2 className="font-medium">Order {order.order_id}</h2><p className="mt-1 text-sm text-slate-500">{new Date(order.created_at).toLocaleString('en-AE',{timeZone:'Asia/Dubai'})} · {stores.find(s=>s.store_id===order.store_id)?.store_name || order.store_id}</p></div><span className="rounded bg-green-50 px-3 py-1 text-sm capitalize text-green-700">{order.status}</span></div>
        <ul className="my-4 divide-y">{order.items.map(item=><li key={item.product_id} className="flex justify-between gap-4 py-2 text-sm"><span>{item.quantity} × {item.product_name}</span><span className="shrink-0">AED {(item.price_aed*item.quantity).toFixed(2)}</span></li>)}</ul>
        <div className="flex flex-wrap justify-between gap-3 border-t pt-4"><p className="text-sm text-slate-600">Delivery: {order.estimated_delivery_window}</p><p className="font-medium">Total AED {order.total_aed.toFixed(2)}</p></div>
      </article>)}</div>
      <nav aria-label="Order pagination" className="mt-6 flex items-center justify-center gap-4"><button disabled={page<=1} className="btn-secondary disabled:opacity-40" onClick={()=>setPage(p=>p-1)}>Previous</button><span>Page {page} of {data.total_pages}</span><button disabled={page>=data.total_pages} className="btn-secondary disabled:opacity-40" onClick={()=>setPage(p=>p+1)}>Next</button></nav>
    </>:<div className="mt-6 rounded-lg border bg-white p-8"><p>No orders yet.</p><p className="mt-2 text-sm text-slate-500">Review and confirm your basket to place your first order.</p><Link href="/cart" className="btn-primary mt-4 inline-block">View basket</Link></div>)}
  </main>
}
