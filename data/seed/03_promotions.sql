-- ════════════════════════════════════════════════════════════════════
-- ARC seed 03 — promotions (DATA_MODEL.md §3: 5 active promotions)
-- ════════════════════════════════════════════════════════════════════

INSERT INTO promotions
  (promotion_id, name, description, category, dietary_filter, discount_pct,
   discount_flat_aed, min_cart_aed, max_uses, valid_from, valid_until, is_active) VALUES
  ('promo_rice_10',       'Rice 10% off',          '10% off all rice & grains',       'grains',     NULL,    10.0, NULL,  50.0,  NULL, '2026-10-01', '2026-10-31', true),
  ('promo_halal_bundle',  'Halal chicken bundle',  'Save on halal poultry',           'halal_meat', 'halal', 12.0, NULL,  80.0,  NULL, '2026-10-01', '2026-10-31', true),
  ('promo_dairy_saver',   'Dairy saver pack',      '15% off dairy over AED 40',       'dairy',      NULL,    15.0, NULL,  40.0,  NULL, '2026-10-01', '2026-10-31', true),
  ('promo_fresh_veg_15',  'Fresh veg 15% off',     '15% off fresh vegetables',        'vegetables', NULL,    15.0, NULL,  30.0,  NULL, '2026-10-01', '2026-10-31', true),
  ('promo_weekend_family','Weekend family bundle', 'AED 25 off carts over AED 250',   'all',        NULL,    0.0,  25.0,  250.0, NULL, '2026-10-01', '2026-10-31', true);
