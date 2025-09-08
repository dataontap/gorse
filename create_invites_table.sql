
CREATE TABLE IF NOT EXISTS invites (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    email VARCHAR(255) NOT NULL,
    invitation_status VARCHAR(50) NOT NULL DEFAULT 'invite_sent',
    invited_by_user_id INTEGER,
    invited_by_firebase_uid VARCHAR(128),
    invitation_token VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP + INTERVAL '7 days',
    accepted_at TIMESTAMP,
    rejected_at TIMESTAMP,
    cancelled_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (invited_by_user_id) REFERENCES users(id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_invites_email ON invites(email);
CREATE INDEX IF NOT EXISTS idx_invites_status ON invites(invitation_status);
CREATE INDEX IF NOT EXISTS idx_invites_token ON invites(invitation_token);
CREATE INDEX IF NOT EXISTS idx_invites_user_id ON invites(user_id);
