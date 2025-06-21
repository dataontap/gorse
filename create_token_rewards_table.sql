
CREATE TABLE IF NOT EXISTS token_rewards (
    id SERIAL PRIMARY KEY,
    purchase_id INTEGER,
    user_id INTEGER NOT NULL,
    eth_address VARCHAR(42) NOT NULL,
    amount_cents INTEGER NOT NULL,
    token_amount DECIMAL(18,9) NOT NULL,
    tx_hash VARCHAR(66),
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_token_rewards_user ON token_rewards(user_id);
CREATE INDEX IF NOT EXISTS idx_token_rewards_eth_address ON token_rewards(eth_address);
CREATE INDEX IF NOT EXISTS idx_token_rewards_purchase ON token_rewards(purchase_id);
CREATE INDEX IF NOT EXISTS idx_token_rewards_tx_hash ON token_rewards(tx_hash);
