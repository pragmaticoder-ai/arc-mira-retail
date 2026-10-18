import assert from 'node:assert/strict'
import { test } from 'node:test'
import { JSDOM } from 'jsdom'
import React, { act } from 'react'
import { createRoot } from 'react-dom/client'
import { CategorySidebar } from '../components/CategorySidebar.tsx'
import { NavBar } from '../components/NavBar.tsx'
import { ProductCard } from '../components/ProductCard.tsx'
import { CartProvider } from '../context/CartContext.tsx'

const dom=new JSDOM('<div id="root"></div>',{url:'http://localhost/'})
Object.assign(globalThis,{window:dom.window,document:dom.window.document,sessionStorage:dom.window.sessionStorage,IS_REACT_ACT_ENVIRONMENT:true})
const root=createRoot(document.getElementById('root'))
const customer={customer_id:'demo_ahmed',name:'Ahmed',username:'ahmed-demo',initials:'A'}
globalThis.fetch=async()=>({ok:true,json:async()=>({customer})})
const click=async element=>{assert.ok(element);await act(async()=>element.dispatchEvent(new dom.window.MouseEvent('click',{bubbles:true})))}
const button=text=>[...document.querySelectorAll('button')].find(b=>b.textContent.includes(text))

test('category selection, dietary and stock toggles, facet search selection and clear filters work',async()=>{
 const calls=[]
 const props={active:'all',halalOnly:false,maxBudget:0,inStock:false,attributes:{},facets:{brand:[{value:'Daawat',count:3}]}}
 for(const key of ['onSelect','onHalalToggle','onBudgetChange','onAttributes','onInStock'])props[key]=value=>calls.push([key,value])
 await act(async()=>root.render(React.createElement(CategorySidebar,props)))
 await click(button('All groceries'))
 await click([...document.querySelectorAll('input')].find(i=>i.parentElement.textContent.includes('In stock only')))
 await click([...document.querySelectorAll('input')].find(i=>i.parentElement.textContent.includes('Halal meat only')))
 await click([...document.querySelectorAll('input')].find(i=>i.parentElement.textContent.includes('Daawat')))
 assert.ok(calls.some(([k,v])=>k==='onSelect'&&v==='all'))
 assert.ok(calls.some(([k,v])=>k==='onInStock'&&v===true))
 assert.ok(calls.some(([k,v])=>k==='onHalalToggle'&&v===true))
 assert.ok(calls.some(([k,v])=>k==='onAttributes'&&v.brand[0]==='Daawat'))
 await click(button('Clear filters'))
 assert.deepEqual(calls.slice(-4),[['onAttributes',{}],['onHalalToggle',false],['onInStock',false],['onBudgetChange',0]])
})
test('navigation exposes working cart/orders destinations, offers callback and avatar menu',async()=>{
 let offers=false
 await act(async()=>root.render(React.createElement(CartProvider,null,React.createElement(NavBar,{search:'',onSearch:()=>{},offersOnly:false,onOffers:v=>offers=v,stores:[{store_id:'dubai_marina_01',store_name:'MIRA Marina'}],storeId:'dubai_marina_01',onStoreChange:()=>{}}))))
 assert.equal(document.querySelector('a[aria-label^="Cart"]').getAttribute('href'),'/cart?store_id=dubai_marina_01')
 assert.ok(document.querySelector('a[href="/orders"]'))
 await click(button('Offers'));assert.equal(offers,true)
 await click(document.querySelector('button[aria-haspopup="menu"]'))
 assert.ok(button('Sign out'));assert.ok(button('Switch customer'))
 assert.ok(document.body.textContent.includes('Ahmed'))
 await act(async()=>document.dispatchEvent(new dom.window.KeyboardEvent('keydown',{key:'Escape',bubbles:true})))
 assert.equal(document.querySelector('[role="menu"]'),null)
})
test('product details links and add buttons target the real product; unavailable items cannot be added',async()=>{
 let added=null
 const product={product_id:'rice',store_id:'dubai_marina_01',product_name:'Basmati rice',category:'grains',price_aed:20,stock_quantity:3,dietary_flags:'',attributes:{},images:[]}
 await act(async()=>root.render(React.createElement(ProductCard,{product,added:false,onAdd:id=>added=id})))
 assert.match(document.querySelector('a').getAttribute('href'),/^\/products\/rice\?store_id=/)
 await click(button('Add'));assert.equal(added,'rice')
 await act(async()=>root.render(React.createElement(ProductCard,{product:{...product,stock_quantity:0},added:false,onAdd:()=>{throw Error('unavailable clicked')}})))
 assert.equal(document.querySelector('button').disabled,true)
})

