import { NextRequest, NextResponse } from 'next/server'
import { authConfigured, authRequired, safeNext, sessionCookieName, validSession } from '@/lib/auth'

export async function middleware(request: NextRequest) {
  const path=request.nextUrl.pathname
  if(path==='/login' || path==='/api/auth/login' || path==='/api/auth/logout')return NextResponse.next()
  if(!authRequired())return NextResponse.next()
  if(!authConfigured())return new NextResponse('Sign-in is not configured.',{status:503})
  if(await validSession(request.cookies.get(sessionCookieName())?.value))return NextResponse.next()
  if(path.startsWith('/api/'))return NextResponse.json({error_message:'Please sign in to continue.'},{status:401,headers:{'Cache-Control':'no-store'}})
  const login=new URL('/login',request.url)
  login.searchParams.set('next',safeNext(path+request.nextUrl.search))
  return NextResponse.redirect(login)
}

export const config={matcher:['/((?!_next/static|_next/image|favicon.svg).*)']}
