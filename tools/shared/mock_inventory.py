"""Shared mock seed data for backend mock adapters.

Mirrors DATA_MODEL.md table shapes and stays consistent with the frontend
fixture (frontend/aria-app/lib/mockProducts.ts). The backend engineer can
replace these with the real data/seed/*.sql once AlloyDB is up; the adapters
read from here only in mock mode.

Kept intentionally small (a representative slice, not all 50 rows) — enough to
exercise every tool path incl. the brown-rice stockout and Almarai Laban
perishable-discount demo scenarios.
"""

from __future__ import annotations

STORE_ID = "dubai_marina_01"

MOCK_STORES = [
    {"store_id": "dubai_marina_01", "store_name": "MIRA Dubai Marina", "area": "Dubai Marina", "city": "Dubai"},
    {"store_id": "jbr_01", "store_name": "MIRA JBR", "area": "JBR", "city": "Dubai"},
    {"store_id": "al_barsha_01", "store_name": "MIRA Al Barsha", "area": "Al Barsha", "city": "Dubai"},
]

MOCK_CUSTOMERS = [
    {"customer_id": "sarah_123", "name": "Sarah", "email": "sarah@example.ae", "dietary_preference": "halal", "household_size": 4, "weekly_budget_aed": 300.0, "preferred_store": "dubai_marina_01",
     "last_orders": [
         {"product_id": "rice_basmati_5kg", "product_name": "India Gate Basmati Rice 5kg", "last_ordered": "2026-10-10"},
         {"product_id": "chicken_whole_1kg", "product_name": "Fresh Halal Whole Chicken 1kg", "last_ordered": "2026-10-10"},
         {"product_id": "milk_almarai_2l", "product_name": "Almarai Full Fat Milk 2L", "last_ordered": "2026-10-03"},
     ]},
    {"customer_id": "ahmed_456", "name": "Ahmed", "email": "ahmed@example.ae", "dietary_preference": "none", "household_size": 1, "weekly_budget_aed": 120.0, "preferred_store": "jbr_01",
     "last_orders": [
         {"product_id": "pasta_barilla_500g", "product_name": "Barilla Penne Pasta 500g", "last_ordered": "2026-10-12"},
     ]},
    {"customer_id": "fatima_789", "name": "Fatima", "email": "fatima@example.ae", "dietary_preference": "vegetarian", "household_size": 3, "weekly_budget_aed": 220.0, "preferred_store": "al_barsha_01",
     "last_orders": []},  # new customer, no history
]

