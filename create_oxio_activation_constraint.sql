
-- First, let's clean up any duplicate OXIO activations (keep the most recent one)
DELETE FROM oxio_activations 
WHERE id IN (
    SELECT id FROM (
        SELECT id, ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC) as rn
        FROM oxio_activations
    ) t WHERE rn > 1
);

-- Also clean up duplicates by firebase_uid
DELETE FROM oxio_activations 
WHERE id IN (
    SELECT id FROM (
        SELECT id, ROW_NUMBER() OVER (PARTITION BY firebase_uid ORDER BY created_at DESC) as rn
        FROM oxio_activations
        WHERE firebase_uid IS NOT NULL
    ) t WHERE rn > 1
);

-- Add unique constraint to prevent multiple activations per user
-- Check if constraint exists first, then add if it doesn't
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

-- Clean up duplicate purchases within the last 10 seconds (using fixed interval instead of NOW())
DELETE FROM purchases 
WHERE id IN (
    SELECT id FROM (
        SELECT id, ROW_NUMBER() OVER (
            PARTITION BY UserID, StripeProductID, (DateCreated::date) 
            ORDER BY DateCreated DESC
        ) as rn
        FROM purchases
        WHERE DateCreated > CURRENT_TIMESTAMP - INTERVAL '10 seconds'
    ) t WHERE rn > 1
);

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
