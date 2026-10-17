// lib/mockProducts.ts
// 50 MIRA Retail products across 8 grocery categories.
// Fields match DATA_MODEL.md inventory table exactly.
// Demo scenarios baked in:
//   - "rice_brown_500g" is OUT OF STOCK (stock_quantity=0) at Dubai Marina
//     → drives the ARIA substitution + PULSE stockout pattern demo.
//   - "laban_almarai_1l" has discount_active=true (perishable 25% off)
//     → drives ARIA surfacing the PULSE-approved discount.

import type { Product } from './types'

const STORE = 'dubai_marina_01'
const SUP = (n: number) => `sup_${String(n).padStart(3, '0')}`

export const MOCK_PRODUCTS: Product[] = [
  // ── Dairy ──────────────────────────────────────────────────────────
  { product_id: 'milk_almarai_2l', product_name: 'Almarai Full Fat Milk 2L', category: 'dairy', brand: 'Almarai', price_aed: 12.0, dietary_flags: 'halal,vegetarian', store_id: STORE, aisle_ref: 'A2', stock_quantity: 40, reorder_threshold: 10, supplier_id: SUP(1), discount_active: false, is_perishable: true, expiry_date: '2026-10-24' },
  { product_id: 'laban_almarai_1l', product_name: 'Almarai Laban 1L', category: 'dairy', brand: 'Almarai', price_aed: 8.0, dietary_flags: 'halal,vegetarian', store_id: STORE, aisle_ref: 'A2', stock_quantity: 48, reorder_threshold: 12, supplier_id: SUP(1), discount_active: true, discount_pct: 25, discounted_price_aed: 6.0, is_perishable: true, expiry_date: '2026-10-19' },
  { product_id: 'cheese_kraft_200g', product_name: 'Kraft Cheddar Slices 200g', category: 'dairy', brand: 'Kraft', price_aed: 14.5, dietary_flags: 'halal,vegetarian', store_id: STORE, aisle_ref: 'A3', stock_quantity: 25, reorder_threshold: 8, supplier_id: SUP(2), discount_active: false, is_perishable: true, expiry_date: '2026-11-10' },
  { product_id: 'yogurt_activia_6pk', product_name: 'Activia Yogurt 6-pack', category: 'dairy', brand: 'Activia', price_aed: 11.0, dietary_flags: 'halal,vegetarian', store_id: STORE, aisle_ref: 'A2', stock_quantity: 30, reorder_threshold: 10, supplier_id: SUP(1), discount_active: false, is_perishable: true, expiry_date: '2026-10-28' },
  { product_id: 'butter_lurpak_200g', product_name: 'Lurpak Butter 200g', category: 'dairy', brand: 'Lurpak', price_aed: 16.0, dietary_flags: 'halal,vegetarian', store_id: STORE, aisle_ref: 'A3', stock_quantity: 18, reorder_threshold: 6, supplier_id: SUP(2), discount_active: false, is_perishable: true, expiry_date: '2026-12-01' },
  { product_id: 'eggs_dozen', product_name: 'Fresh Eggs Dozen', category: 'dairy', brand: 'Al Jazeera', price_aed: 13.0, dietary_flags: 'halal,vegetarian', store_id: STORE, aisle_ref: 'A2', stock_quantity: 50, reorder_threshold: 15, supplier_id: SUP(3), discount_active: false, is_perishable: true, expiry_date: '2026-11-05' },

  // ── Grains & staples ───────────────────────────────────────────────
  { product_id: 'rice_basmati_5kg', product_name: 'India Gate Basmati Rice 5kg', category: 'grains', brand: 'India Gate', price_aed: 45.0, dietary_flags: 'halal,vegetarian,vegan', store_id: STORE, aisle_ref: 'B1', stock_quantity: 22, reorder_threshold: 8, supplier_id: SUP(4), discount_active: false, is_perishable: false },
  { product_id: 'rice_brown_500g', product_name: 'Brown Rice 500g', category: 'grains', brand: 'Organic Larder', price_aed: 9.5, dietary_flags: 'halal,vegetarian,vegan', store_id: STORE, aisle_ref: 'B1', stock_quantity: 0, reorder_threshold: 10, supplier_id: SUP(4), discount_active: false, is_perishable: false },
  { product_id: 'pasta_barilla_500g', product_name: 'Barilla Penne Pasta 500g', category: 'grains', brand: 'Barilla', price_aed: 7.0, dietary_flags: 'halal,vegetarian,vegan', store_id: STORE, aisle_ref: 'B2', stock_quantity: 35, reorder_threshold: 10, supplier_id: SUP(5), discount_active: false, is_perishable: false },
  { product_id: 'flour_wheat_2kg', product_name: 'Whole Wheat Flour 2kg', category: 'grains', brand: 'Al Khaleej', price_aed: 10.0, dietary_flags: 'halal,vegetarian,vegan', store_id: STORE, aisle_ref: 'B1', stock_quantity: 28, reorder_threshold: 10, supplier_id: SUP(4), discount_active: false, is_perishable: false },
  { product_id: 'oats_quaker_1kg', product_name: 'Quaker Oats 1kg', category: 'grains', brand: 'Quaker', price_aed: 18.0, dietary_flags: 'halal,vegetarian,vegan', store_id: STORE, aisle_ref: 'B2', stock_quantity: 20, reorder_threshold: 6, supplier_id: SUP(5), discount_active: false, is_perishable: false },
  { product_id: 'lentils_red_1kg', product_name: 'Red Lentils 1kg', category: 'grains', brand: 'Organic Larder', price_aed: 12.0, dietary_flags: 'halal,vegetarian,vegan', store_id: STORE, aisle_ref: 'B3', stock_quantity: 24, reorder_threshold: 8, supplier_id: SUP(4), discount_active: false, is_perishable: false },

  // ── Halal meat & poultry ───────────────────────────────────────────
  { product_id: 'chicken_whole_1kg', product_name: 'Fresh Halal Whole Chicken 1kg', category: 'halal_meat', brand: 'Al Islami', price_aed: 22.0, dietary_flags: 'halal', store_id: STORE, aisle_ref: 'C1', stock_quantity: 30, reorder_threshold: 10, supplier_id: SUP(6), discount_active: false, is_perishable: true, expiry_date: '2026-10-20' },
  { product_id: 'chicken_breast_500g', product_name: 'Halal Chicken Breast 500g', category: 'halal_meat', brand: 'Al Islami', price_aed: 18.0, dietary_flags: 'halal', store_id: STORE, aisle_ref: 'C1', stock_quantity: 26, reorder_threshold: 10, supplier_id: SUP(6), discount_active: false, is_perishable: true, expiry_date: '2026-10-20' },
  { product_id: 'beef_mince_500g', product_name: 'Halal Beef Mince 500g', category: 'halal_meat', brand: 'Al Ain', price_aed: 28.0, dietary_flags: 'halal', store_id: STORE, aisle_ref: 'C2', stock_quantity: 20, reorder_threshold: 8, supplier_id: SUP(6), discount_active: false, is_perishable: true, expiry_date: '2026-10-21' },
  { product_id: 'lamb_chops_500g', product_name: 'Halal Lamb Chops 500g', category: 'halal_meat', brand: 'Al Ain', price_aed: 42.0, dietary_flags: 'halal', store_id: STORE, aisle_ref: 'C2', stock_quantity: 12, reorder_threshold: 5, supplier_id: SUP(6), discount_active: false, is_perishable: true, expiry_date: '2026-10-21' },
  { product_id: 'fish_salmon_400g', product_name: 'Fresh Salmon Fillet 400g', category: 'halal_meat', brand: 'Fish Market', price_aed: 38.0, dietary_flags: 'halal', store_id: STORE, aisle_ref: 'C3', stock_quantity: 15, reorder_threshold: 6, supplier_id: SUP(7), discount_active: false, is_perishable: true, expiry_date: '2026-10-19' },

  // ── Fresh vegetables ───────────────────────────────────────────────
  { product_id: 'tomato_1kg', product_name: 'Fresh Tomatoes 1kg', category: 'vegetables', brand: 'Local Farm', price_aed: 6.0, dietary_flags: 'halal,vegetarian,vegan', store_id: STORE, aisle_ref: 'D1', stock_quantity: 45, reorder_threshold: 15, supplier_id: SUP(8), discount_active: false, is_perishable: true, expiry_date: '2026-10-22' },
  { product_id: 'onion_1kg', product_name: 'Yellow Onions 1kg', category: 'vegetables', brand: 'Local Farm', price_aed: 4.5, dietary_flags: 'halal,vegetarian,vegan', store_id: STORE, aisle_ref: 'D1', stock_quantity: 50, reorder_threshold: 15, supplier_id: SUP(8), discount_active: false, is_perishable: true, expiry_date: '2026-11-02' },
  { product_id: 'potato_2kg', product_name: 'Potatoes 2kg', category: 'vegetables', brand: 'Local Farm', price_aed: 8.0, dietary_flags: 'halal,vegetarian,vegan', store_id: STORE, aisle_ref: 'D1', stock_quantity: 40, reorder_threshold: 12, supplier_id: SUP(8), discount_active: false, is_perishable: true, expiry_date: '2026-11-08' },
  { product_id: 'cucumber_500g', product_name: 'Cucumbers 500g', category: 'vegetables', brand: 'Local Farm', price_aed: 5.0, dietary_flags: 'halal,vegetarian,vegan', store_id: STORE, aisle_ref: 'D2', stock_quantity: 38, reorder_threshold: 12, supplier_id: SUP(8), discount_active: false, is_perishable: true, expiry_date: '2026-10-23' },
  { product_id: 'spinach_250g', product_name: 'Fresh Spinach 250g', category: 'vegetables', brand: 'Green Valley', price_aed: 7.0, dietary_flags: 'halal,vegetarian,vegan', store_id: STORE, aisle_ref: 'D2', stock_quantity: 22, reorder_threshold: 8, supplier_id: SUP(8), discount_active: false, is_perishable: true, expiry_date: '2026-10-20' },
  { product_id: 'carrot_1kg', product_name: 'Carrots 1kg', category: 'vegetables', brand: 'Local Farm', price_aed: 5.5, dietary_flags: 'halal,vegetarian,vegan', store_id: STORE, aisle_ref: 'D1', stock_quantity: 35, reorder_threshold: 12, supplier_id: SUP(8), discount_active: false, is_perishable: true, expiry_date: '2026-10-30' },

  // ── Fresh fruits ───────────────────────────────────────────────────
  { product_id: 'banana_1kg', product_name: 'Bananas 1kg', category: 'fruits', brand: 'Chiquita', price_aed: 6.5, dietary_flags: 'halal,vegetarian,vegan', store_id: STORE, aisle_ref: 'E1', stock_quantity: 42, reorder_threshold: 15, supplier_id: SUP(9), discount_active: false, is_perishable: true, expiry_date: '2026-10-21' },
  { product_id: 'apple_red_1kg', product_name: 'Red Apples 1kg', category: 'fruits', brand: 'Washington', price_aed: 9.0, dietary_flags: 'halal,vegetarian,vegan', store_id: STORE, aisle_ref: 'E1', stock_quantity: 36, reorder_threshold: 12, supplier_id: SUP(9), discount_active: false, is_perishable: true, expiry_date: '2026-10-27' },
  { product_id: 'orange_2kg', product_name: 'Oranges 2kg', category: 'fruits', brand: 'Valencia', price_aed: 12.0, dietary_flags: 'halal,vegetarian,vegan', store_id: STORE, aisle_ref: 'E2', stock_quantity: 28, reorder_threshold: 10, supplier_id: SUP(9), discount_active: false, is_perishable: true, expiry_date: '2026-10-25' },
  { product_id: 'grapes_500g', product_name: 'Seedless Grapes 500g', category: 'fruits', brand: 'Local Farm', price_aed: 11.0, dietary_flags: 'halal,vegetarian,vegan', store_id: STORE, aisle_ref: 'E2', stock_quantity: 20, reorder_threshold: 8, supplier_id: SUP(9), discount_active: false, is_perishable: true, expiry_date: '2026-10-20' },
  { product_id: 'mango_1kg', product_name: 'Alphonso Mangoes 1kg', category: 'fruits', brand: 'Ratnagiri', price_aed: 18.0, dietary_flags: 'halal,vegetarian,vegan', store_id: STORE, aisle_ref: 'E3', stock_quantity: 16, reorder_threshold: 6, supplier_id: SUP(9), discount_active: false, is_perishable: true, expiry_date: '2026-10-22' },
  { product_id: 'strawberry_250g', product_name: 'Strawberries 250g', category: 'fruits', brand: 'Driscoll', price_aed: 14.0, dietary_flags: 'halal,vegetarian,vegan', store_id: STORE, aisle_ref: 'E3', stock_quantity: 0, reorder_threshold: 6, supplier_id: SUP(9), discount_active: false, is_perishable: true, expiry_date: '2026-10-19' },

  // ── Beverages ──────────────────────────────────────────────────────
  { product_id: 'water_masafi_6pk', product_name: 'Masafi Water 6x1.5L', category: 'beverages', brand: 'Masafi', price_aed: 9.0, dietary_flags: 'halal,vegetarian,vegan', store_id: STORE, aisle_ref: 'F1', stock_quantity: 60, reorder_threshold: 20, supplier_id: SUP(10), discount_active: false, is_perishable: false },
  { product_id: 'juice_lacnor_1l', product_name: 'Lacnor Orange Juice 1L', category: 'beverages', brand: 'Lacnor', price_aed: 8.5, dietary_flags: 'halal,vegetarian', store_id: STORE, aisle_ref: 'F1', stock_quantity: 34, reorder_threshold: 12, supplier_id: SUP(10), discount_active: false, is_perishable: true, expiry_date: '2026-11-15' },
  { product_id: 'tea_lipton_100', product_name: 'Lipton Tea Bags 100s', category: 'beverages', brand: 'Lipton', price_aed: 15.0, dietary_flags: 'halal,vegetarian,vegan', store_id: STORE, aisle_ref: 'F2', stock_quantity: 25, reorder_threshold: 8, supplier_id: SUP(11), discount_active: false, is_perishable: false },
  { product_id: 'coffee_nescafe_200g', product_name: 'Nescafe Gold 200g', category: 'beverages', brand: 'Nescafe', price_aed: 32.0, dietary_flags: 'halal,vegetarian,vegan', store_id: STORE, aisle_ref: 'F2', stock_quantity: 18, reorder_threshold: 6, supplier_id: SUP(11), discount_active: false, is_perishable: false },
  { product_id: 'soda_pepsi_6pk', product_name: 'Pepsi 6x330ml', category: 'beverages', brand: 'Pepsi', price_aed: 12.0, dietary_flags: 'halal,vegetarian,vegan', store_id: STORE, aisle_ref: 'F3', stock_quantity: 44, reorder_threshold: 15, supplier_id: SUP(10), discount_active: false, is_perishable: false },
  { product_id: 'laban_up_1l', product_name: 'Laban Up 1L', category: 'beverages', brand: 'Marmum', price_aed: 7.5, dietary_flags: 'halal,vegetarian', store_id: STORE, aisle_ref: 'F1', stock_quantity: 30, reorder_threshold: 10, supplier_id: SUP(1), discount_active: false, is_perishable: true, expiry_date: '2026-10-26' },

  // ── Snacks & bakery ────────────────────────────────────────────────
  { product_id: 'bread_white_loaf', product_name: 'White Bread Loaf', category: 'snacks', brand: 'Modern Bakery', price_aed: 5.0, dietary_flags: 'halal,vegetarian', store_id: STORE, aisle_ref: 'G1', stock_quantity: 40, reorder_threshold: 15, supplier_id: SUP(12), discount_active: false, is_perishable: true, expiry_date: '2026-10-20' },
  { product_id: 'croissant_4pk', product_name: 'Butter Croissants 4-pack', category: 'snacks', brand: 'Modern Bakery', price_aed: 12.0, dietary_flags: 'halal,vegetarian', store_id: STORE, aisle_ref: 'G1', stock_quantity: 22, reorder_threshold: 8, supplier_id: SUP(12), discount_active: false, is_perishable: true, expiry_date: '2026-10-19' },
  { product_id: 'chips_lays_165g', product_name: 'Lays Classic Chips 165g', category: 'snacks', brand: 'Lays', price_aed: 8.0, dietary_flags: 'halal,vegetarian', store_id: STORE, aisle_ref: 'G2', stock_quantity: 50, reorder_threshold: 15, supplier_id: SUP(13), discount_active: false, is_perishable: false },
  { product_id: 'biscuits_oreo_300g', product_name: 'Oreo Biscuits 300g', category: 'snacks', brand: 'Oreo', price_aed: 10.0, dietary_flags: 'halal,vegetarian', store_id: STORE, aisle_ref: 'G2', stock_quantity: 38, reorder_threshold: 12, supplier_id: SUP(13), discount_active: false, is_perishable: false },
  { product_id: 'nuts_mixed_500g', product_name: 'Mixed Nuts 500g', category: 'snacks', brand: 'Al Rifai', price_aed: 35.0, dietary_flags: 'halal,vegetarian,vegan', store_id: STORE, aisle_ref: 'G3', stock_quantity: 16, reorder_threshold: 6, supplier_id: SUP(13), discount_active: false, is_perishable: false },
  { product_id: 'dates_khalas_1kg', product_name: 'Khalas Dates 1kg', category: 'snacks', brand: 'Bateel', price_aed: 28.0, dietary_flags: 'halal,vegetarian,vegan', store_id: STORE, aisle_ref: 'G3', stock_quantity: 24, reorder_threshold: 8, supplier_id: SUP(13), discount_active: false, is_perishable: false },

  // ── Condiments & oils ──────────────────────────────────────────────
  { product_id: 'oil_olive_1l', product_name: 'Extra Virgin Olive Oil 1L', category: 'condiments', brand: 'Rahma', price_aed: 30.0, dietary_flags: 'halal,vegetarian,vegan', store_id: STORE, aisle_ref: 'H1', stock_quantity: 20, reorder_threshold: 8, supplier_id: SUP(14), discount_active: false, is_perishable: false },
  { product_id: 'oil_sunflower_1_8l', product_name: 'Sunflower Oil 1.8L', category: 'condiments', brand: 'Rahma', price_aed: 16.0, dietary_flags: 'halal,vegetarian,vegan', store_id: STORE, aisle_ref: 'H1', stock_quantity: 28, reorder_threshold: 10, supplier_id: SUP(14), discount_active: false, is_perishable: false },
  { product_id: 'ketchup_heinz_570g', product_name: 'Heinz Ketchup 570g', category: 'condiments', brand: 'Heinz', price_aed: 11.0, dietary_flags: 'halal,vegetarian,vegan', store_id: STORE, aisle_ref: 'H2', stock_quantity: 32, reorder_threshold: 10, supplier_id: SUP(15), discount_active: false, is_perishable: false },
  { product_id: 'salt_table_1kg', product_name: 'Iodized Table Salt 1kg', category: 'condiments', brand: 'Al Ghurair', price_aed: 3.0, dietary_flags: 'halal,vegetarian,vegan', store_id: STORE, aisle_ref: 'H2', stock_quantity: 48, reorder_threshold: 15, supplier_id: SUP(15), discount_active: false, is_perishable: false },
  { product_id: 'sugar_white_2kg', product_name: 'White Sugar 2kg', category: 'condiments', brand: 'Al Khaleej', price_aed: 9.0, dietary_flags: 'halal,vegetarian,vegan', store_id: STORE, aisle_ref: 'H3', stock_quantity: 36, reorder_threshold: 12, supplier_id: SUP(15), discount_active: false, is_perishable: false },
  { product_id: 'honey_natural_500g', product_name: 'Natural Honey 500g', category: 'condiments', brand: 'Al Shifa', price_aed: 34.0, dietary_flags: 'halal,vegetarian', store_id: STORE, aisle_ref: 'H3', stock_quantity: 14, reorder_threshold: 5, supplier_id: SUP(15), discount_active: false, is_perishable: false },
  { product_id: 'vinegar_apple_500ml', product_name: 'Apple Cider Vinegar 500ml', category: 'condiments', brand: 'Bragg', price_aed: 22.0, dietary_flags: 'halal,vegetarian,vegan', store_id: STORE, aisle_ref: 'H2', stock_quantity: 18, reorder_threshold: 6, supplier_id: SUP(14), discount_active: false, is_perishable: false },
  { product_id: 'spice_mix_100g', product_name: 'Biryani Spice Mix 100g', category: 'condiments', brand: 'Shan', price_aed: 6.0, dietary_flags: 'halal,vegetarian,vegan', store_id: STORE, aisle_ref: 'H1', stock_quantity: 40, reorder_threshold: 12, supplier_id: SUP(15), discount_active: false, is_perishable: false },
]

export const CATEGORY_META: {
  id: Product['category']
  label: string
  emoji: string
}[] = [
  { id: 'dairy', label: 'Dairy', emoji: '🥛' },
  { id: 'grains', label: 'Grains & staples', emoji: '🌾' },
  { id: 'halal_meat', label: 'Halal meat', emoji: '🍗' },
  { id: 'vegetables', label: 'Vegetables', emoji: '🥦' },
  { id: 'fruits', label: 'Fruits', emoji: '🍎' },
  { id: 'beverages', label: 'Beverages', emoji: '🧃' },
  { id: 'snacks', label: 'Snacks & bakery', emoji: '🥐' },
  { id: 'condiments', label: 'Condiments & oils', emoji: '🫒' },
]

export function getProductById(id: string): Product | undefined {
  return MOCK_PRODUCTS.find((p) => p.product_id === id)
}
