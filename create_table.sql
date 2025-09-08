
CREATE TABLE IF NOT EXISTS users (
    UserID SERIAL PRIMARY KEY,
    EmailID VARCHAR(255) NOT NULL,
    UserTypeID INTEGER,
    SegmentID INTEGER,
    StatusID INTEGER,
    GroupID INTEGER,
    NetworkID INTEGER,
    IMSI VARCHAR(15),
    MDN VARCHAR(15),
    LineID INTEGER,
    PlanID INTEGER,
    FirebaseID VARCHAR(128),
    AppPushID VARCHAR(255),
    StripeID VARCHAR(100),
    AdTagID VARCHAR(100),
    PrivacyAgentID INTEGER,
    FulfilmentID INTEGER,
    IMEI VARCHAR(20),
    DateCreated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    DateModified TIMESTAMP,
    DateSuspended TIMESTAMP,
    DateClosed TIMESTAMP,
    LastAccessedByID INTEGER
);

-- Create index on frequently queried fields
CREATE INDEX idx_users_email ON users(EmailID);
CREATE INDEX idx_users_imei ON users(IMEI);
CREATE INDEX idx_users_stripe ON users(StripeID);
