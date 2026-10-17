-- ════════════════════════════════════════════════════════════════════
-- ARC seed 02 — inventory (50 products, 8 categories, Dubai Marina)
-- Matches frontend/aria-app/lib/mockProducts.ts exactly.
-- Demo scenarios:
--   rice_brown_500g  : stock_quantity=0  (stockout → substitution + PULSE pattern)
--   strawberry_250g  : stock_quantity=0  (second OOS item)
--   laban_almarai_1l : discount_active=true, 25% (perishable discount surfacing)
-- Embeddings generated post-load (DEPLOYMENT.md §4); omitted here.
-- ════════════════════════════════════════════════════════════════════

INSERT INTO inventory
  (product_id, product_name, category, brand, price_aed, dietary_flags, store_id,
   aisle_ref, stock_quantity, reorder_threshold, supplier_id,
   is_perishable, expiry_date, discount_active, discount_pct) VALUES
-- ── Dairy ──
('milk_almarai_2l','Almarai Full Fat Milk 2L','dairy','Almarai',12.0,'halal,vegetarian','dubai_marina_01','A2',40,10,'sup_001',true,'2026-10-24',false,NULL),
('laban_almarai_1l','Almarai Laban 1L','dairy','Almarai',8.0,'halal,vegetarian','dubai_marina_01','A2',48,12,'sup_001',true,'2026-10-19',true,25.0),
('cheese_kraft_200g','Kraft Cheddar Slices 200g','dairy','Kraft',14.5,'halal,vegetarian','dubai_marina_01','A3',25,8,'sup_002',true,'2026-11-10',false,NULL),
('yogurt_activia_6pk','Activia Yogurt 6-pack','dairy','Activia',11.0,'halal,vegetarian','dubai_marina_01','A2',30,10,'sup_001',true,'2026-10-28',false,NULL),
('butter_lurpak_200g','Lurpak Butter 200g','dairy','Lurpak',16.0,'halal,vegetarian','dubai_marina_01','A3',18,6,'sup_002',true,'2026-12-01',false,NULL),
('eggs_dozen','Fresh Eggs Dozen','dairy','Al Jazeera',13.0,'halal,vegetarian','dubai_marina_01','A2',50,15,'sup_003',true,'2026-11-05',false,NULL),
-- ── Grains & staples ──
('rice_basmati_5kg','India Gate Basmati Rice 5kg','grains','India Gate',45.0,'halal,vegetarian,vegan','dubai_marina_01','B1',22,8,'sup_004',false,NULL,false,NULL),
('rice_brown_500g','Brown Rice 500g','grains','Organic Larder',9.5,'halal,vegetarian,vegan','dubai_marina_01','B1',0,10,'sup_004',false,NULL,false,NULL),
('pasta_barilla_500g','Barilla Penne Pasta 500g','grains','Barilla',7.0,'halal,vegetarian,vegan','dubai_marina_01','B2',35,10,'sup_005',false,NULL,false,NULL),
('flour_wheat_2kg','Whole Wheat Flour 2kg','grains','Al Khaleej',10.0,'halal,vegetarian,vegan','dubai_marina_01','B1',28,10,'sup_004',false,NULL,false,NULL),
('oats_quaker_1kg','Quaker Oats 1kg','grains','Quaker',18.0,'halal,vegetarian,vegan','dubai_marina_01','B2',20,6,'sup_005',false,NULL,false,NULL),
('lentils_red_1kg','Red Lentils 1kg','grains','Organic Larder',12.0,'halal,vegetarian,vegan','dubai_marina_01','B3',24,8,'sup_004',false,NULL,false,NULL),
-- ── Halal meat & poultry ──
('chicken_whole_1kg','Fresh Halal Whole Chicken 1kg','halal_meat','Al Islami',22.0,'halal','dubai_marina_01','C1',30,10,'sup_006',true,'2026-10-20',false,NULL),
('chicken_breast_500g','Halal Chicken Breast 500g','halal_meat','Al Islami',18.0,'halal','dubai_marina_01','C1',26,10,'sup_006',true,'2026-10-20',false,NULL),
('beef_mince_500g','Halal Beef Mince 500g','halal_meat','Al Ain',28.0,'halal','dubai_marina_01','C2',20,8,'sup_006',true,'2026-10-21',false,NULL),
('lamb_chops_500g','Halal Lamb Chops 500g','halal_meat','Al Ain',42.0,'halal','dubai_marina_01','C2',12,5,'sup_006',true,'2026-10-21',false,NULL),
('fish_salmon_400g','Fresh Salmon Fillet 400g','halal_meat','Fish Market',38.0,'halal','dubai_marina_01','C3',15,6,'sup_007',true,'2026-10-19',false,NULL),
-- ── Fresh vegetables ──
('tomato_1kg','Fresh Tomatoes 1kg','vegetables','Local Farm',6.0,'halal,vegetarian,vegan','dubai_marina_01','D1',45,15,'sup_008',true,'2026-10-22',false,NULL),
('onion_1kg','Yellow Onions 1kg','vegetables','Local Farm',4.5,'halal,vegetarian,vegan','dubai_marina_01','D1',50,15,'sup_008',true,'2026-11-02',false,NULL),
('potato_2kg','Potatoes 2kg','vegetables','Local Farm',8.0,'halal,vegetarian,vegan','dubai_marina_01','D1',40,12,'sup_008',true,'2026-11-08',false,NULL),
('cucumber_500g','Cucumbers 500g','vegetables','Local Farm',5.0,'halal,vegetarian,vegan','dubai_marina_01','D2',38,12,'sup_008',true,'2026-10-23',false,NULL),
('spinach_250g','Fresh Spinach 250g','vegetables','Green Valley',7.0,'halal,vegetarian,vegan','dubai_marina_01','D2',22,8,'sup_008',true,'2026-10-20',false,NULL),
('carrot_1kg','Carrots 1kg','vegetables','Local Farm',5.5,'halal,vegetarian,vegan','dubai_marina_01','D1',35,12,'sup_008',true,'2026-10-30',false,NULL),
-- ── Fresh fruits ──
('banana_1kg','Bananas 1kg','fruits','Chiquita',6.5,'halal,vegetarian,vegan','dubai_marina_01','E1',42,15,'sup_009',true,'2026-10-21',false,NULL),
('apple_red_1kg','Red Apples 1kg','fruits','Washington',9.0,'halal,vegetarian,vegan','dubai_marina_01','E1',36,12,'sup_009',true,'2026-10-27',false,NULL),
('orange_2kg','Oranges 2kg','fruits','Valencia',12.0,'halal,vegetarian,vegan','dubai_marina_01','E2',28,10,'sup_009',true,'2026-10-25',false,NULL),
('grapes_500g','Seedless Grapes 500g','fruits','Local Farm',11.0,'halal,vegetarian,vegan','dubai_marina_01','E2',20,8,'sup_009',true,'2026-10-20',false,NULL),
('mango_1kg','Alphonso Mangoes 1kg','fruits','Ratnagiri',18.0,'halal,vegetarian,vegan','dubai_marina_01','E3',16,6,'sup_009',true,'2026-10-22',false,NULL),
('strawberry_250g','Strawberries 250g','fruits','Driscoll',14.0,'halal,vegetarian,vegan','dubai_marina_01','E3',0,6,'sup_009',true,'2026-10-19',false,NULL),
-- ── Beverages ──
('water_masafi_6pk','Masafi Water 6x1.5L','beverages','Masafi',9.0,'halal,vegetarian,vegan','dubai_marina_01','F1',60,20,'sup_010',false,NULL,false,NULL),
('juice_lacnor_1l','Lacnor Orange Juice 1L','beverages','Lacnor',8.5,'halal,vegetarian','dubai_marina_01','F1',34,12,'sup_010',true,'2026-11-15',false,NULL),
('tea_lipton_100','Lipton Tea Bags 100s','beverages','Lipton',15.0,'halal,vegetarian,vegan','dubai_marina_01','F2',25,8,'sup_011',false,NULL,false,NULL),
('coffee_nescafe_200g','Nescafe Gold 200g','beverages','Nescafe',32.0,'halal,vegetarian,vegan','dubai_marina_01','F2',18,6,'sup_011',false,NULL,false,NULL),
('soda_pepsi_6pk','Pepsi 6x330ml','beverages','Pepsi',12.0,'halal,vegetarian,vegan','dubai_marina_01','F3',44,15,'sup_010',false,NULL,false,NULL),
('laban_up_1l','Laban Up 1L','beverages','Marmum',7.5,'halal,vegetarian','dubai_marina_01','F1',30,10,'sup_001',true,'2026-10-26',false,NULL),
-- ── Snacks & bakery ──
('bread_white_loaf','White Bread Loaf','snacks','Modern Bakery',5.0,'halal,vegetarian','dubai_marina_01','G1',40,15,'sup_012',true,'2026-10-20',false,NULL),
('croissant_4pk','Butter Croissants 4-pack','snacks','Modern Bakery',12.0,'halal,vegetarian','dubai_marina_01','G1',22,8,'sup_012',true,'2026-10-19',false,NULL),
('chips_lays_165g','Lays Classic Chips 165g','snacks','Lays',8.0,'halal,vegetarian','dubai_marina_01','G2',50,15,'sup_013',false,NULL,false,NULL),
('biscuits_oreo_300g','Oreo Biscuits 300g','snacks','Oreo',10.0,'halal,vegetarian','dubai_marina_01','G2',38,12,'sup_013',false,NULL,false,NULL),
('nuts_mixed_500g','Mixed Nuts 500g','snacks','Al Rifai',35.0,'halal,vegetarian,vegan','dubai_marina_01','G3',16,6,'sup_013',false,NULL,false,NULL),
('dates_khalas_1kg','Khalas Dates 1kg','snacks','Bateel',28.0,'halal,vegetarian,vegan','dubai_marina_01','G3',24,8,'sup_013',false,NULL,false,NULL),
-- ── Condiments & oils ──
('oil_olive_1l','Extra Virgin Olive Oil 1L','condiments','Rahma',30.0,'halal,vegetarian,vegan','dubai_marina_01','H1',20,8,'sup_014',false,NULL,false,NULL),
('oil_sunflower_1_8l','Sunflower Oil 1.8L','condiments','Rahma',16.0,'halal,vegetarian,vegan','dubai_marina_01','H1',28,10,'sup_014',false,NULL,false,NULL),
('ketchup_heinz_570g','Heinz Ketchup 570g','condiments','Heinz',11.0,'halal,vegetarian,vegan','dubai_marina_01','H2',32,10,'sup_015',false,NULL,false,NULL),
('salt_table_1kg','Iodized Table Salt 1kg','condiments','Al Ghurair',3.0,'halal,vegetarian,vegan','dubai_marina_01','H2',48,15,'sup_015',false,NULL,false,NULL),
('sugar_white_2kg','White Sugar 2kg','condiments','Al Khaleej',9.0,'halal,vegetarian,vegan','dubai_marina_01','H3',36,12,'sup_015',false,NULL,false,NULL),
('honey_natural_500g','Natural Honey 500g','condiments','Al Shifa',34.0,'halal,vegetarian','dubai_marina_01','H3',14,5,'sup_015',false,NULL,false,NULL),
('vinegar_apple_500ml','Apple Cider Vinegar 500ml','condiments','Bragg',22.0,'halal,vegetarian,vegan','dubai_marina_01','H2',18,6,'sup_014',false,NULL,false,NULL),
('spice_mix_100g','Biryani Spice Mix 100g','condiments','Shan',6.0,'halal,vegetarian,vegan','dubai_marina_01','H1',40,12,'sup_015',false,NULL,false,NULL);