test('product pagination, sort, page size and offers request the selected catalog page',async()=>{
 const {ProductGrid}=await import('../components/ProductGrid.tsx')
 const requests=[]
 globalThis.fetch=async url=>{
  if(url==='/api/auth/session')return {ok:true,json:async()=>({customer})}
  requests.push(String(url))
  return {ok:true,json:async()=>({items:[{product_id:'test-rice',store_id:'dubai_marina_01',product_name:'Rice',category:'grains',price_aed:10,stock_quantity:5,attributes:{},dietary_flags:''}],total:50,total_pages:3,facets:{}})}
 }
 const props={category:'all',halalOnly:false,maxBudget:0,storeId:'dubai_marina_01',search:'',attributes:{},inStock:false,onFacets:()=>{},offersOnly:false}
 await act(async()=>root.render(React.createElement(CartProvider,null,React.createElement(ProductGrid,props))))
 await click(button('Next'))
 assert.equal(new URL(requests.at(-1),'http://localhost').searchParams.get('page'),'2')
 await click(button('Previous'))
 assert.equal(new URL(requests.at(-1),'http://localhost').searchParams.get('page'),'1')
 const sort=document.querySelector('select[aria-label="Sort products"]')
 await act(async()=>{sort.value='price_desc';sort.dispatchEvent(new dom.window.Event('change',{bubbles:true}))})
 assert.equal(new URL(requests.at(-1),'http://localhost').searchParams.get('sort'),'price_desc')
 const size=document.querySelector('select[aria-label="Products per page"]')
 await act(async()=>{size.value='48';size.dispatchEvent(new dom.window.Event('change',{bubbles:true}))})
 assert.equal(new URL(requests.at(-1),'http://localhost').searchParams.get('page_size'),'48')
 await act(async()=>root.render(React.createElement(CartProvider,null,React.createElement(ProductGrid,{...props,offersOnly:true}))))
 assert.equal(new URL(requests.at(-1),'http://localhost').searchParams.get('offers_only'),'true')
})

test('order history refresh and pagination load the correct page',async()=>{
 const {default:Orders}=await import('../app/orders/page.tsx')
 const requests=[]
 globalThis.fetch=async url=>{
  requests.push(String(url))
  if(url==='/api/auth/session')return {ok:true,json:async()=>({customer})}
  if(url==='/api/aria/bootstrap')return {ok:true,json:async()=>({stores:[]})}
  return {ok:true,json:async()=>({items:[{order_id:'MR-TEST',created_at:new Date().toISOString(),store_id:'dubai_marina_01',status:'confirmed',items:[],total_aed:25}],total:25,total_pages:2})}
 }
 await act(async()=>root.render(React.createElement(CartProvider,null,React.createElement(Orders))))
 await click(button('Next'));assert.equal(requests.at(-1),'/api/aria/orders?page=2')
 await click(button('Previous'));assert.equal(requests.at(-1),'/api/aria/orders?page=1')
 const before=requests.length;await click(button('Refresh'));assert.ok(requests.length>before)
 assert.ok(document.body.textContent.includes('MR-TEST'))
})

test('basket quantity controls, remove and explicit review/confirm invoke real chat contract',async()=>{
 const {default:Cart}=await import('../app/cart/page.tsx')
 await act(async()=>root.render(null))
 const product={product_id:'milk',product_name:'Milk',store_id:'dubai_marina_01',price_aed:12,stock_quantity:3,attributes:{},dietary_flags:''}
 const item={...product,quantity:1,aisle_ref:'A1',in_stock:true,substituted:false,discount_active:false}
 sessionStorage.setItem('arc-checkout-demo_ahmed',JSON.stringify({items:[item],catalog:[product]}))
 const requests=[]
 globalThis.fetch=async(url,options)=>{
  if(url==='/api/auth/session')return {ok:true,json:async()=>({customer})}
  if(url==='/api/aria/bootstrap')return {ok:true,json:async()=>({customer,stores:[{store_id:'dubai_marina_01',store_name:'MIRA Marina'}],default_store_id:'dubai_marina_01'})}
  if(String(url).startsWith('/api/aria/products/'))return {ok:true,json:async()=>product}
  if(url==='/api/aria/chat'){
   const body=JSON.parse(options.body);requests.push(body)
   return {ok:true,json:async()=>({session_id:body.session_id,reply:'Review your basket',cart:{items:body.cart,total_aed:12,promotion:null},quote_id:'verified-quote',cart_changed:true,order:body.message==='confirm'?{order_id:'MR-UI-TEST',total_aed:12}:null})}
  }
  throw Error('Unexpected request '+url)
 }
 await act(async()=>root.render(React.createElement(CartProvider,null,React.createElement(Cart))))
 await click(document.querySelector('button[aria-label="Increase Milk"]'))
 assert.equal(document.querySelector('[aria-label="Quantity of Milk"]').textContent,'2')
 await click(document.querySelector('button[aria-label="Decrease Milk"]'))
 assert.equal(document.querySelector('[aria-label="Quantity of Milk"]').textContent,'1')
 await click(button('Review updated basket'))
 assert.equal(requests.at(-1).message,'review cart')
 await click(button('Confirm order'))
 assert.equal(requests.at(-1).message,'confirm')
 assert.equal(requests.at(-1).quote_id,'verified-quote')
 await click([...document.querySelectorAll('button')].find(b=>b.textContent==='Remove'))
 assert.ok(document.body.textContent.includes('Your basket is empty'))
})
