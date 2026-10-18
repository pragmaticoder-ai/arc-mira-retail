import { NextResponse } from 'next/server'
import { getAriaConfig } from '@/lib/config'

export const dynamic = 'force-dynamic'

export async function POST(request: Request) {
  const cfg = getAriaConfig()
  let body: Record<string, unknown>
  try {
    const parsed = await request.json()
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) throw new Error()
    body = parsed
  } catch {
    return NextResponse.json({ error_message: 'Invalid JSON body' }, { status: 400 })
  }
  if (typeof body.message !== 'string' || !body.message.trim()) {
    return NextResponse.json({ error_message: 'message is required' }, { status: 400 })
  }
  try {
    const upstream = await fetch(`${cfg.ariaAgentUrl}/aria/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...(cfg.ariaAgentToken ? { Authorization: `Bearer ${cfg.ariaAgentToken}` } : {}) },
      body: JSON.stringify({ ...body, customer_id: body.customer_id ?? cfg.defaultCustomerId, store_id: body.store_id ?? cfg.defaultStoreId }),
      signal: AbortSignal.timeout(cfg.requestTimeoutMs),
      cache: 'no-store',
    })
    const data = await upstream.json()
    if (!upstream.ok) {
      return NextResponse.json({ error_message: typeof data.detail === 'string' ? data.detail : 'The request could not be validated. Please review your basket.' }, { status: upstream.status })
    }
    if (typeof data.reply !== 'string' || !Array.isArray(data.cart?.items)) throw new Error('Invalid backend response')
    return NextResponse.json(data)
  } catch {
    return NextResponse.json({ error_message: 'ARIA is unavailable. Check that the local backend is running, then retry.' }, { status: 503 })
  }
}
