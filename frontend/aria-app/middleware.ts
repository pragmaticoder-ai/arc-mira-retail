import { NextRequest, NextResponse } from 'next/server'

// A shared demo account protects the hosted prototype. Runtime service-account
// identity is separate and never sent to the browser.
export async function middleware(request: NextRequest) {
  const username=process.env.DEMO_USERNAME
  const password=process.env.DEMO_PASSWORD
  if(!username || !password) {
    if(process.env.K_SERVICE) return new NextResponse('Demo access is not configured.',{status:503})
    return NextResponse.next()
  }
  const provided=request.headers.get('authorization') || ''
  let credentials=''
  try { if(provided.startsWith('Basic '))credentials=atob(provided.slice(6)) } catch { /* Reject malformed credentials. */ }
  const digest=async(value:string)=>new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(value)))
  const [actual,expected]=await Promise.all([digest(credentials),digest(`${username}:${password}`)])
  let difference=0
  for(let i=0;i<actual.length;i++)difference|=actual[i]^expected[i]
  if(difference!==0)return new NextResponse('Sign in with your MIRA demo credentials.',{status:401,headers:{'WWW-Authenticate':'Basic realm="MIRA ARIA", charset="UTF-8"','Cache-Control':'no-store'}})
  return NextResponse.next()
}

export const config={matcher:['/((?!favicon.svg).*)']}
