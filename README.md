# dot. - DOT GLOBAL CONNECTIVITY

A comprehensive Flask-based API platform providing global eSIM connectivity, token management, and network services.

## Features

- **Firebase Authentication**: Secure user authentication and management
- **OXIO eSIM Integration**: Global eSIM activation and connectivity services  
- **Stripe Payments**: Subscription and marketplace payment processing
- **DOTM Token System**: Blockchain token rewards and management
- **Network Features**: Configurable network optimization and security
- **Beta Program**: eSIM testing and activation for beta users
- **Real-time Notifications**: FCM push notifications and WebSocket support

## API Documentation

- **Swagger UI**: [https://get-dot-esim.replit.app/api/](https://get-dot-esim.replit.app/api/)
- **Static Docs**: [https://get-dot-esim.replit.app/api/export-docs](https://get-dot-esim.replit.app/api/export-docs)
- **GORSE Docs**: [https://gorse.dotmobile.app/api/](https://gorse.dotmobile.app/api/)

## Quick Start

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables (see .env.example)
4. Run the application: `python main.py`

## Environment Variables

```
DATABASE_URL=postgresql://...
STRIPE_SECRET_KEY=sk_...
FIREBASE_ADMIN_SDK={"type": "service_account"...}
OXIO_API_KEY=...
OXIO_AUTH_TOKEN=...
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register Firebase user
- `GET /api/auth/current-user` - Get current user data
- `POST /api/auth/update-imei` - Update user IMEI

### OXIO eSIM Services  
- `GET /api/oxio/test-connection` - Test OXIO API connection
- `POST /api/oxio/activate-line` - Activate eSIM line
- `GET /api/oxio-user-data` - Get user OXIO data

### Payments & Subscriptions
- `POST /api/record-global-purchase` - Record marketplace purchase
- `GET /api/subscription-status` - Get user subscription status
- `GET /api/user/data-balance` - Get user data balance

### DOTM Tokens
- `GET /api/token/price` - Get current token price
- `GET /api/token/balance/<address>` - Get token balance
- `POST /api/token/founding-token` - Assign founding member token

### Network Features
- `GET /api/network-features/<firebase_uid>` - Get user network features
- `PUT /api/network-features/<firebase_uid>/<product_id>` - Toggle network feature

## Technology Stack

- **Backend**: Flask, Flask-RESTX, Flask-SocketIO
- **Database**: PostgreSQL with psycopg2
- **Authentication**: Firebase Admin SDK
- **Payments**: Stripe API
- **Blockchain**: Web3.py for Ethereum integration
- **eSIM**: OXIO API integration
- **Real-time**: WebSocket with SocketIO

## License

Proprietary - DOT Mobile Inc.

## Support

For API support, contact: api@dotmobile.app