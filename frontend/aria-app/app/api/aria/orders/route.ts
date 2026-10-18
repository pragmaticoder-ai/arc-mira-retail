import { requestCustomer } from '@/lib/auth'
import { NextResponse } from 'next/server'
import { getAriaConfig } from '@/lib/config'
import { getAriaHeaders } from '@/lib/upstreamAuth'

export const dynamic = 'force-dynamic'
export async function GET(request: Request) {
  const customer=await requestCustomer(request)
  if(!customer)return NextResponse.json({error_message:"Please sign in."},{status:401})
  const cfg=getAriaConfig()
  const params=new URL(request.url).searchParams
  params.set('customer_id',customer.customer_id)
  try {
    const response=await fetch(`${cfg.ariaAgentUrl}/aria/orders?${params}`,{
      cache:'no-store',signal:AbortSignal.timeout(cfg.requestTimeoutMs),
      headers:await getAriaHeaders(),
    })
    const body=await response.json()
    return NextResponse.json(response.ok?body:{error_message:typeof body.detail==='string'?body.detail:'Unable to load orders'},{status:response.status})
  } catch {
    return NextResponse.json({error_message:'Order history is unavailable. Please retry.'},{status:503})
  }
}
