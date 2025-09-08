
-- Create data usage log table for tracking actual consumption
CREATE TABLE IF NOT EXISTS data_usage_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    stripe_customer_id VARCHAR(100) NOT NULL,
    megabytes_used DECIMAL(10,2) NOT NULL,
    stripe_event_id VARCHAR(255),
    session_id VARCHAR(255),
    device_info TEXT,
    location_info TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_data_usage_user ON data_usage_log(user_id);
CREATE INDEX IF NOT EXISTS idx_data_usage_customer ON data_usage_log(stripe_customer_id);
CREATE INDEX IF NOT EXISTS idx_data_usage_date ON data_usage_log(created_at);

-- Create a view for easy usage summary queries
CREATE OR REPLACE VIEW user_usage_summary AS
SELECT 
    u.id as user_id,
    u.email,
    u.stripe_customer_id,
    SUM(dul.megabytes_used) as total_mb_used,
    COUNT(dul.id) as usage_sessions,
    MAX(dul.created_at) as last_usage,
    DATE_TRUNC('month', dul.created_at) as usage_month
FROM users u
LEFT JOIN data_usage_log dul ON u.id = dul.user_id
GROUP BY u.id, u.email, u.stripe_customer_id, DATE_TRUNC('month', dul.created_at)
ORDER BY usage_month DESC;
