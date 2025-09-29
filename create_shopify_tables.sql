-- Shopify integration tables for marketplace

-- Store Shopify shop credentials and settings
CREATE TABLE IF NOT EXISTS shopify_shops (
    id SERIAL PRIMARY KEY,
    shop_domain VARCHAR(255) UNIQUE NOT NULL,
    access_token TEXT NOT NULL,
    shop_name VARCHAR(255),
    email VARCHAR(255),
    plan_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    webhook_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Track products synced with Shopify
CREATE TABLE IF NOT EXISTS shopify_products (
    id SERIAL PRIMARY KEY,
    local_product_id INTEGER, -- References local product/listing
    shopify_product_id BIGINT NOT NULL,
    shopify_variant_id BIGINT,
    shop_domain VARCHAR(255) NOT NULL,
    product_title VARCHAR(255),
    product_handle VARCHAR(255),
    sku VARCHAR(100),
    price_cents INTEGER,
    inventory_quantity INTEGER DEFAULT 0,
    sync_status VARCHAR(50) DEFAULT 'synced', -- synced, pending, error
    last_sync_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (shop_domain) REFERENCES shopify_shops(shop_domain)
);

-- Shopify collections for category mapping
CREATE TABLE IF NOT EXISTS shopify_collections (
    id SERIAL PRIMARY KEY,
    shopify_collection_id BIGINT NOT NULL,
    shop_domain VARCHAR(255) NOT NULL,
    collection_title VARCHAR(255),
    collection_handle VARCHAR(255),
    collection_type VARCHAR(50), -- 'devices', 'esim_services', 'physical_products'
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (shop_domain) REFERENCES shopify_shops(shop_domain)
);

-- Seller listings (devices for auction/sale)
CREATE TABLE IF NOT EXISTS seller_listings (
    id SERIAL PRIMARY KEY,
    seller_firebase_uid VARCHAR(128) NOT NULL,
    seller_email VARCHAR(255),
    device_type VARCHAR(100) NOT NULL, -- 'smartphone', 'tablet', 'laptop', etc.
    brand VARCHAR(100),
    model VARCHAR(255) NOT NULL,
    storage_capacity VARCHAR(50),
    color VARCHAR(100),
    condition_grade VARCHAR(20) NOT NULL, -- 'excellent', 'good', 'fair', 'poor'
    cosmetic_condition TEXT,
    functional_condition TEXT,
    original_accessories TEXT, -- JSON array of included accessories
    asking_price_cents INTEGER NOT NULL,
    minimum_price_cents INTEGER,
    listing_type VARCHAR(20) DEFAULT 'auction', -- 'auction', 'fixed_price'
    photos JSON, -- Array of photo URLs
    description TEXT,
    imei VARCHAR(20),
    serial_number VARCHAR(100),
    carrier_lock_status VARCHAR(50), -- 'unlocked', 'locked_to_carrier', 'unknown'
    battery_health INTEGER, -- Percentage
    approval_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'approved', 'rejected'
    rejection_reason TEXT,
    approved_by_admin_uid VARCHAR(128),
    approved_at TIMESTAMP,
    shopify_product_id BIGINT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Seller profiles and verification
CREATE TABLE IF NOT EXISTS sellers (
    id SERIAL PRIMARY KEY,
    firebase_uid VARCHAR(128) UNIQUE NOT NULL,
    email VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    phone_number VARCHAR(20),
    verification_status VARCHAR(20) DEFAULT 'unverified', -- 'unverified', 'pending', 'verified'
    verification_documents JSON, -- Array of document URLs
    rating_average DECIMAL(3,2) DEFAULT 0.00,
    total_sales INTEGER DEFAULT 0,
    total_earnings_cents INTEGER DEFAULT 0,
    commission_rate DECIMAL(5,4) DEFAULT 0.1000, -- 10% default commission
    is_active BOOLEAN DEFAULT TRUE,
    verified_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Track orders and transactions
CREATE TABLE IF NOT EXISTS marketplace_orders (
    id SERIAL PRIMARY KEY,
    order_number VARCHAR(50) UNIQUE NOT NULL,
    buyer_firebase_uid VARCHAR(128),
    buyer_email VARCHAR(255),
    seller_firebase_uid VARCHAR(128) NOT NULL,
    seller_listing_id INTEGER NOT NULL,
    shopify_order_id BIGINT,
    stripe_payment_intent_id VARCHAR(255),
    total_amount_cents INTEGER NOT NULL,
    seller_amount_cents INTEGER NOT NULL, -- After commission
    commission_amount_cents INTEGER NOT NULL,
    order_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'paid', 'shipped', 'delivered', 'cancelled'
    payment_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'paid', 'failed', 'refunded'
    shipping_address JSON,
    tracking_number VARCHAR(100),
    shipped_at TIMESTAMP,
    delivered_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (seller_listing_id) REFERENCES seller_listings(id),
    FOREIGN KEY (seller_firebase_uid) REFERENCES sellers(firebase_uid)
);

-- Webhook events from Shopify
CREATE TABLE IF NOT EXISTS shopify_webhook_events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(100) UNIQUE NOT NULL,
    shop_domain VARCHAR(255),
    event_type VARCHAR(100) NOT NULL,
    event_data JSON NOT NULL,
    processed BOOLEAN DEFAULT FALSE,
    processing_error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);

-- Product sync queue for batch operations
CREATE TABLE IF NOT EXISTS product_sync_queue (
    id SERIAL PRIMARY KEY,
    operation_type VARCHAR(20) NOT NULL, -- 'create', 'update', 'delete'
    entity_type VARCHAR(20) NOT NULL, -- 'product', 'collection', 'listing'
    entity_id INTEGER NOT NULL,
    shopify_shop_domain VARCHAR(255),
    sync_data JSON,
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    retry_count INTEGER DEFAULT 0,
    error_message TEXT,
    scheduled_for TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_shopify_products_local_id ON shopify_products(local_product_id);
CREATE INDEX IF NOT EXISTS idx_shopify_products_shopify_id ON shopify_products(shopify_product_id);
CREATE INDEX IF NOT EXISTS idx_shopify_products_sync_status ON shopify_products(sync_status);

CREATE INDEX IF NOT EXISTS idx_seller_listings_seller_uid ON seller_listings(seller_firebase_uid);
CREATE INDEX IF NOT EXISTS idx_seller_listings_approval_status ON seller_listings(approval_status);
CREATE INDEX IF NOT EXISTS idx_seller_listings_shopify_product ON seller_listings(shopify_product_id);

CREATE INDEX IF NOT EXISTS idx_sellers_firebase_uid ON sellers(firebase_uid);
CREATE INDEX IF NOT EXISTS idx_sellers_verification_status ON sellers(verification_status);

CREATE INDEX IF NOT EXISTS idx_marketplace_orders_buyer_uid ON marketplace_orders(buyer_firebase_uid);
CREATE INDEX IF NOT EXISTS idx_marketplace_orders_seller_uid ON marketplace_orders(seller_firebase_uid);
CREATE INDEX IF NOT EXISTS idx_marketplace_orders_status ON marketplace_orders(order_status);
CREATE INDEX IF NOT EXISTS idx_marketplace_orders_payment_status ON marketplace_orders(payment_status);

CREATE INDEX IF NOT EXISTS idx_webhook_events_processed ON shopify_webhook_events(processed);
CREATE INDEX IF NOT EXISTS idx_webhook_events_event_type ON shopify_webhook_events(event_type);

CREATE INDEX IF NOT EXISTS idx_sync_queue_status ON product_sync_queue(status);
CREATE INDEX IF NOT EXISTS idx_sync_queue_scheduled ON product_sync_queue(scheduled_for);