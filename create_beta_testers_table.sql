
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
