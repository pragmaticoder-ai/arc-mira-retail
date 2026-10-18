'use client'

import { useState } from 'react'
import { demoCustomers } from '@/lib/customers'
import { MiraLogo } from '@/components/MiraLogo'

export default function LoginPage() {
  const [busy,setBusy]=useState(false)
  const [error,setError]=useState('')
  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();setBusy(true);setError('')
    const form=new FormData(event.currentTarget)
    try {
      const response=await fetch('/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:form.get('username'),password:form.get('password'),remember:form.get('remember')==='on',next:new URLSearchParams(window.location.search).get('next')})})
      const data=await response.json()
      if(!response.ok)throw new Error(data.error_message || 'Unable to sign in. Please retry.')
      window.location.assign(data.redirect)
    } catch(e) {setError(e instanceof Error?e.message:'Unable to sign in. Please retry.');setBusy(false)}
  }
  return <main className="flex min-h-screen items-center justify-center bg-slate-50 px-5 py-12">
    <div className="w-full max-w-[360px] rounded-xl border border-slate-200 bg-white px-7 py-8 shadow-card">
      <div className="mb-6 flex justify-center"><MiraLogo size="lg" variant="color" showTagline/></div>
      <div className="mb-4 text-center"><span className="badge-mira"><span className="mr-1.5 h-1.5 w-1.5 rounded-full bg-mira-600"/>ARIA grocery assistant</span></div>
      <h1 className="text-center text-xl font-semibold text-slate-800">Welcome back</h1>
      <p className="mb-6 mt-1 text-center text-sm text-slate-500">Sign in to your MIRA Retail account</p>
      <form onSubmit={submit} className="flex flex-col gap-4">
        <div><label htmlFor="username" className="mb-1 block text-sm text-slate-600">Demo customer</label><select id="username" name="username" autoComplete="username" required className="input" disabled={busy}>{demoCustomers.map(customer=><option key={customer.username} value={customer.username}>{customer.name} · {customer.household_size===1?'1 person':`${customer.household_size} people`}{customer.dietary_preference==='none'?'':` · ${customer.dietary_preference}`}</option>)}</select></div>
        <div><label htmlFor="password" className="mb-1 block text-sm text-slate-600">Password</label><input id="password" name="password" type="password" autoComplete="current-password" required maxLength={1000} className="input" placeholder="Enter your password" disabled={busy}/></div>
        <label className="flex items-center gap-2 text-sm text-slate-600"><input name="remember" type="checkbox" className="accent-mira-600" disabled={busy}/>Remember me</label>
        {error && <p role="alert" className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p>}
        <button type="submit" disabled={busy} className="btn-primary w-full disabled:opacity-60">{busy?'Signing in…':'Sign in'}</button>
      </form>
      <p className="mt-5 text-center text-xs leading-5 text-slate-400">Choose a customer and use the shared demo password. No signup required.</p>
    </div>
  </main>
}
