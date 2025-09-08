
CREATE TABLE IF NOT EXISTS purchases (
    PurchaseID SERIAL PRIMARY KEY,
    StripeID VARCHAR(100),
    StripeProductID VARCHAR(100) NOT NULL,
    PriceID VARCHAR(100) NOT NULL,
    TotalAmount INTEGER NOT NULL,
    DateCreated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UserID INTEGER,
    StripeTransactionID VARCHAR(100),
    FirebaseUID VARCHAR(128)
);

-- Create index on frequently queried fields
CREATE INDEX IF NOT EXISTS idx_purchases_stripe ON purchases(StripeID);
CREATE INDEX IF NOT EXISTS idx_purchases_product ON purchases(StripeProductID);
CREATE INDEX IF NOT EXISTS idx_purchases_user ON purchases(UserID);
CREATE INDEX IF NOT EXISTS idx_purchases_firebase_uid ON purchases(FirebaseUID);
CREATE INDEX IF NOT EXISTS idx_purchases_stripe_transaction ON purchases(StripeTransactionID);
