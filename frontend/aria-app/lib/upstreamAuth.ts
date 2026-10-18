import { getAriaConfig } from '@/lib/config'

let cached: {token:string; expires:number}|null=null
export async function getAriaHeaders(): Promise<Record<string,string>> {
  const cfg=getAriaConfig()
  if(cfg.ariaAgentToken)return {Authorization:`Bearer ${cfg.ariaAgentToken}`}
  if(!process.env.K_SERVICE)return {}
  if(!cached || Date.now()>=cached.expires) {
    const url=new URL('http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/identity')
    url.searchParams.set('audience',cfg.ariaAgentUrl)
    url.searchParams.set('format','full')
    const response=await fetch(url,{headers:{'Metadata-Flavor':'Google'},cache:'no-store',signal:AbortSignal.timeout(10000)})
    if(!response.ok)throw new Error('Unable to authenticate to ARIA')
    cached={token:await response.text(),expires:Date.now()+45*60*1000}
  }
  return {Authorization:`Bearer ${cached.token}`}
}
