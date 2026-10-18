import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { test } from 'node:test'
import ts from 'typescript'

const accounts=JSON.parse(await readFile(new URL('../lib/demoCustomers.json',import.meta.url),'utf8'))
let customers=await readFile(new URL('../lib/customers.ts',import.meta.url),'utf8')
customers=customers.replace("import accounts from './demoCustomers.json'",'const accounts='+JSON.stringify(accounts))
const customerModule=ts.transpileModule(customers,{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText
const customerUrl='data:text/javascript;base64,'+Buffer.from(customerModule).toString('base64')
let source=await readFile(new URL('../lib/auth.ts',import.meta.url),'utf8')
source=source.replace("'./customers'",JSON.stringify(customerUrl))
const {outputText}=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}})
const auth=await import('data:text/javascript;base64,'+Buffer.from(outputText).toString('base64'))
process.env.DEMO_USERNAME='test-demo'
process.env.DEMO_PASSWORD='temporary-test-secret'

test('correct credentials only; unicode invalid input is rejected safely',async()=>{
  assert.equal(await auth.checkCredentials('test-demo','temporary-test-secret'),true)
  assert.equal(await auth.checkCredentials('test-demo','wrong'),false)
  assert.equal(await auth.checkCredentials('wrong','temporary-test-secret'),false)
  assert.equal(await auth.checkCredentials('测试','wrong'),false)
})
test('signed session expires and forged or malformed tokens are rejected',async()=>{
  const now=1000000
  const token=await auth.createSession(60,now)
  assert.equal(await auth.validSession(token,now),true)
  assert.equal(await auth.validSession(token,now+60000),false)
  const [body,sig]=token.split('.')
  const payload=JSON.parse(Buffer.from(body,'base64url').toString())
  payload.exp+=1000000
  assert.equal(await auth.validSession(Buffer.from(JSON.stringify(payload)).toString('base64url')+'.'+sig,now),false)
  for(const value of [undefined,'invalid',token+'.extra','%%%%.%%%','x'.repeat(5000)])assert.equal(await auth.validSession(value,now),false)
})
test('password rotation invalidates previous sessions',async()=>{
  const token=await auth.createSession()
  process.env.DEMO_PASSWORD='replacement-test-secret'
  assert.equal(await auth.validSession(token),false)
  process.env.DEMO_PASSWORD='temporary-test-secret'
})
test('return paths cannot redirect outside the app or into an authentication loop',()=>{
  for(const value of ['https://example.com','//example.com','/\\example.com','/%2f%2fexample.com','/%5cexample.com','/login','/api/auth/login','/%00',null])assert.equal(auth.safeNext(value),'/')
  assert.equal(auth.safeNext('/cart?store_id=dubai_marina_01'),'/cart?store_id=dubai_marina_01')
})
test('cross-origin sign-in and sign-out are rejected',()=>{
  assert.equal(auth.sameOrigin(new Request('https://mira.example/api/auth/login',{headers:{host:'mira.example',origin:'https://evil.example'}})),false)
  assert.equal(auth.sameOrigin(new Request('https://mira.example/api/auth/login',{headers:{host:'mira.example',origin:'https://mira.example'}})),true)
})

test('each signed customer is bound to their own identity',async()=>{
  for(const account of accounts){
    assert.equal(await auth.checkCredentials(account.username,'temporary-test-secret'),true)
    const token=await auth.createSession(60,Date.now(),account.username)
    assert.equal((await auth.sessionCustomer(token)).customer_id,account.customer_id)
    const request=new Request('https://mira.example/api/auth/session',{headers:{cookie:auth.sessionCookieName()+'='+token}})
    assert.equal((await auth.requestCustomer(request)).customer_id,account.customer_id)
  }
})
