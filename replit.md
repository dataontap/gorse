# DOTM Platform

## Overview

The DOTM Platform is a comprehensive telecommunications service platform offering global eSIM connectivity, cryptocurrency rewards, and network optimization. It bridges traditional mobile services with blockchain technology, providing global data through OXIO's infrastructure, integrating DOTM token rewards, and utilizing Firebase for user management. The platform includes a Model Context Protocol (MCP) server for AI assistant integration, extensive API services, and a multi-layered architecture supporting various features from basic connectivity to advanced network management. Its business vision is to revolutionize mobile services by incorporating Web3 technologies, offering a unique value proposition in the telecommunications market.

## Recent Changes

### October 22, 2025 - Repository Cleanup & Deployment Automation

**Milestone: Automated Repository Cleanup System**

Implemented comprehensive cleanup system that automatically removes screenshots and temporary files from the repository before every GitHub push.

**Key Features:**
1. ✅ Created automated cleanup script (`scripts/cleanup-repo.sh`)
2. ✅ Removed 849 files (171MB) of screenshots and temporary assets
3. ✅ Updated .gitignore to prevent future commits of development files
4. ✅ Integrated cleanup into `scripts/push-to-github.sh` workflow
5. ✅ Added cleanup step to GitHub Actions workflow
6. ✅ Safe mode excludes system directories (.git, .cache, .config)

**Files Automatically Removed:**
- Screenshots from attached_assets/ directory
- Temporary images and photos
- Backup files (*.tmp, *~, *.bak)
- Empty directories

**Integration Points:**
- Local push script runs cleanup before git operations
- GitHub Actions workflow includes cleanup step
- .gitignore prevents future commits of development assets

**Files Created:**
- `scripts/cleanup-repo.sh`: Automated cleanup script
- `CLEANUP_SYSTEM.md`: Complete documentation
- Updated `.gitignore`: Added development asset patterns
- Updated `.github/workflows/auto-push.yml`: Added cleanup step
- Updated `scripts/push-to-github.sh`: Integrated cleanup

### October 22, 2025 - AI-Driven eSIM Activation via MCP v2 Server

**Milestone: ChatGPT & Gemini Integration for eSIM Activation**

Successfully implemented complete AI-driven eSIM activation workflow using Model Context Protocol (MCP) v2, enabling users to activate eSIMs by simply asking ChatGPT or Gemini AI.

**Key Features Implemented:**
1. ✅ Fixed MCP v2 server integration - resolved `_tool_manager` attribute error
2. ✅ Added `activate_esim` tool with **automatic Stripe invoice generation**
3. ✅ Integrated OXIO activation workflow for AI-driven provisioning
4. ✅ Created comprehensive test suites for ChatGPT (6 tests) and Gemini (7 tests)
5. ✅ Implemented end-to-end invoice → payment → activation flow validation
6. ✅ **Added rate limiting: 100 activations/hour with queue management**
7. ✅ **Verified invocation phrases: "Global Data eSIM" and "DOT eSIM"**

**Technical Architecture:**
- **MCP v2 Endpoint:** `/mcp/v2/messages` (JSON-RPC 2.0)
- **Auto-Registration:** Automatically creates new users from ChatGPT/Gemini with their email
- **Payment Verification:** Queries `purchases` table for `esim_beta` product ($1)
- **Automatic Invoicing:** Creates and sends Stripe invoices when payment not found
- **Security:** Firebase authentication + email verification + Stripe payment check
- **Integration:** Reuses existing `activate_esim_for_user()` and OXIO API
- **Tools Available:** 5 total (calculate_pricing, search_services, get_service_details, compare_memberships, activate_esim)

**User Flow:**
1. User tells AI: "I want to activate my eSIM"
2. AI authenticates with Firebase Bearer token
3. AI calls MCP server's `activate_esim` tool
4. **If no payment:** Server automatically creates and sends Stripe invoice to user's email
5. User pays $1 invoice via Stripe email link
6. Stripe webhook records purchase in database
7. User tells AI: "I paid the invoice"
8. AI calls `activate_esim` again - payment now verified ✅
9. Server activates eSIM via OXIO integration
10. User receives email with QR code and phone number
11. AI explains activation details to user

**Files Updated:**
- `mcp_server_v2.py`: Added activate_esim tool with payment verification + rate limiting
- `mcp_rate_limiter.py`: Rate limiting module (100/hour, queue management, ETA estimation)
- `main.py`: Fixed MCP v2 messages endpoint handler integration
- `tests/test_mcp_chatgpt_esim.py`: ChatGPT integration test suite
- `tests/test_mcp_gemini_esim.py`: Gemini AI integration test suite
- `tests/test_invocation_phrases.py`: Tests for "Global Data eSIM" and "DOT eSIM" phrases
- `tests/test_end_to_end_esim_activation.py`: Complete workflow testing
- `MCP_V2_ESIM_ACTIVATION_GUIDE.md`: Comprehensive integration guide
- `INVOCATION_PHRASES_GUIDE.md`: Discovery phrase documentation and rate limiting

