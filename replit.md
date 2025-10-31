# DOTM Platform

## Overview

The DOTM Platform is a telecommunications service platform that integrates global eSIM connectivity, cryptocurrency rewards, and network optimization. It merges traditional mobile services with blockchain technology, leveraging OXIO's infrastructure for global data and incorporating DOTM token rewards. Firebase is used for user management, and a Model Context Protocol (MCP) server enables AI assistant integration. The platform offers extensive API services and a multi-layered architecture to support features ranging from basic connectivity to advanced network management. Its business vision is to innovate mobile services through Web3 technologies, providing a unique offering in the telecommunications market.

## Admin Portal Access

The platform includes a secure admin portal accessible only to the platform owner (aa@dotmobile.app). Access is provided through two methods:

1. **Direct Login on Admin Page**: Navigate to `/admin` to access a dedicated login form. When not authenticated, the page displays a login interface instead of redirecting, allowing direct sign-in with owner credentials.

2. **Profile Page Button**: When logged in as the owner, a prominent "∞ Admin Portal" button appears on the profile page, providing quick access to the admin dashboard. This button features an infinity symbol (∞) and is styled with a gradient purple design for easy identification.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture

The core application is built with Flask, utilizing Flask-RESTX for API documentation and Flask-SocketIO for real-time communication. It uses a PostgreSQL database with connection pooling and a modular, service-oriented design. A device tracking system dynamically detects, registers, and tracks user devices, displaying their status in the Marketplace.

### Authentication & User Management

Firebase handles user authentication via the Admin SDK for server-side token verification, with `firebaseAuthStateChanged` ensuring authentication state consistency. The system employs a dual identity approach, linking Firebase UIDs with internal database IDs and OXIO user IDs.

### Payment & Billing Architecture

Stripe is integrated for subscription management, one-time purchases, and product catalog management, supporting dynamic pricing and multi-currency transactions. All purchases are recorded in the Purchases table via Stripe webhooks and displayed in the Dashboard.

### Connectivity Services

Deep integration with OXIO's API facilitates eSIM provisioning, data management, and network services. The OXIO API base URL is now configurable via the `OXIO_ENVIRONMENT` secret (currently set to `https://api-staging.brandvno.com` for staging). To switch to production, simply update the secret to `https://api.brandvno.com`. The platform also offers configurable network features such as VPN, security enhancements, and communication services (VoLTE, Wi-Fi calling).

**Phone Number Management**: Users can search and select phone numbers through the profile page using two methods:
- ZIP code search: Find available numbers in specific geographic areas
- NPA NXX search: Search by area code (NPA) and exchange (NXX) - the first 6 digits of a phone number

The system tracks all number change requests in the `phone_number_changes` table, recording search parameters, selected numbers, status workflow (pending, approved, completed, failed), and OXIO API interactions. Four dedicated API endpoints handle number lookup operations, propagating proper HTTP status codes from OXIO's upstream responses.

### Blockchain Integration

Web3.py integrates Ethereum smart contracts for DOTM token management on Sepolia testnet and mainnet, including an automated token reward system based on service usage.

**Wallet Management Features**: The payments page provides comprehensive wallet details through an expandable interface:
- Real-time DOTM token balance synchronization with Sepolia testnet via `/api/token/balance/me` endpoint
- Expandable "Wallet Details" button replacing the previous USD value display
- Detailed wallet information including:
  - Ethereum address (shortened format with full address stored for copy)
  - Wallet creation date (formatted from database `created_at` field)
  - Direct Etherscan link to view wallet on Sepolia testnet
  - QR code generation for easy address sharing (via QR Server API)
  - One-click address copy to clipboard with visual feedback
- Differentiated member benefits: "Founding Member Benefits" (crown icon) vs "Member Benefits" (star icon) based on `/api/founder-status` endpoint
- Full dark mode support for all wallet UI components

**Transaction History**: The "Recent Transactions" section displays a combined view of blockchain transfers and platform purchases:
- `/api/token/transactions` endpoint combines:
  - Blockchain token transfers from Ethereum Mainnet via Etherscan API
  - Platform purchases from database
