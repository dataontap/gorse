
-- Add unique constraint to prevent multiple activations per user
-- This provides database-level protection against duplicates

ALTER TABLE oxio_activations 
ADD CONSTRAINT unique_user_activation 
UNIQUE (user_id);

-- Also add constraint for Firebase UID as backup
ALTER TABLE oxio_activations 
ADD CONSTRAINT unique_firebase_uid_activation 
UNIQUE (firebase_uid);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_oxio_activations_user_id ON oxio_activations(user_id);
CREATE INDEX IF NOT EXISTS idx_oxio_activations_firebase_uid ON oxio_activations(firebase_uid);
