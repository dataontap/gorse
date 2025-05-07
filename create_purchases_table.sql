
CREATE TABLE IF NOT EXISTS purchases (
    PurchaseID SERIAL PRIMARY KEY,
    StripeID VARCHAR(100) NOT NULL,
    StripeProductID VARCHAR(100) NOT NULL,
    PriceID VARCHAR(100) NOT NULL,
    TotalAmount INTEGER NOT NULL,
    DateCreated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UserID INTEGER,
    FOREIGN KEY (UserID) REFERENCES users(UserID)
);

-- Create index on frequently queried fields
CREATE INDEX idx_purchases_stripe ON purchases(StripeID);
CREATE INDEX idx_purchases_product ON purchases(StripeProductID);
