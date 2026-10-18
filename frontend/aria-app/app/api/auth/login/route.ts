import { NextResponse } from 'next/server'
import { authConfigured, authRequired, checkCredentials, createSession, REMEMBER_SECONDS, safeNext, sameOrigin, SESSION_SECONDS, sessionCookieName } from '@/lib/auth'

export const dynamic='force-dynamic'
export async function POST(request: Request) {
  const headers={'Cache-Control':'no-store'}
  if(!sameOrigin(request))return NextResponse.json({error_message:'Please sign in from the MIRA login page.'},{status:403,headers})
  if(!authConfigured()) {
    if(authRequired())return NextResponse.json({error_message:'Sign-in is unavailable. Please contact the demo owner.'},{status:503,headers})
    return NextResponse.json({redirect:'/'},{headers})
  }
  let body
  try {
    const text=await request.text()
    if(text.length>4096)throw new Error()
    body=JSON.parse(text)
    if(typeof body.username!=='string' || typeof body.password!=='string')throw new Error()
  } catch {return NextResponse.json({error_message:'Enter your username and password.'},{status:400,headers})}
  if(!await checkCredentials(body.username,body.password))return NextResponse.json({error_message:'Incorrect username or password.'},{status:401,headers})
  const seconds=body.remember===true?REMEMBER_SECONDS:SESSION_SECONDS
  const response=NextResponse.json({redirect:safeNext(body.next)},{headers})
  response.cookies.set(sessionCookieName(),await createSession(seconds,Date.now(),body.username),{httpOnly:true,secure:Boolean(process.env.K_SERVICE)||new URL(request.url).protocol==='https:',sameSite:'lax',path:'/',...(body.remember===true?{maxAge:seconds}:{})})
  return response
}
