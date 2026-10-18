import { requestCustomer } from '@/lib/auth'
import { NextResponse } from 'next/server'
import { getAriaConfig } from '@/lib/config'
import { getAriaHeaders } from '@/lib/upstreamAuth'

export const dynamic = 'force-dynamic'
export async function GET(request: Request) {
  const customer=await requestCustomer(request)
  if(!customer)return NextResponse.json({error_message:"Please sign in."},{status:401})
  const cfg = getAriaConfig()
  try {
    const response = await fetch(`${cfg.ariaAgentUrl}/aria/bootstrap?customer_id=${encodeURIComponent(customer.customer_id)}`, {
      cache: 'no-store', signal: AbortSignal.timeout(cfg.requestTimeoutMs),
      headers: await getAriaHeaders(),
    })
    if (!response.ok) throw new Error()
    return NextResponse.json(await response.json())
  } catch {
    return NextResponse.json({ error_message: 'Store setup is unavailable. Check the backend and database connection.' }, { status: 503 })
  }
}
