-- Sample cross-store availability for transfer proposals. No demand is seeded.
INSERT INTO inventory
    (product_id, product_name, category, brand, price_aed, dietary_flags, store_id,
     aisle_ref, stock_quantity, reorder_threshold, supplier_id,
     is_perishable, expiry_date, discount_active, discount_pct)
SELECT src.product_id, src.product_name, src.category, src.brand, src.price_aed,
       src.dietary_flags, dest.store_id, src.aisle_ref, dest.quantity,
       dest.threshold, src.supplier_id, src.is_perishable, src.expiry_date, false, NULL
FROM inventory src
JOIN (VALUES
    ('rice_brown_500g', 'jbr_01', 45, 10),
    ('rice_brown_500g', 'al_barsha_01', 12, 10),
    ('strawberry_250g', 'jbr_01', 18, 6),
    ('milk_almarai_2l', 'jbr_01', 30, 10)
) AS dest(product_id, store_id, quantity, threshold) ON dest.product_id=src.product_id
WHERE src.store_id='dubai_marina_01';
