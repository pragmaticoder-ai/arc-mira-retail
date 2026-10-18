import ts from 'typescript'
import {existsSync} from 'node:fs'
import { readFile } from 'node:fs/promises'
import { pathToFileURL, fileURLToPath } from 'node:url'
import { resolve as pathResolve } from 'node:path'
const root=fileURLToPath(new URL('../',import.meta.url))
export async function resolve(specifier,context,next){
  if(specifier==='next/navigation')return {url:new URL('./stubs/navigation.mjs',import.meta.url).href,shortCircuit:true}
  if(specifier==='next/link')return {url:new URL('./stubs/link.mjs',import.meta.url).href,shortCircuit:true}
  if(specifier.startsWith('@/'))return {url:pathToFileURL(pathResolve(root,specifier.slice(2)+(existsSync(pathResolve(root,specifier.slice(2)+'.tsx'))?'.tsx':'.ts'))).href,shortCircuit:true}
  return next(specifier,context)
}
export async function load(url,context,next){
  if((url.endsWith('.tsx') || url.endsWith('.ts'))){
    const source=await readFile(new URL(url),'utf8')
    const output=ts.transpileModule("import React from 'react';\n"+source,{compilerOptions:{jsx:ts.JsxEmit.React,module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText
    return {format:'module',source:output,shortCircuit:true}
  }
  return next(url,context)
}
