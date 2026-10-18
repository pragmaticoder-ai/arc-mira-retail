'use client'

import Link from 'next/link'
import { useEffect, useRef, useState } from 'react'
import { useCart } from '@/context/CartContext'

export function CustomerMenu() {
  const {customer}=useCart()
  const [open,setOpen]=useState(false)
  const [busy,setBusy]=useState(false)
  const [error,setError]=useState('')
  const menu=useRef<HTMLDivElement>(null)
  useEffect(()=>{
    const outside=(e:MouseEvent)=>{if(!menu.current?.contains(e.target as Node))setOpen(false)}
    const escape=(e:KeyboardEvent)=>{if(e.key==='Escape')setOpen(false)}
    document.addEventListener('click',outside);document.addEventListener('keydown',escape)
    return()=>{document.removeEventListener('click',outside);document.removeEventListener('keydown',escape)}
  },[])
  async function logout() {
    setBusy(true);setError('')
    try {
      const response=await fetch('/api/auth/logout',{method:'POST'})
      if(!response.ok)throw new Error()
      window.location.assign('/login')
    } catch {setBusy(false);setError('Unable to sign out. Please retry.')}
  }
  return <div ref={menu} className="relative">
    <button type="button" aria-label={`Account menu for ${customer?.name || 'customer'}`} aria-haspopup="menu" aria-expanded={open} onClick={()=>setOpen(v=>!v)} className="flex h-9 w-9 items-center justify-center rounded-full bg-mira-600 text-sm font-medium text-white focus:outline-none focus:ring-2 focus:ring-mira-200">{customer?.initials || 'M'}</button>
    {open && <div role="menu" aria-label="Customer account" className="absolute right-0 z-50 mt-3 w-60 rounded-lg border border-slate-200 bg-white p-2 text-sm text-slate-700 shadow-card">
      <div className="border-b border-slate-100 px-3 py-3"><p className="font-medium text-slate-800">{customer?.name || 'MIRA customer'}</p><p className="mt-1 text-xs text-slate-500">{customer?.username}</p></div>
      <Link href="/orders" role="menuitem" onClick={()=>setOpen(false)} className="block rounded px-3 py-2 hover:bg-slate-50">My orders</Link>
      <button role="menuitem" onClick={logout} disabled={busy} className="block w-full rounded px-3 py-2 text-left hover:bg-slate-50 disabled:opacity-50">Switch customer</button>
      <button role="menuitem" onClick={logout} disabled={busy} className="block w-full rounded px-3 py-2 text-left text-mira-700 hover:bg-mira-50 disabled:opacity-50">{busy?'Signing out…':'Sign out'}</button>
      {error && <p role="alert" className="px-3 py-2 text-xs text-red-600">{error}</p>}
    </div>}
  </div>
}
