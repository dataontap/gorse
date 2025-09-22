# eSIM Activation System Documentation

## Overview

The DOTM Platform implements a complete eSIM activation system that integrates three main services:
- **Stripe** for payment processing
- **OXIO** for eSIM provisioning and activation
- **Resend** for professional email delivery

This system provides users with instant global connectivity through eSIM technology.

## System Architecture

```
User Payment → Stripe Checkout → Webhook → eSIM Activation Service → OXIO API → Email Notification
```

### Key Components

1. **Payment Processing** (Stripe)
2. **eSIM Provisioning** (OXIO)
3. **Email Notifications** (Resend)
4. **Database Storage** (PostgreSQL)
5. **Webhook Processing** (Stripe Events)

---

## API Integrations

### 1. Stripe Payment API

**Purpose**: Handle secure payments and subscription management

**Key Features**:
- One-time purchases (Global Data, Metal Card)
- Annual subscriptions (Basic/Full Membership)
- Beta testing payments ($1 eSIM access)
- Automatic webhook notifications

**Configuration**:
```python
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
```

**Products Created**:
- `global_data_10gb` - $20.00 (10GB global data)
- `basic_membership` - $24.00/year
- `full_membership` - $66.00/year
- `esim_beta` - $1.00 (beta access)
- `metal_card` - $99.99

### 2. OXIO Network API

**Purpose**: Provision and activate eSIM profiles globally

**Base URL**: `https://api-staging.brandvno.com`

**Authentication**: Basic Auth (API Key + Auth Token)

**Key Endpoints**:
- `POST /v2/end-users` - Create OXIO user
- `POST /v2/groups` - Create user groups
- `POST /v3/lines/line` - Activate eSIM line

**Configuration**:
```python
headers = {
    'Authorization': f'Basic {base64_credentials}',
    'Content-Type': 'application/json'
}

# Brand ID retrieved from environment variables
brand_id = os.environ.get('OXIO_BRAND_ID')
```

### 3. Resend Email API

**Purpose**: Send professional transactional emails

**Features**:
- 99.9% delivery rate
- HTML email templates
- Domain authentication (@dotmobile.app)
- Delivery tracking

**Configuration**:
```python
resend.api_key = os.environ.get('RESEND_API_KEY')
```

---

## eSIM Activation Flow

### 1. Payment Processing

```python
@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    # Create Stripe checkout session
    # Handle different product types
    # Return checkout URL
```

**Process**:
1. User selects product (Global Data, Membership, etc.)
2. System creates Stripe checkout session
3. User completes payment
4. Stripe sends webhook notification

### 2. Webhook Processing

```python
@app.route('/stripe/webhook/<webhook_secret>', methods=['POST'])
def handle_stripe_webhook():
    # Verify webhook signature
    # Process payment events
    # Trigger eSIM activation
```

**Key Events**:
- `checkout.session.completed` - Payment successful
- `payment_intent.succeeded` - Payment confirmed
- `invoice.payment_succeeded` - Subscription payment

### 3. eSIM Activation Service

Located in `esim_activation_service.py`, this service orchestrates the complete activation workflow:

```python
def activate_esim_after_payment(firebase_uid, user_email, user_name, stripe_session_id, purchase_amount):
    # 1. Get or create user data
    # 2. Ensure OXIO user exists
    # 3. Activate eSIM line
    # 4. Process activation data
    # 5. Store activation record
    # 6. Award DOTM tokens
    # 7. Send confirmation email
```

### 4. OXIO Integration Steps

#### Step 1: Create OXIO User
```python
def create_oxio_user(first_name, last_name, email, firebase_uid):
    payload = {
        "sex": "UNSPECIFIED",
        "firstName": first_name,
        "lastName": last_name,
        "email": email
    }
    # POST to /v2/end-users
```

#### Step 2: Activate eSIM Line
```python
def activate_line(oxio_user_id, plan_id, group_id):
    payload = {
        "lineType": "LINE_TYPE_MOBILITY",
        "countryCode": "US",
        "sim": {"simType": "EMBEDDED"},
        "endUser": {
            "brandId": os.environ.get('OXIO_BRAND_ID'),  # Retrieved from secrets
            "endUserId": oxio_user_id
        },
        "activateOnAttach": False
    }
    # POST to /v3/lines/line
```

### 5. Data Processing and Storage

**Database Tables**:
- `users` - User profiles and OXIO mappings
- `oxio_activations` - eSIM activation records
- `purchases` - Payment transactions
- `subscriptions` - Membership subscriptions

**Activation Record**:
```sql
CREATE TABLE oxio_activations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    firebase_uid VARCHAR(128),
    purchase_id VARCHAR(200),
    iccid VARCHAR(50),
    line_id VARCHAR(100),
    phone_number VARCHAR(20),
    activation_status VARCHAR(50),
    esim_qr_code TEXT,
    activation_url VARCHAR(500),
    oxio_response TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 6. Email Notification

The system sends comprehensive activation emails with:
- eSIM profile details
- Phone number assignment
- QR code for activation
- Setup instructions
- Support contact information

---

## API Endpoints

### User-Facing Endpoints

#### Purchase Endpoints
```
POST /create-checkout-session
- Creates Stripe checkout session
- Body: { productId, firebaseUid, email }
- Returns: { checkout_url, session_id }

GET /esim/success
- Payment success page
- Displays activation progress
```

#### Status Endpoints
```
GET /api/subscription-status?firebaseUid={uid}
- Returns user subscription status
- Response: { status, type, end_date }

GET /api/user-esim-details?firebaseUid={uid}
- Returns eSIM activation details
- Response: { activations[], phone_numbers[] }

GET /api/oxio-activation-status?firebaseUid={uid}
- Returns OXIO activation status
- Response: { success, activations[] }
```

### Admin Endpoints

```
POST /api/test-esim-activation
- Test activation service
- Body: { firebaseUid, email, name }

