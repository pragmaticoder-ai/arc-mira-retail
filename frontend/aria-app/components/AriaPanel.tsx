'use client'

// components/AriaPanel.tsx
// The ARIA chat panel (white, 340px) per BRAND.md/SCREENS.md:
//   mira-600 header · chat thread (aria/user bubbles) · reasoning drawer
//   · thinking state · live cart preview · text input.
// Calls POST /api/aria/chat (the contract endpoint) for every message.

import { useCallback, useRef, useState } from 'react'
import { useRouter } from 'next/navigation'
import { CartPreview } from '@/components/CartPreview'
import { ReasoningDrawer } from '@/components/ReasoningDrawer'
import { useCart } from '@/context/CartContext'
import type { AriaChatResponse, ChatMessage, DemandSignal, SubstitutionOffer } from '@/lib/types'

const SUGGESTED = 'Weekly halal groceries, family of 4, AED 300. Include brown rice.'

interface AriaPanelProps {
  storeId: string
  customerId: string
}

export function AriaPanel({ storeId, customerId }: AriaPanelProps) {
  const router = useRouter()
  const { setCart, setOrder, items, quoteId } = useCart()
  const [signals, setSignals] = useState<DemandSignal[]>([])
  const [offers, setOffers] = useState<SubstitutionOffer[]>([])
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'greeting',
      role: 'aria',
      text: 'Hi, I’m ARIA. Tell me what you need and I’ll build your cart — within your budget and dietary preferences.',
    },
  ])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const [confirming, setConfirming] = useState(false)
  const sessionId = useRef<string>(crypto.randomUUID())

  const send = useCallback(
    async (text: string, feedback?: 'satisfied' | 'compromise' | 'rejected', productId?: string) => {
      const trimmed = text.trim()
      if (!trimmed || busy) return
      setBusy(true)
      setConfirming(['confirm', 'confirm order', 'review cart', 'yes', 'place order', 'go ahead', 'proceed'].includes(trimmed.toLowerCase()) && !feedback)
      setInput('')

      const userMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'user',
        text: trimmed,
      }
      const thinkingMsg: ChatMessage = {
        id: 'thinking',
        role: 'aria',
        text: 'ARIA is thinking…',
        thinking: true,
      }
      setMessages((prev) => [...prev, userMsg, thinkingMsg])

      try {
        const res = await fetch('/api/aria/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            session_id: sessionId.current,
            customer_id: customerId,
            store_id: storeId,
            message: trimmed,
            feedback, product_id: productId,
            ...(['confirm', 'confirm order', 'review cart', 'yes', 'place order', 'go ahead', 'proceed'].includes(trimmed.toLowerCase()) || feedback ? { cart: items, quote_id: quoteId } : {}),
          }),
        })
        const raw = await res.json()
        if (!res.ok) throw new Error(raw.error_message || 'Unable to process your request')
        const data = raw as AriaChatResponse
        if (typeof data.reply !== 'string' || !Array.isArray(data.cart?.items)) throw new Error('ARIA returned an invalid response')
        sessionId.current = data.session_id
        setSignals(data.demand_signals || [])
        setOffers(data.substitution_offers || [])

        if (data.cart_changed !== false) setCart({ ...data.cart, quote_id: data.quote_id })
        if (data.order) {
          setOrder(data.order)
          setTimeout(() => router.push('/order/confirmed'), 900)
        }

        setMessages((prev) =>
          prev
            .filter((m) => m.id !== 'thinking')
            .concat({
              id: crypto.randomUUID(),
              role: 'aria',
              text: data.reply,
              reasoning: data.reasoning,
            }),
        )
      } catch (err) {
        setMessages((prev) =>
          prev
            .filter((m) => m.id !== 'thinking')
            .concat({
              id: crypto.randomUUID(),
              role: 'aria',
              text: err instanceof Error ? err.message : 'There was an issue reaching ARIA. Please try again.',
            }),
        )
      } finally {
        setBusy(false)
        setConfirming(false)
      }
    },
    [busy, customerId, storeId, setCart, setOrder, router, items, quoteId],
  )

  return (
    <aside className="flex min-h-[600px] md:min-h-0 w-full md:w-[360px] shrink-0 flex-col border-l border-slate-200 bg-white">
      {/* Header */}
      <div className="bg-mira-600 px-md py-3 text-white">
        <p className="text-sm font-medium">ARIA — grocery assistant</p>
        <p className="text-xs text-mira-100">Shopping advice · shared store inventory</p>
      </div>

      {/* Chat thread */}
      <div className="flex flex-1 flex-col gap-md overflow-y-auto p-md">
        {messages.map((m) =>
          m.thinking ? (
            <div
              key={m.id}
              className="self-start rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-700"
            >
              <span className="mr-1 inline-block animate-pulse">●</span>
              {m.text}
            </div>
          ) : (
            <div
              key={m.id}
              className={m.role === 'aria' ? 'self-start' : 'self-end'}
            >
              <div className={m.role === 'aria' ? 'bubble-aria' : 'bubble-user'}>
                {m.text}
              </div>
              {m.role === 'aria' && m.reasoning && (
                <ReasoningDrawer steps={m.reasoning} />
              )}
            </div>
          ),
        )}

        {messages.length === 1 && (
          <button
            type="button"
            onClick={() => send(SUGGESTED)}
            className="btn-secondary self-start text-xs"
          >
            Try: “{SUGGESTED}”
          </button>
        )}
      </div>

      {/* Live cart */}
      {offers.length > 0 && <div className="max-h-52 overflow-y-auto border-t border-slate-200 p-md text-sm">
        {offers.map((offer) => <div key={offer.product_id} className="mb-sm">
          <p className="font-medium text-slate-700">{offer.product_name}</p>
          <p className="text-xs text-slate-500">{offer.substitute_name ? `Alternative: ${offer.substitute_name}` : 'No suitable alternative'}</p>
          <div className="mt-2 flex flex-wrap gap-1">
            {offer.substitute_product_id && <>
              <button className="rounded border px-2 py-1 text-xs" disabled={busy} onClick={() => send('This alternative meets my needs.', 'satisfied', offer.product_id)}>Meets my needs</button>
              <button className="rounded border border-amber-300 px-2 py-1 text-xs" disabled={busy} onClick={() => send('Okay this time; I still prefer the original.', 'compromise', offer.product_id)}>Temporary compromise</button>
            </>}
            <button className="rounded border px-2 py-1 text-xs" disabled={busy} onClick={() => send('No thanks, I want the original product.', 'rejected', offer.product_id)}>Decline</button>
          </div>
        </div>)}
        {signals.filter((s) => s.outcome !== 'fulfilled').map((s) => <p key={s.product_id} className="mt-1 text-xs text-mira-700">Recorded: {s.outcome === 'unknown' ? 'awaiting your feedback' : s.outcome} · {s.product_name}</p>)}
      </div>}
      <CartPreview onConfirm={() => send('confirm')} busy={busy} confirming={confirming} />

      {/* Input row */}
      <form
        onSubmit={(e) => {
          e.preventDefault()
          send(input)
        }}
        className="flex items-center gap-sm border-t border-slate-200 p-md"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Message ARIA…"
          aria-label="Message ARIA"
          className="input flex-1"
          disabled={busy}
        />
        <button type="submit" disabled={busy || !input.trim()} className="btn-primary">
          Send
        </button>
      </form>
    </aside>
  )
}
