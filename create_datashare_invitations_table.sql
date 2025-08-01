
CREATE TABLE IF NOT EXISTS datashare_invitations (
    id SERIAL PRIMARY KEY,
    group_owner_id INTEGER NOT NULL,
    group_owner_firebase_uid VARCHAR(128) NOT NULL,
    group_name VARCHAR(255) NOT NULL,
    invited_email VARCHAR(255) NOT NULL,
    invited_name VARCHAR(255),
    invitation_status VARCHAR(50) DEFAULT 'invite_sent',
    is_demo_user BOOLEAN DEFAULT FALSE,
    personal_message TEXT,
    invitation_token VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    accepted_at TIMESTAMP,
    rejected_at TIMESTAMP,
    FOREIGN KEY (group_owner_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_datashare_invitations_owner ON datashare_invitations(group_owner_firebase_uid);
CREATE INDEX IF NOT EXISTS idx_datashare_invitations_email ON datashare_invitations(invited_email);
CREATE INDEX IF NOT EXISTS idx_datashare_invitations_status ON datashare_invitations(invitation_status);