# Representative inventory slice. dietary_flags is comma-separated like the DDL.
MOCK_INVENTORY = [
    {"product_id": "milk_almarai_2l", "product_name": "Almarai Full Fat Milk 2L", "category": "dairy", "brand": "Almarai", "price_aed": 12.0, "dietary_flags": "halal,vegetarian", "store_id": STORE_ID, "aisle_ref": "A2", "stock_quantity": 40, "reorder_threshold": 10, "discount_active": False, "is_perishable": True, "expiry_date": "2026-10-24"},
    {"product_id": "laban_almarai_1l", "product_name": "Almarai Laban 1L", "category": "dairy", "brand": "Almarai", "price_aed": 8.0, "dietary_flags": "halal,vegetarian", "store_id": STORE_ID, "aisle_ref": "A2", "stock_quantity": 48, "reorder_threshold": 12, "discount_active": True, "discount_pct": 25, "discounted_price_aed": 6.0, "is_perishable": True, "expiry_date": "2026-10-19"},
    {"product_id": "eggs_dozen", "product_name": "Fresh Eggs Dozen", "category": "dairy", "brand": "Al Jazeera", "price_aed": 13.0, "dietary_flags": "halal,vegetarian", "store_id": STORE_ID, "aisle_ref": "A2", "stock_quantity": 50, "reorder_threshold": 15, "discount_active": False, "is_perishable": True, "expiry_date": "2026-11-05"},
    {"product_id": "rice_basmati_5kg", "product_name": "India Gate Basmati Rice 5kg", "category": "grains", "brand": "India Gate", "price_aed": 45.0, "dietary_flags": "halal,vegetarian,vegan", "store_id": STORE_ID, "aisle_ref": "B1", "stock_quantity": 22, "reorder_threshold": 8, "discount_active": False, "is_perishable": False},
    {"product_id": "rice_brown_500g", "product_name": "Brown Rice 500g", "category": "grains", "brand": "Organic Larder", "price_aed": 9.5, "dietary_flags": "halal,vegetarian,vegan", "store_id": STORE_ID, "aisle_ref": "B1", "stock_quantity": 0, "reorder_threshold": 10, "discount_active": False, "is_perishable": False},
    {"product_id": "pasta_barilla_500g", "product_name": "Barilla Penne Pasta 500g", "category": "grains", "brand": "Barilla", "price_aed": 7.0, "dietary_flags": "halal,vegetarian,vegan", "store_id": STORE_ID, "aisle_ref": "B2", "stock_quantity": 35, "reorder_threshold": 10, "discount_active": False, "is_perishable": False},
    {"product_id": "chicken_whole_1kg", "product_name": "Fresh Halal Whole Chicken 1kg", "category": "halal_meat", "brand": "Al Islami", "price_aed": 22.0, "dietary_flags": "halal", "store_id": STORE_ID, "aisle_ref": "C1", "stock_quantity": 30, "reorder_threshold": 10, "discount_active": False, "is_perishable": True, "expiry_date": "2026-10-20"},
    {"product_id": "tomato_1kg", "product_name": "Fresh Tomatoes 1kg", "category": "vegetables", "brand": "Local Farm", "price_aed": 6.0, "dietary_flags": "halal,vegetarian,vegan", "store_id": STORE_ID, "aisle_ref": "D1", "stock_quantity": 45, "reorder_threshold": 15, "discount_active": False, "is_perishable": True, "expiry_date": "2026-10-22"},
    {"product_id": "onion_1kg", "product_name": "Yellow Onions 1kg", "category": "vegetables", "brand": "Local Farm", "price_aed": 4.5, "dietary_flags": "halal,vegetarian,vegan", "store_id": STORE_ID, "aisle_ref": "D1", "stock_quantity": 50, "reorder_threshold": 15, "discount_active": False, "is_perishable": True, "expiry_date": "2026-11-02"},
    {"product_id": "banana_1kg", "product_name": "Bananas 1kg", "category": "fruits", "brand": "Chiquita", "price_aed": 6.5, "dietary_flags": "halal,vegetarian,vegan", "store_id": STORE_ID, "aisle_ref": "E1", "stock_quantity": 42, "reorder_threshold": 15, "discount_active": False, "is_perishable": True, "expiry_date": "2026-10-21"},
    {"product_id": "bread_white_loaf", "product_name": "White Bread Loaf", "category": "snacks", "brand": "Modern Bakery", "price_aed": 5.0, "dietary_flags": "halal,vegetarian", "store_id": STORE_ID, "aisle_ref": "G1", "stock_quantity": 40, "reorder_threshold": 15, "discount_active": False, "is_perishable": True, "expiry_date": "2026-10-20"},
    {"product_id": "oil_sunflower_1_8l", "product_name": "Sunflower Oil 1.8L", "category": "condiments", "brand": "Rahma", "price_aed": 16.0, "dietary_flags": "halal,vegetarian,vegan", "store_id": STORE_ID, "aisle_ref": "H1", "stock_quantity": 28, "reorder_threshold": 10, "discount_active": False, "is_perishable": False},

    # ── Cross-store stock (other MIRA stores) — powers check_stock alternatives ──
    # Brown rice is OOS at Dubai Marina but IN STOCK at JBR and Al Barsha.
    {"product_id": "rice_brown_500g", "product_name": "Brown Rice 500g", "category": "grains", "brand": "Organic Larder", "price_aed": 9.5, "dietary_flags": "halal,vegetarian,vegan", "store_id": "jbr_01", "aisle_ref": "B1", "stock_quantity": 45, "reorder_threshold": 10, "discount_active": False, "is_perishable": False},
    {"product_id": "rice_brown_500g", "product_name": "Brown Rice 500g", "category": "grains", "brand": "Organic Larder", "price_aed": 9.5, "dietary_flags": "halal,vegetarian,vegan", "store_id": "al_barsha_01", "aisle_ref": "B2", "stock_quantity": 12, "reorder_threshold": 10, "discount_active": False, "is_perishable": False},
    # Strawberries OOS at Dubai Marina, in stock at JBR.
    {"product_id": "strawberry_250g", "product_name": "Strawberries 250g", "category": "fruits", "brand": "Driscoll", "price_aed": 14.0, "dietary_flags": "halal,vegetarian,vegan", "store_id": "jbr_01", "aisle_ref": "E3", "stock_quantity": 18, "reorder_threshold": 6, "discount_active": False, "is_perishable": True, "expiry_date": "2026-10-21"},
    # A couple of common products at other stores (for realism).
    {"product_id": "milk_almarai_2l", "product_name": "Almarai Full Fat Milk 2L", "category": "dairy", "brand": "Almarai", "price_aed": 12.0, "dietary_flags": "halal,vegetarian", "store_id": "jbr_01", "aisle_ref": "A2", "stock_quantity": 30, "reorder_threshold": 10, "discount_active": False, "is_perishable": True, "expiry_date": "2026-10-24"},
]

