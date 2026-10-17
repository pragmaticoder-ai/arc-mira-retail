-- ════════════════════════════════════════════════════════════════════
-- ARC seed 01 — stores, suppliers, customer personas
-- DATA_MODEL.md §3: 3 stores, 5 customer personas
-- ════════════════════════════════════════════════════════════════════

-- ── Stores ──────────────────────────────────────────────────────────
INSERT INTO stores (store_id, store_name, area, city, is_active) VALUES
  ('dubai_marina_01', 'MIRA Dubai Marina', 'Dubai Marina', 'Dubai', true),
  ('jbr_01',          'MIRA JBR',          'JBR',          'Dubai', true),
  ('al_barsha_01',    'MIRA Al Barsha',    'Al Barsha',    'Dubai', true);

-- ── Suppliers ───────────────────────────────────────────────────────
INSERT INTO suppliers (supplier_id, supplier_name, contact_email, lead_time_days) VALUES
  ('sup_001', 'Almarai Dairy Co',      'orders@almarai.ae',      1),
  ('sup_002', 'Gulf Cheese Imports',   'orders@gulfcheese.ae',   3),
  ('sup_003', 'Al Jazeera Poultry',    'orders@aljazeera.ae',    2),
  ('sup_004', 'Organic Larder',        'orders@organiclarder.ae',2),
  ('sup_005', 'Pasta & Grains Intl',   'orders@pgi.ae',          4),
  ('sup_006', 'Al Islami Foods',       'orders@alislami.ae',     2),
  ('sup_007', 'Dubai Fish Market',     'orders@fishmarket.ae',   1),
  ('sup_008', 'Local Farm Co-op',      'orders@localfarm.ae',    1),
  ('sup_009', 'Fresh Fruit Importers', 'orders@freshfruit.ae',   2),
  ('sup_010', 'Masafi Beverages',      'orders@masafi.ae',       2),
  ('sup_011', 'Hot Drinks Trading',    'orders@hotdrinks.ae',    5),
  ('sup_012', 'Modern Bakery',         'orders@modernbakery.ae', 1),
  ('sup_013', 'Snack Distributors',    'orders@snacks.ae',       3),
  ('sup_014', 'Rahma Oils',            'orders@rahma.ae',        4),
  ('sup_015', 'Pantry Staples Co',     'orders@pantry.ae',       3);

-- ── Customer personas ───────────────────────────────────────────────
INSERT INTO customer_profiles
  (customer_id, name, email, dietary_preference, household_size, weekly_budget_aed, preferred_store) VALUES
  ('sarah_123',  'Sarah',  'sarah@example.ae',  'halal',      4, 300.00, 'dubai_marina_01'),
  ('ahmed_456',  'Ahmed',  'ahmed@example.ae',  'none',       1, 120.00, 'jbr_01'),
  ('fatima_789', 'Fatima', 'fatima@example.ae', 'vegetarian', 3, 220.00, 'al_barsha_01'),
  ('kumar_234',  'Kumar',  'kumar@example.ae',  'none',       2, 180.00, 'dubai_marina_01'),
  ('layla_567',  'Layla',  'layla@example.ae',  'halal',      5, 380.00, 'dubai_marina_01');
