// lib/mockData.ts
// Stores, customer personas, and promotions.
// Matches DATA_MODEL.md §3 seed overview and the table schemas.

import type { CustomerProfile, Promotion, Store } from './types'

export const MOCK_STORES: Store[] = [
  { store_id: 'dubai_marina_01', store_name: 'MIRA Dubai Marina', area: 'Dubai Marina', city: 'Dubai' },
  { store_id: 'jbr_01', store_name: 'MIRA JBR', area: 'JBR', city: 'Dubai' },
  { store_id: 'al_barsha_01', store_name: 'MIRA Al Barsha', area: 'Al Barsha', city: 'Dubai' },
]

// 5 personas from DATA_MODEL.md §3
export const MOCK_CUSTOMERS: CustomerProfile[] = [
  { customer_id: 'sarah_123', name: 'Sarah', email: 'sarah@example.ae', dietary_preference: 'halal', household_size: 4, weekly_budget_aed: 300, preferred_store: 'dubai_marina_01' },
  { customer_id: 'ahmed_456', name: 'Ahmed', email: 'ahmed@example.ae', dietary_preference: 'none', household_size: 1, weekly_budget_aed: 120, preferred_store: 'jbr_01' },
  { customer_id: 'fatima_789', name: 'Fatima', email: 'fatima@example.ae', dietary_preference: 'vegetarian', household_size: 3, weekly_budget_aed: 220, preferred_store: 'al_barsha_01' },
  { customer_id: 'kumar_234', name: 'Kumar', email: 'kumar@example.ae', dietary_preference: 'none', household_size: 2, weekly_budget_aed: 180, preferred_store: 'dubai_marina_01' },
  { customer_id: 'layla_567', name: 'Layla', email: 'layla@example.ae', dietary_preference: 'halal', household_size: 5, weekly_budget_aed: 380, preferred_store: 'dubai_marina_01' },
]

// Default persona for the mock session
export const DEFAULT_CUSTOMER = MOCK_CUSTOMERS[0] // Sarah

export const MOCK_PROMOTIONS: Promotion[] = [
  { promotion_id: 'promo_rice_10', name: 'Rice 10% off', description: '10% off all rice & grains', category: 'grains', dietary_filter: null, discount_pct: 10, min_cart_aed: 50, valid_from: '2026-10-01', valid_until: '2026-10-31', is_active: true },
  { promotion_id: 'promo_halal_bundle', name: 'Halal chicken bundle', description: 'Save on halal poultry', category: 'halal_meat', dietary_filter: 'halal', discount_pct: 12, min_cart_aed: 80, valid_from: '2026-10-01', valid_until: '2026-10-31', is_active: true },
  { promotion_id: 'promo_dairy_saver', name: 'Dairy saver pack', description: '15% off dairy over AED 40', category: 'dairy', dietary_filter: null, discount_pct: 15, min_cart_aed: 40, valid_from: '2026-10-01', valid_until: '2026-10-31', is_active: true },
  { promotion_id: 'promo_fresh_veg_15', name: 'Fresh veg 15% off', description: '15% off fresh vegetables', category: 'vegetables', dietary_filter: null, discount_pct: 15, min_cart_aed: 30, valid_from: '2026-10-01', valid_until: '2026-10-31', is_active: true },
  { promotion_id: 'promo_weekend_family', name: 'Weekend family bundle', description: 'AED 25 off carts over AED 250', category: 'all', dietary_filter: null, discount_pct: 0, min_cart_aed: 250, valid_from: '2026-10-01', valid_until: '2026-10-31', is_active: true },
]
