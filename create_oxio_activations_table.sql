
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

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_oxio_activations_user_id ON oxio_activations(user_id);
CREATE INDEX IF NOT EXISTS idx_oxio_activations_firebase_uid ON oxio_activations(firebase_uid);
CREATE INDEX IF NOT EXISTS idx_oxio_activations_purchase_id ON oxio_activations(purchase_id);
CREATE INDEX IF NOT EXISTS idx_oxio_activations_iccid ON oxio_activations(iccid);
CREATE INDEX IF NOT EXISTS idx_oxio_activations_line_id ON oxio_activations(line_id);