POST /api/create-oxio-user
- Manually create OXIO user
- Body: { firebaseUid, email, firstName, lastName }

POST /api/fix-user-oxio-data
- Fix user OXIO mappings
- Body: { firebaseUid }
```

### OXIO Testing Endpoints

```
GET /api/oxio/test-connection
- Test OXIO API credentials

GET /api/oxio/test-plans
- Test OXIO plans endpoint

POST /api/oxio/activate-line
- Test line activation
- Body: { activation_payload }

POST /api/oxio/test-sample-activation
- Test with sample payload
```

---

## Webhook Services

### Stripe Webhook Handler

**URL**: `/stripe/webhook/7f3a9b2c8d1e4f5a6b7c8d9e0f1a2b3c`

**Security**: Webhook signature verification

**Processed Events**:
- `checkout.session.completed`
- `payment_intent.succeeded`
- `customer.subscription.created`
- `invoice.payment_succeeded`

**Event Processing**:
```python
def handle_stripe_webhook():
    # 1. Verify webhook signature
    sig_header = request.headers.get('Stripe-Signature')

    # 2. Parse event
    event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)

    # 3. Process based on event type
    if event['type'] == 'checkout.session.completed':
        # Trigger eSIM activation
        activate_esim_for_checkout(session)
```

### Firebase Security & Integration

**Authentication Security**:
```python
from firebase_helper import firebase_auth_required

@app.route('/api/secure-endpoint')
@firebase_auth_required
def secure_endpoint():
    # Firebase ID token is verified automatically
    # User UID is available in request.firebase_user
    pass
```

**Database Integration**:
- All users have `firebase_uid` as unique identifier
- Firebase UID links to OXIO user accounts
- Stripe customers associated via Firebase UID
- FCM tokens mapped to Firebase users

**User Data Security**:
```python
# SECURITY: Always clear localStorage on user switch
localStorage.clear()  # Prevents user data mixing

# Verify Firebase UID exists in database
def verify_firebase_uid(firebase_uid: str) -> bool:
    with get_db_connection() as conn:
        cur.execute("SELECT id FROM users WHERE firebase_uid = %s", (firebase_uid,))
        return cur.fetchone() is not None
```

**Real-time State Management**:
```javascript
// Firebase authentication state listener
firebase.auth().onAuthStateChanged(async function(user) {
    if (user) {
        // Load user data and register FCM token
        await loadUserData(user);
        registerFCMToken();

        // Broadcast auth state change
        broadcastAuthStateChange(user, userData);
    } else {
        // Clear all local storage and notify components
        localStorage.clear();
        broadcastAuthStateChange(null, null);
    }
});
```

---

## Key Data Requirements

### User Data
- `firebase_uid` - Unique user identifier
- `email` - Contact and OXIO account creation
- `display_name` - User personalization
- `oxio_user_id` - OXIO account mapping
- `eth_address` - Token rewards

### OXIO Data
- `endUserId` - OXIO user identifier
- `lineId` - Activated line identifier
- `phoneNumber` - Assigned phone number
- `iccid` - eSIM card identifier
- `activationUrl` - eSIM download link

### Stripe Data
- `session_id` - Checkout session
- `payment_intent` - Payment confirmation
- `customer_id` - Stripe customer
- `product_id` - Purchased product
- `amount_paid` - Transaction amount

---

## Error Handling

### Common Issues

1. **OXIO User Creation Fails**
   - Retry with different payload
   - Check email uniqueness
   - Fallback to manual creation

2. **Line Activation Fails**
   - Verify OXIO user exists
   - Check plan availability
   - Retry with clean payload

3. **Email Delivery Fails**
   - Resend primary service
   - SMTP fallback available
   - Admin notification system

### Monitoring

The system includes comprehensive logging:
- All OXIO API calls with request/response
- Stripe webhook processing
- Email delivery status
- Database operation results

---

## Configuration

### Required Environment Variables

```bash
# Stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# OXIO
OXIO_API_KEY=your_api_key
OXIO_AUTH_TOKEN=your_auth_token
OXIO_BRAND_ID=your_brand_id

# Resend
RESEND_API_KEY=re_...
FROM_EMAIL=noreply@dotmobile.app

# Database
DATABASE_URL=postgresql://...

# Firebase
FIREBASE_CREDENTIALS=path/to/serviceAccount.json
```

### Product Configuration

Products are automatically created via `stripe_products.py`:
- Global Data: $20 for 10GB
- Basic Membership: $24/year
- Full Membership: $66/year
- eSIM Beta: $1 for testing
- Metal Card: $99.99

---

## Testing

### Test Endpoints

Access testing interface at `/oxio-test`:
- Connection testing
- Sample activations
- Custom payload testing
- Real-time response monitoring

### Test Activation

```python
# Test the complete activation flow
POST /api/test-esim-activation
{
    "firebaseUid": "test_uid_123",
    "email": "test@example.com", 
    "name": "Test User"
}
```

---

## Security Considerations

1. **Webhook Verification**: All Stripe webhooks verified with signatures
2. **API Authentication**: OXIO API uses secure Basic Auth
3. **Data Encryption**: All sensitive data encrypted in transit
4. **Rate Limiting**: API abuse protection implemented
5. **Input Validation**: All user inputs sanitized

---

## Monitoring and Analytics

### Key Metrics
- Activation success rate
- Average activation time
- Email delivery rate
- Payment processing time
- OXIO API response times

### Logging
- Complete request/response logging for OXIO
- Stripe event processing logs
- Email delivery confirmations
- Error tracking and alerting

This documentation provides a complete overview of the eSIM activation system implementation, covering all aspects from payment processing to final user notification.