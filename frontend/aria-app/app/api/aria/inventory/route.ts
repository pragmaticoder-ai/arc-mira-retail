import { NextResponse } from 'next/server'
import { getAriaConfig } from '@/lib/config'

export const dynamic = 'force-dynamic'
export async function GET(request: Request) {
  const cfg = getAriaConfig()
  const store = new URL(request.url).searchParams.get('store_id') || cfg.defaultStoreId
  try {
    const response = await fetch(`${cfg.ariaAgentUrl}/aria/inventory?store_id=${encodeURIComponent(store)}`, {
      cache: 'no-store', signal: AbortSignal.timeout(cfg.requestTimeoutMs),
      headers: cfg.ariaAgentToken ? { Authorization: `Bearer ${cfg.ariaAgentToken}` } : {},
    })
    if (!response.ok) throw new Error()
    return NextResponse.json(await response.json())
  } catch {
    return NextResponse.json({ error_message: 'Store inventory is unavailable. Start the backend and retry.' }, { status: 503 })
  }
}
