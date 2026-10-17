-- ════════════════════════════════════════════════════════════════════
-- ARC seed 04 — replenishment schedules
-- DATA_MODEL.md §3: realistic delivery schedules per store per product.
--
-- THE DEMO SCENARIO (intentional gap):
--   Brown rice at Dubai Marina is delivered Tuesday 14:00, but customer
--   demand peaks Mon–Wed 10:00–12:00. The shelf empties ~20h before the next
--   replenishment lands. This is what PULSE.find_root_cause() surfaces.
-- ════════════════════════════════════════════════════════════════════

INSERT INTO replenishment_schedule
  (store_id, product_id, supplier_id, delivery_day, delivery_time,
   quantity_per_delivery, lead_time_days) VALUES
  -- The gap: brown rice delivered Tuesday afternoon, after the Mon–Wed peak
  ('dubai_marina_01', 'rice_brown_500g',   'sup_004', 'Tuesday',   '14:00', 40, 2),
  -- Other staples on healthier cadences
  ('dubai_marina_01', 'rice_basmati_5kg',  'sup_004', 'Monday',    '09:00', 30, 2),
  ('dubai_marina_01', 'milk_almarai_2l',   'sup_001', 'Daily',     '06:00', 60, 1),
  ('dubai_marina_01', 'laban_almarai_1l',  'sup_001', 'Daily',     '06:00', 50, 1),
  ('dubai_marina_01', 'chicken_whole_1kg', 'sup_006', 'Wednesday', '08:00', 40, 2),
  ('dubai_marina_01', 'tomato_1kg',        'sup_008', 'Daily',     '05:00', 50, 1),
  ('dubai_marina_01', 'banana_1kg',        'sup_009', 'Monday',    '07:00', 45, 2),
  ('dubai_marina_01', 'bread_white_loaf',  'sup_012', 'Daily',     '05:30', 40, 1),
  ('dubai_marina_01', 'strawberry_250g',   'sup_009', 'Thursday',  '07:00', 20, 2);
