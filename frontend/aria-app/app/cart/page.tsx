'use client'

import Link from 'next/link'
import { CustomerMenu } from '@/components/CustomerMenu'
import { useEffect, useState } from 'react'
import { AriaPanel } from '@/components/AriaPanel'
import { useCart } from '@/context/CartContext'
import type { Product, Store } from '@/lib/types'

export default function CartPage() {
  const {items,catalog,total_aed,promotion,removeProduct,setQuantity,registerProducts,hydrated}=useCart()
  const [setup,setSetup]=useState<{storeId:string;customerId:string;storeName:string}|null>(null)
  const [error,setError]=useState('')
  useEffect(()=>{
    const controller=new AbortController()
    fetch('/api/aria/bootstrap',{signal:controller.signal,cache:'no-store'}).then(async r=>{
      if(!r.ok) throw new Error('Unable to load your store. Please retry.')
      const data=await r.json()
      const requested=new URLSearchParams(window.location.search).get('store_id')
      const storeId=data.stores.some((s:Store)=>s.store_id===requested)?requested:data.default_store_id || data.customer.preferred_store
      setSetup({storeId,customerId:data.customer.customer_id,storeName:data.stores.find((s:Store)=>s.store_id===storeId)?.store_name || 'MIRA'})
    }).catch(e=>{if(!controller.signal.aborted)setError(e.message)})
    return()=>controller.abort()
  },[])
  const productKey=items.map(i=>i.product_id).sort().join(',')
  useEffect(()=>{
    if(!setup || !productKey)return
    const controller=new AbortController()
    Promise.all(productKey.split(',').map(async id=>{
      const r=await fetch(`/api/aria/products/${encodeURIComponent(id)}?store_id=${encodeURIComponent(setup.storeId)}`,{signal:controller.signal,cache:'no-store'})
      return r.ok?await r.json() as Product:null
    })).then(products=>registerProducts(products.filter((p):p is Product=>p!==null))).catch(()=>{/* Checkout always revalidates stock and prices. */})
    return()=>controller.abort()
  },[setup,productKey,registerProducts])
  if(error)return <main className="p-8" role="alert">{error} <Link href="/" className="underline">Back to groceries</Link></main>
  if(!setup || !hydrated)return <main className="p-8" role="status">Loading your basket…</main>
  return <div className="flex min-h-screen flex-col">
    <header className="flex flex-wrap items-center justify-between gap-3 bg-slate-900 px-6 py-4 text-white"><Link href={`/?store_id=${encodeURIComponent(setup.storeId)}`}>← Continue shopping</Link><span>MIRA · {setup.storeName}</span><div className="flex items-center gap-4"><Link href="/orders">My orders</Link><CustomerMenu/></div></header>
    <div className="flex flex-1 flex-col md:flex-row">
      <main className="flex-1 p-5 md:p-10"><h1 className="text-2xl font-medium">Your basket</h1>
        {!items.length?<div className="mt-8 rounded-lg border bg-white p-8"><p>Your basket is empty.</p><Link className="btn-primary mt-4 inline-block" href={`/?store_id=${encodeURIComponent(setup.storeId)}`}>Browse groceries</Link></div>:<>
          <ul className="mt-6 divide-y rounded-lg border bg-white">{items.map(item=>{
            const product=catalog.find(p=>p.product_id===item.product_id)
            return <li key={item.product_id} className="flex flex-wrap items-center gap-4 p-4">
              {product?.image_url && <img src={product.image_url} alt="" className="h-20 w-20 object-contain"/>}
              <div className="min-w-40 flex-1"><Link className="font-medium hover:underline" href={`/products/${encodeURIComponent(item.product_id)}?store_id=${encodeURIComponent(setup.storeId)}&return_to=${encodeURIComponent('/cart?store_id='+setup.storeId)}`}>{item.product_name}</Link><p className="mt-1 text-sm text-slate-500">AED {item.price_aed.toFixed(2)} each</p></div>
              <div className="flex items-center gap-3"><button className="btn-secondary" aria-label={`Decrease ${item.product_name}`} onClick={()=>setQuantity(item.product_id,item.quantity-1)}>−</button><span aria-label={`Quantity of ${item.product_name}`}>{item.quantity}</span><button className="btn-secondary disabled:opacity-40" aria-label={`Increase ${item.product_name}`} disabled={!product || item.quantity>=product.stock_quantity} onClick={()=>setQuantity(item.product_id,item.quantity+1)}>+</button></div>
              <span className="w-24 text-right font-medium">AED {(item.price_aed*item.quantity).toFixed(2)}</span><button className="text-sm text-slate-500 underline" onClick={()=>removeProduct(item.product_id)}>Remove</button>
            </li>
          })}</ul>
          <div className="mt-5 rounded-lg border bg-white p-5">{promotion && <p className="mb-2 text-sm text-green-700">{promotion.promotion_name}: −AED {promotion.discount_aed.toFixed(2)}</p>}<p className="flex justify-between text-xl font-medium"><span>Total</span><span>AED {total_aed.toFixed(2)}</span></p><p className="mt-3 text-sm text-slate-500">Review the basket with ARIA, then confirm the current quote to place your order.</p></div>
        </>}
      </main>
      <AriaPanel storeId={setup.storeId} customerId={setup.customerId}/>
    </div>
  </div>
}
