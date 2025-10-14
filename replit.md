# DOTM Platform

## Overview

The DOTM Platform is a comprehensive telecommunications service platform that provides global eSIM connectivity, cryptocurrency rewards, and network optimization features. The platform serves as a bridge between traditional mobile services and blockchain technology, offering users global data connectivity through OXIO's infrastructure while incorporating DOTM token rewards and Firebase-based user management.

The platform includes a Model Context Protocol (MCP) server for AI assistant integration, comprehensive API services, and a multi-layered service architecture supporting everything from basic connectivity to advanced network features.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture

**Flask-based REST API**: The core application uses Flask with Flask-RESTX for API documentation and Flask-SocketIO for real-time communication. The main application (`main.py`) serves as the central hub coordinating all services and database operations.

**Database Layer**: PostgreSQL database with connection pooling for managing user data, subscriptions, purchases, and service configurations. The system uses contextual database connections to ensure proper resource management across all services.

**Service-Oriented Design**: The platform employs a modular service architecture where each major functionality (OXIO connectivity, Stripe payments, Firebase authentication, email services) is encapsulated in dedicated service classes.

### Authentication & User Management

**Firebase Authentication**: Firebase handles user authentication and identity management, with Firebase Admin SDK integration for server-side token verification and user management operations.

**Dual Identity System**: Users maintain both Firebase UIDs for authentication and internal database IDs for service management, with OXIO user IDs linking to connectivity services.

### Payment & Billing Architecture

**Stripe Integration**: Complete Stripe integration for subscription management, one-time purchases, and product catalog management. The system automatically creates Stripe customers for new users and manages complex pricing structures including data packages, network features, and membership tiers.

**Dynamic Pricing Engine**: Flexible pricing system supporting multiple billing cycles (one-time, monthly, annual) with service bundling capabilities and multi-currency support (USD/CAD).

### Connectivity Services

**OXIO API Integration**: Deep integration with OXIO's staging API for eSIM provisioning, data management, and network services. The platform handles authentication, user provisioning, and service activation through OXIO's infrastructure.

**Network Feature Management**: Configurable network features including VPN services, security enhancements, optimization features, and communication services (voLTE, Wi-Fi calling) with granular on/off controls.

### Blockchain Integration

**Ethereum Smart Contract Integration**: Web3.py integration for DOTM token management, with support for both Sepolia testnet and mainnet deployments. The system tracks token balances and manages cryptocurrency rewards tied to service usage.

**Token Reward System**: Automated token distribution based on service purchases and usage patterns, with configurable reward percentages per product type.

### MCP Server Architecture

**Model Context Protocol Implementation**: Dedicated MCP server (`mcp_server.py`) providing AI assistants with structured access to service information, pricing data, and feature catalogs while maintaining strict privacy controls.

**Multi-Format API Access**: The MCP server supports both JSON API endpoints for programmatic access and HTML interfaces for interactive browsing, with real-time pricing calculations.

### Data Privacy & Security

**Privacy-First Design**: The MCP server implements strict data isolation, exposing only public service information while protecting all user data, transaction details, and internal metrics.

**Environment-Based Configuration**: All sensitive credentials and API keys are managed through environment variables with fallback mechanisms for development environments.

## External Dependencies

### Core Infrastructure Services

**OXIO API Platform**: Primary connectivity provider offering global eSIM and data services through their staging API (api-staging.brandvno.com). Handles network provisioning, data allocation, and service activation.

**Firebase Authentication**: Google Firebase for user authentication, identity management, and real-time user state synchronization with comprehensive Admin SDK integration.

**Stripe Payment Processing**: Complete payment infrastructure including subscription management, product catalogs, pricing models, and webhook handling for billing events.

### Communication & AI Services

**ElevenLabs Voice Synthesis**: Advanced text-to-speech services providing multilingual personalized messages with custom voice profiles. Supports 30 languages (including English, French, Spanish, Chinese, Japanese, Arabic, Portuguese, German, Hindi, Korean, Italian, Russian, Dutch, Turkish, Polish, Swedish, Filipino, Ukrainian, Greek, Czech, Finnish, Romanian, Vietnamese, Hungarian, Norwegian, Thai, Indonesian, Danish, Hebrew, Malay) with 3 distinct voice personalities:
- **CanadianRockstar**: Energetic and enthusiastic voice (Adam from ElevenLabs)
- **ScienceTeacher**: Clear and professional voice (Bella from ElevenLabs)
- **BuddyFriend**: Warm and friendly voice (Antoni from ElevenLabs)

The system includes intelligent caching for instant playback, automatic pre-generation of EN/FR messages, position tracking for seamless language/voice switching, and real-time audio visualization.

**Intelligent Message System**: Progressive content delivery that adapts to user behavior. The platform automatically selects message types based on listening history:
- **Welcome Messages**: Initial introduction to DOT Mobile platform and services for new users
- **Tip Messages**: Helpful information about DOTM token rewards, Bitchat secure messaging, eSIM management, and network features like VPN and Wi-Fi calling
- **Update Messages**: Latest platform features including the 30-language voice system, intelligent message progression, and Shopify marketplace integration

Messages are tracked through a database history system that ensures users receive progressive content - starting with welcome for new users, then tips after hearing the welcome, and finally updates. The caching system preserves message types to ensure accurate telemetry across all playback scenarios. API endpoints: `/api/welcome-message/voices`, `/api/welcome-message/generate`, `/api/welcome-message/track-listen`, `/api/welcome-audio/<id>`.

**OpenAI Integration**: AI-powered help desk services and automated customer support through OpenAI's API for intelligent query handling.

**SMTP Email Services**: Configurable email delivery system supporting multiple SMTP providers for transactional emails, notifications, and automated communications.

### Blockchain & Web3

**Ethereum Network**: Web3 integration supporting both Sepolia testnet for development and Ethereum mainnet for production token operations.

**DOTM Smart Contract**: Custom ERC-20 token contract deployed on Ethereum for reward distribution and cryptocurrency integration.

### Development & Deployment Tools

**PostgreSQL Database**: Primary data storage with connection pooling and comprehensive schema management for users, subscriptions, transactions, and service configurations.

**Hardhat Development Framework**: Ethereum development environment for smart contract compilation, testing, and deployment with multi-network support.

**GitHub Integration**: Source code management with potential automated deployment pipelines and version control integration.

**Jira Integration**: Help desk ticketing system integration for comprehensive customer support workflow management. Configured using environment variables (JIRA_API_TOKEN, JIRA_EMAIL, JIRA_PROJECT_KEY) for dotmobile.atlassian.net workspace. Note: User dismissed the Replit JIRA connector, so manual integration with environment variables is used instead.

**Shopify Integration**: E-commerce platform integration for marketplace product management. The platform uses Shopify Admin API for product synchronization, inventory management, and order tracking through the centralized admin panel at `/admin/shopify`.