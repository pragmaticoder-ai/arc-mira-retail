import { NextResponse } from 'next/server'
import { getAriaConfig } from '@/lib/config'

export const dynamic = 'force-dynamic'
export async function GET(request: Request) {
  const cfg = getAriaConfig()
  const params = new URL(request.url).searchParams
  if (!params.has('store_id')) params.set('store_id', cfg.defaultStoreId)
  try {
    const response = await fetch(`${cfg.ariaAgentUrl}/aria/catalog?${params}`, {
      cache: 'no-store', signal: AbortSignal.timeout(cfg.requestTimeoutMs),
      headers: cfg.ariaAgentToken ? { Authorization: `Bearer ${cfg.ariaAgentToken}` } : {},
    })
    const body = await response.json()
    if (!response.ok) return NextResponse.json({ error_message: typeof body.detail === 'string' ? body.detail : 'Invalid catalog filters' }, { status: response.status })
    return NextResponse.json(body)
  } catch {
    return NextResponse.json({ error_message: 'The product catalog is unavailable. Please retry.' }, { status: 503 })
  }
}
