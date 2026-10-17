'use client'

// components/CategorySidebar.tsx
// Left sidebar (slate-100) per BRAND.md: 8 grocery categories with emoji,
// active state in mira tint, halal filter toggle, budget slider.

import { CATEGORY_META } from '@/lib/mockProducts'
import type { Category } from '@/lib/types'

interface CategorySidebarProps {
  active: Category | 'all'
  onSelect: (c: Category | 'all') => void
  halalOnly: boolean
  onHalalToggle: (v: boolean) => void
  maxBudget: number
  onBudgetChange: (v: number) => void
}

export function CategorySidebar({
  active,
  onSelect,
  halalOnly,
  onHalalToggle,
  maxBudget,
  onBudgetChange,
}: CategorySidebarProps) {
  return (
    <aside className="flex w-[200px] shrink-0 flex-col gap-lg overflow-y-auto border-r border-slate-200 bg-slate-100 p-md">
      <div>
        <h2 className="mb-sm text-xs font-medium uppercase tracking-wide text-slate-400">
          Categories
        </h2>
        <ul className="flex flex-col gap-0.5">
          <li>
            <button
              type="button"
              onClick={() => onSelect('all')}
              className={`flex w-full items-center gap-2 rounded px-2 py-1.5 text-left text-sm ${
                active === 'all'
                  ? 'bg-mira-50 font-medium text-mira-600'
                  : 'text-slate-600 hover:bg-slate-200'
              }`}
            >
              <span aria-hidden="true">🛍️</span> All items
            </button>
          </li>
          {CATEGORY_META.map((c) => (
            <li key={c.id}>
              <button
                type="button"
                onClick={() => onSelect(c.id)}
                className={`flex w-full items-center gap-2 rounded px-2 py-1.5 text-left text-sm ${
                  active === c.id
                    ? 'bg-mira-50 font-medium text-mira-600'
                    : 'text-slate-600 hover:bg-slate-200'
                }`}
              >
                <span aria-hidden="true">{c.emoji}</span> {c.label}
              </button>
            </li>
          ))}
        </ul>
      </div>

      <div className="border-t border-slate-200 pt-md">
        <label className="flex cursor-pointer items-center justify-between text-sm text-slate-700">
          <span>Halal only</span>
          <input
            type="checkbox"
            checked={halalOnly}
            onChange={(e) => onHalalToggle(e.target.checked)}
            className="h-4 w-4 accent-mira-600"
          />
        </label>
      </div>

      <div className="border-t border-slate-200 pt-md">
        <label htmlFor="budget" className="mb-sm block text-sm text-slate-700">
          Max price: <span className="font-medium text-mira-600">AED {maxBudget}</span>
        </label>
        <input
          id="budget"
          type="range"
          min={0}
          max={50}
          step={5}
          value={maxBudget}
          onChange={(e) => onBudgetChange(Number(e.target.value))}
          className="w-full accent-mira-600"
        />
        <div className="mt-1 flex justify-between text-xs text-slate-400">
          <span>AED 0</span>
          <span>AED 50</span>
        </div>
      </div>
    </aside>
  )
}
