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
import type { AriaChatResponse, ChatMessage } from '@/lib/types'

const SUGGESTED = 'Weekly groceries, family of 4, halal, AED 300'

interface AriaPanelProps {
  storeId: string
  customerId: string
}

export function AriaPanel({ storeId, customerId }: AriaPanelProps) {
  const router = useRouter()
  const { setCart, setOrder } = useCart()
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'greeting',
      role: 'aria',
      text: 'Hi, I’m ARIA. Tell me what you need and I’ll build your cart — within your budget and dietary preferences.',
    },
  ])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const sessionId = useRef<string>(crypto.randomUUID())

  const send = useCallback(
    async (text: string) => {
      const trimmed = text.trim()
      if (!trimmed || busy) return
      setBusy(true)
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
          }),
        })
        const data = (await res.json()) as AriaChatResponse

        if (data.cart && data.cart.items.length > 0) setCart(data.cart)
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
      } catch {
        setMessages((prev) =>
          prev
            .filter((m) => m.id !== 'thinking')
            .concat({
              id: crypto.randomUUID(),
              role: 'aria',
              text: 'There was a brief issue reaching me. Please try again.',
            }),
        )
      } finally {
        setBusy(false)
      }
    },
    [busy, customerId, storeId, setCart, setOrder, router],
  )

  return (
    <aside className="flex w-[340px] shrink-0 flex-col border-l border-slate-200 bg-white">
      {/* Header */}
      <div className="bg-mira-600 px-md py-3 text-white">
        <p className="text-sm font-medium">ARIA — grocery assistant</p>
        <p className="text-xs text-mira-100">Session active · Dubai Marina</p>
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
      <CartPreview onConfirm={() => send('confirm')} confirming={busy} />

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