MOCK_PROMOTIONS = [
    {"promotion_id": "promo_dairy_saver", "name": "Dairy saver pack", "description": "15% off dairy over AED 40", "category": "dairy", "dietary_filter": None, "discount_pct": 15.0, "discount_flat_aed": None, "min_cart_aed": 40.0, "max_uses": None, "times_applied": 0, "valid_from": "2026-10-01", "valid_until": "2026-10-31", "is_active": True},
    {"promotion_id": "promo_rice_10", "name": "Rice 10% off", "description": "10% off rice & grains", "category": "grains", "dietary_filter": None, "discount_pct": 10.0, "discount_flat_aed": None, "min_cart_aed": 50.0, "max_uses": None, "times_applied": 0, "valid_from": "2026-10-01", "valid_until": "2026-10-31", "is_active": True},
    {"promotion_id": "promo_halal_bundle", "name": "Halal chicken bundle", "description": "Save on halal poultry", "category": "halal_meat", "dietary_filter": "halal", "discount_pct": 12.0, "discount_flat_aed": None, "min_cart_aed": 80.0, "max_uses": 100, "times_applied": 0, "valid_from": "2026-10-01", "valid_until": "2026-10-31", "is_active": True},
    # Expired promo (for validation testing) — must never be applied.
    {"promotion_id": "promo_expired", "name": "Summer sale", "description": "expired", "category": "all", "dietary_filter": None, "discount_pct": 20.0, "discount_flat_aed": None, "min_cart_aed": 0.0, "max_uses": None, "times_applied": 0, "valid_from": "2026-06-01", "valid_until": "2026-08-31", "is_active": True},
    # Maxed-out promo (for max_uses testing) — must never be applied.
    {"promotion_id": "promo_maxed", "name": "First 50 only", "description": "limit reached", "category": "all", "dietary_filter": None, "discount_pct": 30.0, "discount_flat_aed": None, "min_cart_aed": 0.0, "max_uses": 50, "times_applied": 50, "valid_from": "2026-10-01", "valid_until": "2026-10-31", "is_active": True},
]


# Replenishment schedules (mirror data/seed/04_replenishment.sql).
# The brown-rice Tuesday-14:00 gap vs Mon–Wed peak is the demo root cause.
MOCK_REPLENISHMENT = [
    {"store_id": STORE_ID, "product_id": "rice_brown_500g", "supplier_id": "sup_004", "delivery_day": "Tuesday", "delivery_time": "14:00", "quantity_per_delivery": 40, "lead_time_days": 2},
    {"store_id": STORE_ID, "product_id": "rice_basmati_5kg", "supplier_id": "sup_004", "delivery_day": "Monday", "delivery_time": "09:00", "quantity_per_delivery": 30, "lead_time_days": 2},
    {"store_id": STORE_ID, "product_id": "milk_almarai_2l", "supplier_id": "sup_001", "delivery_day": "Daily", "delivery_time": "06:00", "quantity_per_delivery": 60, "lead_time_days": 1},
    {"store_id": STORE_ID, "product_id": "laban_almarai_1l", "supplier_id": "sup_001", "delivery_day": "Daily", "delivery_time": "06:00", "quantity_per_delivery": 50, "lead_time_days": 1},
    {"store_id": STORE_ID, "product_id": "chicken_whole_1kg", "supplier_id": "sup_006", "delivery_day": "Wednesday", "delivery_time": "08:00", "quantity_per_delivery": 40, "lead_time_days": 2},
]
