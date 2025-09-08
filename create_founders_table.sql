
-- Create founders table to track founding member status
CREATE TABLE IF NOT EXISTS founders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    firebase_uid VARCHAR(128) UNIQUE NOT NULL,
    founder VARCHAR(1) NOT NULL DEFAULT 'Y' CHECK (founder IN ('Y', 'N')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_founders_user_id ON founders(user_id);
CREATE INDEX IF NOT EXISTS idx_founders_firebase_uid ON founders(firebase_uid);
CREATE INDEX IF NOT EXISTS idx_founders_founder_status ON founders(founder);

-- Create a view for easy access to user founder status
CREATE OR REPLACE VIEW user_founder_status AS
SELECT 
    u.id as user_id,
    u.email,
    u.firebase_uid,
    u.display_name,
    COALESCE(f.founder, 'N') as founder_status,
    f.created_at as founder_since
FROM users u
LEFT JOIN founders f ON u.firebase_uid = f.firebase_uid;
