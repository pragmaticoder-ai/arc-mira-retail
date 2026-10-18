import Link from 'next/link'
import { MiraLogo } from '@/components/MiraLogo'

export default function LoginPage() {
  return <main className="flex min-h-screen items-center justify-center p-6"><div className="max-w-sm rounded-lg border bg-white p-8 text-center"><MiraLogo size="lg" variant="color" showTagline/><h1 className="mt-6 text-xl font-medium">Welcome to MIRA</h1><p className="mt-3 text-sm text-slate-600">Hosted demo access uses the username and password supplied by the project owner.</p><Link href="/" className="btn-primary mt-6 block">Open the store</Link></div></main>
}
