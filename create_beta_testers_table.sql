
-- Create beta testers table for tracking enrollment
CREATE TABLE IF NOT EXISTS beta_testers (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    firebase_uid VARCHAR(128),
    stripe_customer_id VARCHAR(100),
    stripe_subscription_id VARCHAR(100),
    action VARCHAR(10) NOT NULL CHECK (action IN ('ON', 'OFF')),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    github_username VARCHAR(100),
    firebase_app_distribution_group VARCHAR(100),
    device_info TEXT,
    app_version VARCHAR(50),
    
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_beta_testers_user_id ON beta_testers(user_id);
CREATE INDEX IF NOT EXISTS idx_beta_testers_firebase_uid ON beta_testers(firebase_uid);
CREATE INDEX IF NOT EXISTS idx_beta_testers_action ON beta_testers(action);
CREATE INDEX IF NOT EXISTS idx_beta_testers_timestamp ON beta_testers(timestamp);

-- Create a view for current beta tester status
CREATE OR REPLACE VIEW current_beta_testers AS
SELECT DISTINCT ON (user_id) 
    user_id,
    firebase_uid,
    stripe_customer_id,
    action,
    timestamp,
    github_username,
    firebase_app_distribution_group
FROM beta_testers 
ORDER BY user_id, timestamp DESC;
-- Drop existing table if we need to add new columns
ALTER TABLE beta_testers 
ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'enrolled',
ADD COLUMN IF NOT EXISTS stripe_session_id VARCHAR(100),
ADD COLUMN IF NOT EXISTS stripe_payment_intent_id VARCHAR(100),
ADD COLUMN IF NOT EXISTS oxio_plan_id VARCHAR(100);

-- Create index on status
CREATE INDEX IF NOT EXISTS idx_beta_testers_status ON beta_testers(status);
CREATE TABLE IF NOT EXISTS beta_testers (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    firebase_uid VARCHAR(128) NOT NULL,
    stripe_customer_id VARCHAR(100),
    action VARCHAR(50) DEFAULT 'enrollment_request',
    status VARCHAR(50) DEFAULT 'not_enrolled',
    stripe_session_id VARCHAR(255),
    stripe_payment_intent_id VARCHAR(255),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_beta_testers_user_id ON beta_testers(user_id);
CREATE INDEX IF NOT EXISTS idx_beta_testers_firebase_uid ON beta_testers(firebase_uid);
CREATE INDEX IF NOT EXISTS idx_beta_testers_status ON beta_testers(status);
