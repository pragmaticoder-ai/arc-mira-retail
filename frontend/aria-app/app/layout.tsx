import type { Metadata } from 'next'
import './globals.css'
import { CartProvider } from '@/context/CartContext'

export const metadata: Metadata = {
  title: 'MIRA Retail — ARIA grocery assistant',
  description:
    'AI-native grocery shopping with ARIA, MIRA Retail’s customer experience agent.',
  icons: {
    icon: '/favicon.svg',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="bg-slate-50 text-slate-800 antialiased">
        <CartProvider>{children}</CartProvider>
      </body>
    </html>
  )
}
