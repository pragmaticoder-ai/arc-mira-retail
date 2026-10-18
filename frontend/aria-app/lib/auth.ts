import { findCustomer } from './customers'
/** Shared Web Crypto authentication for the login API and Edge middleware. */
export const SESSION_SECONDS = 8 * 60 * 60
export const REMEMBER_SECONDS = 7 * 24 * 60 * 60
export const sessionCookieName = () => process.env.K_SERVICE ? '__Host-mira_session' : 'mira_session'
export const authRequired = () => Boolean(process.env.K_SERVICE || process.env.DEMO_PASSWORD)
export const authConfigured = () => Boolean(process.env.DEMO_USERNAME && process.env.DEMO_PASSWORD)

const encoder = new TextEncoder()
function encode(bytes: Uint8Array): string {
  return btoa(String.fromCharCode(...bytes)).replaceAll('+','-').replaceAll('/','_').replace(/=+$/,'')
}
function decode(value: string): Uint8Array {
  const input=value.replaceAll('-','+').replaceAll('_','/')
  return Uint8Array.from(atob(input.padEnd(Math.ceil(input.length/4)*4,'=')),c=>c.charCodeAt(0))
}
async function key() {
  if(!authConfigured())throw new Error('Sign-in is not configured')
  return crypto.subtle.importKey('raw',encoder.encode('mira-session-v1:'+process.env.DEMO_PASSWORD),{name:'HMAC',hash:'SHA-256'},false,['sign','verify'])
}
export async function checkCredentials(username: string,password: string): Promise<boolean> {
  if(!authConfigured())return false
  const digest=async(value:string)=>new Uint8Array(await crypto.subtle.digest('SHA-256',encoder.encode(value)))
  const [actual,expected]=await Promise.all([digest(`${username.trim()}:${password}`),digest(`${findCustomer(username)?.username || process.env.DEMO_USERNAME}:${process.env.DEMO_PASSWORD}`)])
  let mismatch=0
  for(let i=0;i<actual.length;i++)mismatch|=actual[i]^expected[i]
  return Boolean(findCustomer(username)) && mismatch===0
}
export async function createSession(seconds=SESSION_SECONDS,now=Date.now(),username=process.env.DEMO_USERNAME || ''): Promise<string> {
  const customer=findCustomer(username)
  if(!customer)throw new Error('Unknown customer')
  const body=encode(encoder.encode(JSON.stringify({user:customer.username,customer_id:customer.customer_id,exp:Math.floor(now/1000)+seconds,nonce:crypto.randomUUID()})))
  const signature=await crypto.subtle.sign('HMAC',await key(),encoder.encode(body))
  return `${body}.${encode(new Uint8Array(signature))}`
}
export async function sessionCustomer(token: string|undefined,now=Date.now()) {
  if(!token || token.length>4096 || !authConfigured())return null
  try {
    const parts=token.split('.')
    if(parts.length!==2 || !await crypto.subtle.verify('HMAC',await key(),decode(parts[1]),encoder.encode(parts[0])))return null
    const data=JSON.parse(new TextDecoder().decode(decode(parts[0])))
    const customer=typeof data.user==='string'?findCustomer(data.user):undefined
    return customer && data.customer_id===customer.customer_id && Number.isInteger(data.exp) && data.exp>Math.floor(now/1000)?customer:null
  } catch { return null }
}
export async function validSession(token: string|undefined,now=Date.now()): Promise<boolean> {
  return Boolean(await sessionCustomer(token,now))
}
export async function requestCustomer(request: Request) {
  if(!authRequired())return findCustomer(process.env.DEMO_USERNAME || 'mira-demo')!
  const cookie=(request.headers.get('cookie') || '').split(';').map(p=>p.trim()).find(p=>p.startsWith(sessionCookieName()+'='))
  return sessionCustomer(cookie?.slice(sessionCookieName().length+1))
}
export function safeNext(value: unknown): string {
  if(typeof value!=='string')return '/'
  try {
    const decoded=decodeURIComponent(value)
    if(!decoded.startsWith('/') || decoded.startsWith('//') || /[\\\x00-\x1f]/.test(decoded) || decoded.split('?')[0].startsWith('/login') || decoded.startsWith('/api/'))return '/'
    return value
  } catch {return '/'}
}

export function sameOrigin(request: Request): boolean {
  const origin=request.headers.get('origin')
  try {return !origin || new URL(origin).host===request.headers.get('host')} catch {return false}
}
