'use client'

import { useState } from 'react'
import { CATEGORY_META } from '@/lib/categories'
import type { Category, CatalogFacets } from '@/lib/types'

interface CategorySidebarProps {
  active: Category | 'all'
  onSelect: (c: Category | 'all') => void
  halalOnly: boolean
  onHalalToggle: (v: boolean) => void
  maxBudget: number
  onBudgetChange: (v: number) => void
  facets: CatalogFacets
  attributes: Record<string, string[]>
  onAttributes: (v: Record<string, string[]>) => void
  inStock: boolean
  onInStock: (v: boolean) => void
}
const LABELS: Record<string,string> = { brand:'Brand',product_type:'Product type',pack_size:'Pack size',country_of_origin:'Country of origin',organic:'Organic',vegan:'Vegan',vegetarian:'Vegetarian',gluten_free:'Gluten free',lactose_free:'Lactose free',sugar_free:'Sugar free',halal:'Halal meat only' }

export function CategorySidebar({ active,onSelect,halalOnly,onHalalToggle,maxBudget,onBudgetChange,facets,attributes,onAttributes,inStock,onInStock }: CategorySidebarProps) {
  const [find,setFind]=useState<Record<string,string>>({})
  function toggle(key:string,value:string) {
    const selected=attributes[key] || []
    const next=selected.includes(value)?selected.filter(v=>v!==value):[...selected,value]
    const updated={...attributes}
    if(next.length) updated[key]=next;else delete updated[key]
    onAttributes(updated)
  }
  return <aside className="w-full shrink-0 overflow-y-auto border-r border-slate-200 bg-slate-100 p-md md:w-[220px] md:flex md:flex-col md:gap-md">
    <details open className="mb-md"><summary className="mb-2 cursor-pointer text-sm font-medium text-slate-700">Categories & filters</summary>
      <ul className="flex flex-wrap gap-1 md:flex-col">
        <li><button className={`rounded px-2 py-1 text-left text-sm ${active==='all'?'bg-mira-100 text-mira-700':'text-slate-600'}`} onClick={()=>onSelect('all')}>All groceries</button></li>
        {CATEGORY_META.map(c=><li key={c.id}><button className={`rounded px-2 py-1 text-left text-sm ${active===c.id?'bg-mira-100 text-mira-700':'text-slate-600'}`} onClick={()=>onSelect(c.id)}>{c.emoji} {c.label}</button></li>)}
      </ul>
      <label className="mt-3 flex gap-2 text-sm"><input type="checkbox" checked={inStock} onChange={e=>onInStock(e.target.checked)}/> In stock only</label>
      <label className="mt-2 flex gap-2 text-sm"><input type="checkbox" checked={halalOnly} onChange={e=>onHalalToggle(e.target.checked)}/> Halal meat only</label>
      <label className="mt-3 block text-sm">Maximum price (AED)<input className="input mt-1 w-full" aria-label="Maximum product price in AED" type="number" min="0" step="0.5" value={maxBudget || ''} placeholder="Any price" onChange={e=>onBudgetChange(Math.max(0,Number(e.target.value)))}/></label>
      <button className="mt-3 text-xs text-mira-700 underline" onClick={()=>{onAttributes({});onHalalToggle(false);onInStock(false);onBudgetChange(0)}}>Clear filters</button>
    </details>
    {Object.entries(facets).filter(([key,values])=>key!=='retailer' && key!=='halal' && values.length>0).map(([key,values])=><details open key={key} className="mb-md border-t border-slate-200 pt-3">
      <summary className="cursor-pointer text-sm font-medium text-slate-700">{LABELS[key] || key.replaceAll('_',' ')}</summary>
      {values.length>8 && <input className="input my-2 w-full text-xs" aria-label={`Find ${LABELS[key] || key}`} placeholder="Find…" value={find[key] || ''} onChange={e=>setFind({...find,[key]:e.target.value})}/>}
      <div className="mt-2 max-h-36 overflow-auto">
        {values.filter(v=>v.value.toLowerCase().includes((find[key] || '').toLowerCase())).map(v=><label key={v.value} className="mb-1 flex cursor-pointer items-start gap-2 text-xs text-slate-600">
          <input type="checkbox" checked={(attributes[key] || []).includes(v.value)} onChange={()=>toggle(key,v.value)}/>
          <span className="flex-1 break-words">{v.value==='true'?'Yes':v.value==='false'?'No':v.value}</span><span className="text-slate-400">{v.count}</span>
        </label>)}
      </div>
    </details>)}
    <p className="text-xs text-slate-500">Halal filtering applies to meat. Other dietary filters use stated product attributes.</p>
  </aside>
}
