

-- First, ensure the oxio_activations table exists with correct structure
CREATE TABLE IF NOT EXISTS oxio_activations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    firebase_uid VARCHAR(128),
    purchase_id INTEGER,
    product_id VARCHAR(100),
    iccid VARCHAR(50),
    line_id VARCHAR(100),
    phone_number VARCHAR(20),
    activation_status VARCHAR(50),
    oxio_response TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Clean up any duplicate OXIO activations (keep the most recent one)
DELETE FROM oxio_activations 
WHERE ctid NOT IN (
    SELECT MIN(ctid) FROM oxio_activations 
    GROUP BY user_id, firebase_uid
);

-- Clean up duplicate purchases within the last 10 seconds (using fixed interval)
DELETE FROM purchases 
WHERE ctid NOT IN (
    SELECT MIN(ctid) FROM purchases 
    GROUP BY UserID, StripeProductID, DATE_TRUNC('second', DateCreated)
    HAVING MIN(DateCreated) > CURRENT_TIMESTAMP - INTERVAL '10 seconds'
);

-- Add unique constraint to prevent multiple activations per user
DO $$ 
BEGIN
    -- Add unique constraint for user_id if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'unique_user_oxio_activation'
    ) THEN
        ALTER TABLE oxio_activations 
        ADD CONSTRAINT unique_user_oxio_activation UNIQUE (user_id);
    END IF;
    
    -- Add unique constraint for firebase_uid if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'unique_firebase_oxio_activation'
    ) THEN
        ALTER TABLE oxio_activations 
        ADD CONSTRAINT unique_firebase_oxio_activation UNIQUE (firebase_uid);
    END IF;
END $$;

-- Create indexes for better performance if they don't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE indexname = 'idx_oxio_activations_user_id'
    ) THEN
        CREATE INDEX idx_oxio_activations_user_id ON oxio_activations(user_id);
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE indexname = 'idx_oxio_activations_firebase_uid'
    ) THEN
        CREATE INDEX idx_oxio_activations_firebase_uid ON oxio_activations(firebase_uid);
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE indexname = 'idx_purchases_user_product'
    ) THEN
        CREATE INDEX idx_purchases_user_product ON purchases(UserID, StripeProductID);
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE indexname = 'idx_purchases_created_at'
    ) THEN
        CREATE INDEX idx_purchases_created_at ON purchases(DateCreated);
    END IF;
END $$;

