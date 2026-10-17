'use client'

// components/ReasoningDrawer.tsx
// Expandable "How did ARIA decide this?" panel showing the ReAct chain.
// THOUGHT / ACTION / OBSERVATION styling comes from globals.css
// (.reasoning-step + modifier classes).

import { useState } from 'react'
import type { ReasoningStep } from '@/lib/types'

const STEP_CLASS: Record<ReasoningStep['type'], string> = {
  THOUGHT: 'reasoning-step reasoning-step-thought',
  ACTION: 'reasoning-step reasoning-step-action',
  OBSERVATION: 'reasoning-step reasoning-step-observe',
}

export function ReasoningDrawer({ steps }: { steps: ReasoningStep[] }) {
  const [open, setOpen] = useState(false)
  if (!steps || steps.length === 0) return null

  return (
    <div className="mt-sm">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="flex items-center gap-1 text-xs font-medium text-mira-600 hover:text-mira-700"
      >
        <span aria-hidden="true">{open ? '▾' : '▸'}</span>
        How did ARIA decide this? ({steps.length} steps)
      </button>
      {open && (
        <div className="mt-sm flex flex-col gap-1 rounded-md bg-slate-50 p-sm">
          {steps.map((s, i) => (
            <div key={i} className={STEP_CLASS[s.type]}>
              <span className="font-medium">{s.type}</span>
              <span className="flex-1">{s.text}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
