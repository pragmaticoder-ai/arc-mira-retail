import { NextResponse } from 'next/server'
import { sameOrigin, sessionCookieName } from '@/lib/auth'

export async function POST(request: Request) {
  if(!sameOrigin(request))return NextResponse.json({error_message:'Invalid sign-out request.'},{status:403})
  const response=NextResponse.json({redirect:'/login'},{headers:{'Cache-Control':'no-store'}})
  response.cookies.set(sessionCookieName(),'',{httpOnly:true,secure:Boolean(process.env.K_SERVICE)||new URL(request.url).protocol==='https:',sameSite:'lax',path:'/',maxAge:0})
  return response
}
