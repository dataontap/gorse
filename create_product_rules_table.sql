
CREATE TABLE IF NOT EXISTS product_rules (
    rule_id SERIAL PRIMARY KEY,
    stripe_product_id VARCHAR(100) NOT NULL UNIQUE,
    product_name VARCHAR(255) NOT NULL,
    one_time_charge DECIMAL(10,2) DEFAULT 0.00,
    weekly_charge DECIMAL(10,2) DEFAULT 0.00,
    monthly_charge DECIMAL(10,2) DEFAULT 0.00,
    yearly_charge DECIMAL(10,2) DEFAULT 0.00,
    token_reward_percentage DECIMAL(5,2) DEFAULT 1.00, -- 1% default
    additional_rules TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default product rules
INSERT INTO product_rules (stripe_product_id, product_name, one_time_charge, yearly_charge, token_reward_percentage) VALUES
('global_data_10gb', 'Global Data 10GB', 10.00, 0.00, 1.00),
('basic_membership', 'Basic Membership', 0.00, 24.00, 1.00),
('full_membership', 'Full Membership', 0.00, 66.00, 1.00),
('metal_card', 'DOTM Metal Card', 99.99, 0.00, 1.00)
ON CONFLICT (stripe_product_id) DO NOTHING;

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_product_rules_stripe ON product_rules(stripe_product_id);
