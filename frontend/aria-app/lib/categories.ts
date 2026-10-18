import type { Product } from './types'

export const CATEGORY_META: {
  id: Product['category']
  label: string
  emoji: string
}[] = [
  { id: 'dairy', label: 'Dairy', emoji: '🥛' },
  { id: 'grains', label: 'Grains & staples', emoji: '🌾' },
  { id: 'halal_meat', label: 'Meat & seafood', emoji: '🍗' },
  { id: 'vegetables', label: 'Vegetables', emoji: '🥦' },
  { id: 'fruits', label: 'Fruits', emoji: '🍎' },
  { id: 'beverages', label: 'Beverages', emoji: '🧃' },
  { id: 'snacks', label: 'Snacks & bakery', emoji: '🥐' },
  { id: 'condiments', label: 'Condiments & oils', emoji: '🫒' },
]
