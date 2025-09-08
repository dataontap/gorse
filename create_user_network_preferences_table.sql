
CREATE TABLE IF NOT EXISTS user_network_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    stripe_product_id VARCHAR(100) NOT NULL,
    enabled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, stripe_product_id)
);

CREATE INDEX idx_user_network_preferences_user_id ON user_network_preferences(user_id);
CREATE INDEX idx_user_network_preferences_product_id ON user_network_preferences(stripe_product_id);
