import { NextResponse } from 'next/server'
import { requestCustomer } from '@/lib/auth'
export const dynamic='force-dynamic'
export async function GET(request: Request) {
  const customer=await requestCustomer(request)
  return NextResponse.json(customer?{customer}:{error_message:'Please sign in to continue.'},{status:customer?200:401,headers:{'Cache-Control':'no-store'}})
}
