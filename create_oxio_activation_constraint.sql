
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
END $$;

-- Add unique constraint to prevent duplicate purchases within a short timeframe
DO $$ 
BEGIN
    -- Create partial unique index for recent purchases if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE indexname = 'unique_recent_purchase'
    ) THEN
        CREATE UNIQUE INDEX unique_recent_purchase 
        ON purchases(UserID, StripeProductID, (DateCreated::date)) 
        WHERE DateCreated > NOW() - INTERVAL '30 seconds';
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
        WHERE indexname = 'idx_purchases_recent'
    ) THEN
        CREATE INDEX idx_purchases_recent ON purchases(UserID, DateCreated) 
        WHERE DateCreated > NOW() - INTERVAL '1 minute';
    END IF;
END $$;
