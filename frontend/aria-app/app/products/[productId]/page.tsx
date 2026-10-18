'use client'

import Link from 'next/link'
import { useEffect,useState } from 'react'
import { useCart } from '@/context/CartContext'
import type { Product } from '@/lib/types'

export default function ProductDetails({ params }: { params: { productId: string } }) {
  const [product,setProduct]=useState<Product|null>(null)
  const [error,setError]=useState('')
  const [image,setImage]=useState('')
  const [back,setBack]=useState('/')
  const { registerProducts,addProduct,items }=useCart()
  useEffect(()=>{
    const controller=new AbortController()
    const query=new URLSearchParams(window.location.search)
    const store=query.get('store_id') || 'dubai_marina_01'
    const returnTo=query.get('return_to') || `/?store_id=${encodeURIComponent(store)}`
    setBack(returnTo==='/' || returnTo.startsWith('/?') ? returnTo : '/')
    fetch(`/api/aria/products/${encodeURIComponent(params.productId)}?store_id=${encodeURIComponent(store)}`,{signal:controller.signal,cache:'no-store'})
      .then(async response=>{const body=await response.json();if(!response.ok)throw new Error(body.error_message || 'Product unavailable');return body})
      .then(body=>{if(!controller.signal.aborted){setProduct(body);setImage(body.image_url || '');registerProducts([body])}})
      .catch(error=>{if(!controller.signal.aborted)setError(error.message)})
    return()=>controller.abort()
  },[params.productId,registerProducts])
  if(error)return <main className="p-8"><Link href={back} className="text-mira-700 underline">Back to groceries</Link><p role="alert" className="mt-4">{error}</p></main>
  if(!product)return <main className="p-8" role="status">Loading product details…</main>
  const price=product.discount_active && product.discounted_price_aed!=null?product.discounted_price_aed:product.price_aed
  const quantity=items.find(i=>i.product_id===product.product_id)?.quantity || 0
  return <main className="mx-auto max-w-6xl p-5 md:p-10">
    <Link href={back} className="text-sm text-mira-700 underline">← Back to groceries</Link>
    <div className="mt-6 grid gap-8 md:grid-cols-2">
      <div><div className="flex h-80 items-center justify-center rounded-lg border bg-white p-5">{image?<img src={image} alt={product.product_name} className="h-full w-full object-contain"/>:<span className="text-slate-400">No image provided</span>}</div>
        <div className="mt-3 flex gap-2 overflow-x-auto">{(product.images || []).map(src=><button aria-label="View product image" onClick={()=>setImage(src)} key={src} className={`h-16 w-16 shrink-0 rounded border p-1 ${image===src?'border-mira-600':''}`}><img src={src} alt="" className="h-full w-full object-contain" loading="lazy"/></button>)}</div>
      </div>
      <div><p className="text-sm text-slate-500">{product.brand}</p><h1 className="mt-1 text-2xl font-medium">{product.product_name}</h1>
        <p className="mt-4 text-2xl font-medium text-mira-700">AED {price.toFixed(2)} <span className="text-sm font-normal text-slate-500">{product.attributes?.pack_size || ''}{product.unit_type && product.unit_type!=='qty'?` · ${product.unit_type}`:''}</span></p>
        <p className="mt-2 text-sm text-slate-600">{product.stock_quantity>0?`${product.stock_quantity} in stock`:'Currently unavailable'}</p>
        <button disabled={product.stock_quantity<=0} onClick={()=>addProduct(product.product_id)} className="btn-primary mt-5 disabled:opacity-40">{quantity?`In basket (${quantity}) · add one`:'Add to cart'}</button>

        <dl className="mt-5 grid grid-cols-2 gap-x-4 gap-y-2 text-sm">{Object.entries(product.attributes || {}).map(([key,value])=><div key={key}><dt className="text-slate-500">{key.replaceAll('_',' ')}</dt><dd>{value==='true'?'Yes':value==='false'?'No':value}</dd></div>)}</dl>
        {product.category==='halal_meat' && !product.dietary_flags.split(',').includes('halal') && <p className="mt-3 text-xs text-slate-500">Halal certification is unverified.</p>}
      </div>
    </div>
    {product.description && <section className="mt-10"><h2 className="mb-3 text-lg font-medium">About this product</h2><p className="whitespace-pre-line text-sm leading-6 text-slate-600">{product.description}</p></section>}
  </main>
}
