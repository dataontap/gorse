# 🌐 GORSE Platform API Documentation

GLOBAL DATA

## 📚 Documentation Links

- **Interactive API Docs**: [Swagger UI](/api)
- **Platform Documentation**: [/docs](/docs)
- **GitHub Repository**: [dataontap/gorse](https://github.com/dataontap/gorse)
- **Live API**: [https://get-dot-esim.replit.app/api/](https://get-dot-esim.replit.app/api/)

## 🚀 Quick Start

1. **Authentication**: Set up Firebase Authentication
2. **Register User**: POST `/api/auth/register` with Firebase UID
3. **Make API Calls**: Include `firebaseUid` parameter
4. **Check Status**: Use debug endpoints for troubleshooting

## 📋 Key Endpoints

### User Management
- `POST /api/auth/register` - Register Firebase user
- `GET /api/auth/current-user` - Get user profile
- `GET /api/user/data-balance` - Check data balance

### OXIO Integration
- `GET /api/oxio/test-connection` - Test OXIO connectivity
- `POST /api/oxio/activate-line` - Activate eSIM line
- `GET /api/oxio-user-data` - Get user's OXIO profile

### Marketplace
- `POST /api/record-global-purchase` - Purchase data/memberships
- `GET /api/subscription-status` - Check subscription status

### Network Features
- `GET /api/network-features/{firebaseUid}` - Get feature status
- `PUT /api/network-features/{firebaseUid}/{productId}` - Toggle features

## 🔧 Environment Variables

```bash
FIREBASE_ADMIN_KEY=your_firebase_key
STRIPE_SECRET_KEY=sk_test_...
OXIO_API_KEY=your_oxio_key
OXIO_AUTH_TOKEN=your_oxio_token
DATABASE_URL=postgresql://...
```

## 📱 Platform Features

- **Global Connectivity**: 160+ countries eSIM coverage
- **Canadian MVNO**: Network 302 100 enterprise service  
- **Token Integration**: DOTM cryptocurrency rewards
- **Payment Processing**: Stripe subscriptions and purchases
- **Real-time APIs**: Live data usage and network monitoring

## 🔗 Integration Examples

### JavaScript/Node.js
```javascript
// Register user
const response = await fetch('/api/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        firebaseUid: 'user_uid',
        email: 'user@example.com'
    })
});

// Check data balance
const balance = await fetch(`/api/user/data-balance?firebaseUid=${uid}`);
const data = await balance.json();
console.log(`Balance: ${data.dataBalance} GB`);
```

### Python
```python
import requests

# Purchase data plan
response = requests.post('/api/record-global-purchase', json={
    'productId': 'global_data_10gb',
    'firebaseUid': 'user_uid'
})
print(f"Purchase result: {response.json()}")
```

## 📊 Monitoring & Debug

- `/db-test` - Database connection status
- `/api/debug/user-creation-status/{firebaseUid}` - User system verification
- `/token-price-pings` - Token price history
- `/api/debug/recent-purchases` - Purchase debugging

## 🆘 Support

- **Help Desk**: [/help-admin](/help-admin)
- **Contact**: [/message-admin](/message-admin)
- **Status**: Monitor all services via debug endpoints

## 📄 Files

- `index.html` - Interactive Swagger UI documentation
- `openapi.json` - OpenAPI 3.0 specification
- `README.md` - This comprehensive guide

## 🏗️ Architecture

Built on Flask with:
- Firebase Authentication
- PostgreSQL database  
- Stripe payments
- OXIO eSIM integration
- Ethereum blockchain integration

## 📅 Version
API Version: 3.0
Platform: GORSE (Global Optimized Roaming Service Engine)