**Testing Results:**
- ✅ MCP server health check passing
- ✅ Connection initialization working
- ✅ activate_esim tool properly exposed
- ✅ Payment verification logic confirmed
- ✅ User validation logic confirmed
- ✅ Integration with existing OXIO workflow verified

### October 21, 2025 - User Profile eSIM Display Fixed

**Milestone: Complete User Profile eSIM Integration**

Successfully restored and fixed the user profile page to properly display eSIM information and phone numbers.

**Key Fixes Completed:**
1. ✅ Fixed critical Flask server crash caused by duplicate MCP server route definitions
2. ✅ Corrected network services API to display proper service names and valid expiry dates (was showing "undefined" and "31/12/1969")
3. ✅ Created `/api/user-phone-numbers` endpoint to retrieve user eSIM and phone number data
4. ✅ Fixed API response format to match frontend expectations:
   - Returns `phone_numbers` array (not single object)
   - Field mapping: `activation_code` → `lpa_code`, `created_at` → `activated_at`
   - Proper JSON structure with success flag

**Database Schema:**
- User activation data stored in `oxio_activations` table
- Key fields: `firebase_uid`, `phone_number`, `iccid`, `activation_code`, `esim_qr_code`, `activation_status`, `created_at`

**Technical Notes:**
- Frontend expects arrays wrapped in descriptive keys (e.g., `phone_numbers` array)
- API response formats must exactly match frontend expectations for proper rendering
- Firebase UID is used as the primary key for user lookups across systems

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture

The core application uses Flask with Flask-RESTX for API documentation and Flask-SocketIO for real-time communication. It employs a PostgreSQL database with connection pooling and a modular, service-oriented design. A device tracking system automatically detects, registers, and tracks user devices, displaying their status dynamically in the Marketplace.

### Authentication & User Management

Firebase handles user authentication via Firebase Admin SDK for server-side token verification. A custom `firebaseAuthStateChanged` event ensures authentication state consistency across all pages. The system uses a dual identity approach with Firebase UIDs for authentication and internal database IDs for service management, linked with OXIO user IDs.

### Payment & Billing Architecture

Stripe is fully integrated for subscription management, one-time purchases, and product catalog management, supporting dynamic pricing and multi-currency transactions. All purchases are automatically recorded in the Purchases table via the Stripe webhook handler and displayed in the Dashboard's "Recent Purchases" section. The `/api/user-purchases` endpoint provides purchase history retrieval with formatted product names and amounts.

### Connectivity Services

Deep integration with OXIO's staging API handles eSIM provisioning, data management, and network services. The platform also includes configurable network features like VPN, security enhancements, and communication services (VoLTE, Wi-Fi calling).

### Blockchain Integration

Web3.py integrates Ethereum smart contracts for DOTM token management on both Sepolia testnet and mainnet, including an automated token reward system based on service usage.

### MCP Server Architecture

A dedicated MCP server provides AI assistants with structured access to service information, pricing data, and feature catalogs through multi-format API endpoints (JSON and HTML), while maintaining strict privacy controls.

### Data Privacy & Security

The platform is designed with privacy in mind, isolating public service information from sensitive user and transaction data. All sensitive credentials are managed through environment variables.

## External Dependencies

### Core Infrastructure Services

-   **OXIO API Platform**: Provides global eSIM and data services via their staging API (api-staging.brandvno.com).
-   **Firebase Authentication**: Google Firebase for user authentication, identity management, and real-time state synchronization.
-   **Stripe Payment Processing**: Comprehensive payment infrastructure for subscriptions, product catalogs, and webhooks.

### Communication & AI Services

-   **ElevenLabs Voice Synthesis**: Advanced text-to-speech services with multilingual support (30 languages) and custom voice profiles (CanadianRockstar, ScienceTeacher, BuddyFriend). Includes intelligent caching and progressive message delivery (Welcome, Tip, Update messages).
-   **OpenAI Integration**: AI-powered help desk and automated customer support.
-   **SMTP Email Services**: Configurable system for transactional emails and notifications.

### Blockchain & Web3

-   **Ethereum Network**: Web3 integration supporting Sepolia testnet and Ethereum mainnet.
-   **DOTM Smart Contract**: Custom ERC-20 token contract for rewards.

### Development & Deployment Tools

-   **PostgreSQL Database**: Primary data storage.
-   **Hardhat Development Framework**: For Ethereum smart contract development.
-   **GitHub Integration**: Source code management.
-   **Jira Integration**: Ticketing system for customer support.
-   **Shopify Integration**: E-commerce platform for marketplace product management via Shopify Admin API.