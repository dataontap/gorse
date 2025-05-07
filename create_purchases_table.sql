
CREATE TABLE IF NOT EXISTS purchases (
    PurchaseID SERIAL PRIMARY KEY,
    TransactionID VARCHAR(100) UNIQUE,
    StripeID VARCHAR(100) NOT NULL,
    StripeProductID VARCHAR(100) NOT NULL,
    PriceID VARCHAR(100) NOT NULL,
    TotalAmount INTEGER NOT NULL,
    DateCreated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UserID INTEGER
);

-- Create index on frequently queried fields
CREATE INDEX IF NOT EXISTS idx_purchases_stripe ON purchases(StripeID);
CREATE INDEX IF NOT EXISTS idx_purchases_product ON purchases(StripeProductID);
CREATE INDEX IF NOT EXISTS idx_purchases_transaction ON purchases(TransactionID);
