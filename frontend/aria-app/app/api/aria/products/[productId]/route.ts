import { NextResponse } from 'next/server'
import { getAriaConfig } from '@/lib/config'
import { getAriaHeaders } from '@/lib/upstreamAuth'

export const dynamic = 'force-dynamic'
export async function GET(request: Request, { params }: { params: { productId: string } }) {
  const cfg = getAriaConfig()
  const store = new URL(request.url).searchParams.get('store_id') || cfg.defaultStoreId
  try {
    const response = await fetch(`${cfg.ariaAgentUrl}/aria/products/${encodeURIComponent(params.productId)}?store_id=${encodeURIComponent(store)}`, {
      cache: 'no-store', signal: AbortSignal.timeout(cfg.requestTimeoutMs),
      headers: await getAriaHeaders(),
    })
    if (!response.ok) return NextResponse.json({ error_message: response.status === 404 ? 'Product not found at this store' : 'Product details are unavailable' }, { status: response.status })
    return NextResponse.json(await response.json())
  } catch {
    return NextResponse.json({ error_message: 'Product details are unavailable' }, { status: 503 })
  }
}