- Displays as IN (↓) or OUT (↑) transactions with token amounts and USD values
- Shows last 5 transactions by default with "Show More" button to load all
- Clickable transactions open detailed modal with:
  - Full transaction details (hash, from, to, timestamp, value)
  - Direct Etherscan link for blockchain transactions
  - Network identification (Mainnet vs Stripe Payment)
- Network badge displays "Mainnet" for blockchain transactions
- Gracefully handles users without database records (new signups)

### MCP Server Architecture

A dedicated MCP server provides AI assistants with structured access to service information, pricing data, and feature catalogs through multi-format API endpoints (JSON and HTML), while maintaining strict privacy controls. It includes AI-driven eSIM activation workflows, automatically generating Stripe invoices if payment is not found, and implementing rate limiting (100 activations/hour with queue management).

### UI/UX Decisions

The user profile page is designed to display eSIM information and phone numbers clearly. API responses are formatted to match frontend expectations, including specific field mappings and JSON structures with success flags.

**Progressive Personalized Messaging**: The platform delivers evolving personalized audio messages based on user login patterns:

*First Login - Welcome Message* (`/api/message/get-current`):
- Location-aware greeting with IP-based city, region, and country detection via IP-API.com (free, no API key)
- Local time calculation from timezone data with time-of-day context (morning, afternoon, evening, night)
- Real-time contextual information via Gemini API with Google Search grounding:
  - Current weather conditions in user's location
  - Traffic and transportation updates
  - Today's events and activities happening locally
- ISP recognition contextualizing network insights available before membership purchase
- Personalized with user's join date from database
- All contextual data stored as permanent acquisition records in database
- Message starts with: "Welcome to our community. We are building the connectivity network of the future for Canadians anywhere,"

*Second Login - Tip Message*:
- Platform usage tips and feature discovery
- Best practices for network optimization
- No location/events data (focused on actionable tips)

*Third Login - Update Message*:
- Platform news and new feature announcements
- Service improvements and community updates
- No location/events data (focused on platform updates)

*Subsequent Logins*:
- Returns the most recently played message for replay
- Messages cached indefinitely for user convenience

**Technical Implementation**:
- `/api/message/get-current` endpoint determines which message to serve based on `user_message_history` table
- `/api/welcome-message/generate` endpoint generates new messages (accepts `message_type` parameter: welcome, tip, update)
- All audio cached in `welcome_messages` table with:
  - `language` and `voice_profile` keys for audio generation
  - `location_context` JSONB field storing comprehensive acquisition data (location, time, weather, traffic, events)
  - `generated_at_local_time` timestamp in user's timezone
- ElevenLabs text-to-speech with 30+ language support and custom voice profiles
- Gemini API with grounding for real-time Google Search results (weather, traffic, events)
- Location service extracts timezone and calculates local time with time-of-day classification
- Response headers include: `X-Message-Type`, `X-Is-New`, `X-Location`, `X-Local-Time`, `X-Has-Context`

### Data Privacy & Security

The platform isolates public service information from sensitive user and transaction data. All sensitive credentials are managed through environment variables.

## External Dependencies

### Core Infrastructure Services

-   **OXIO API Platform**: Provides global eSIM and data services via its staging API.
-   **Firebase Authentication**: Google Firebase for user authentication and identity management.
-   **Stripe Payment Processing**: For subscriptions, product catalogs, and webhooks.

### Communication & AI Services

-   **ElevenLabs Voice Synthesis**: Provides advanced text-to-speech services with multilingual support and custom voice profiles.
-   **Google Gemini API**: AI-powered contextual information with Google Search grounding for real-time weather, traffic, and events data.
-   **OpenAI Integration**: For AI-powered help desk and automated customer support.
-   **SMTP Email Services**: For transactional emails and notifications.
-   **IP-API.com**: Free IP geolocation, ISP detection, and timezone service for personalized welcome messages.

### Blockchain & Web3

-   **Ethereum Network**: Supports Web3 integration on Sepolia testnet and Ethereum mainnet.
-   **DOTM Smart Contract**: Custom ERC-20 token contract.

### Development & Deployment Tools

-   **PostgreSQL Database**: Primary data storage.
-   **Hardhat Development Framework**: For Ethereum smart contract development.
-   **GitHub Integration**: For source code management.
-   **Jira Integration**: For customer support ticketing.
-   **Shopify Integration**: For marketplace product management via Shopify Admin API.