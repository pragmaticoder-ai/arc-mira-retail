'use client'

// app/login/page.tsx — Screen 1: Login / Welcome (SCREENS.md)
// Centered card on slate-50. Logo + "ARIA active" badge carry the brand.
// This is a demo login — submitting goes straight to the store.

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { MiraLogo } from '@/components/MiraLogo'

export default function LoginPage() {
  const router = useRouter()

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 p-md">
      <div className="w-[340px] rounded-lg border border-slate-200 bg-white p-lg shadow-card">
        <div className="mb-lg flex flex-col items-center gap-sm">
          <MiraLogo size="lg" variant="color" showTagline />
          <span className="badge-mira mt-sm">ARIA grocery assistant active</span>
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault()
            router.push('/')
          }}
          className="flex flex-col gap-md"
        >
          <div>
            <label htmlFor="email" className="mb-1 block text-sm text-slate-600">
              Email
            </label>
            <input
              id="email"
              type="email"
              defaultValue="sarah@example.ae"
              className="input"
              autoComplete="email"
            />
          </div>
          <div>
            <label htmlFor="password" className="mb-1 block text-sm text-slate-600">
              Password
            </label>
            <input
              id="password"
              type="password"
              defaultValue="demo"
              className="input"
              autoComplete="current-password"
            />
          </div>

          <div className="flex items-center justify-between text-sm">
            <label className="flex items-center gap-2 text-slate-600">
              <input type="checkbox" className="h-4 w-4 accent-mira-600" defaultChecked />
              Remember me
            </label>
            <a href="#" className="text-mira-600 hover:text-mira-700">
              Forgot password?
            </a>
          </div>

          <button type="submit" className="btn-primary w-full">
            Sign in
          </button>
        </form>

        <p className="mt-md text-center text-sm text-slate-500">
          New to MIRA?{' '}
          <Link href="/" className="text-mira-600 hover:text-mira-700">
            Create an account
          </Link>
        </p>
        <p className="mt-md text-center text-xs text-slate-400">
          By continuing you agree to MIRA Retail’s privacy policy.
        </p>
      </div>
    </main>
  )
}
