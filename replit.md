# DOTM Platform

## Overview

The DOTM Platform is a comprehensive telecommunications service platform offering global eSIM connectivity, cryptocurrency rewards, and network optimization. It bridges traditional mobile services with blockchain technology, providing global data through OXIO's infrastructure, integrating DOTM token rewards, and utilizing Firebase for user management. The platform includes a Model Context Protocol (MCP) server for AI assistant integration, extensive API services, and a multi-layered architecture supporting various features from basic connectivity to advanced network management. Its business vision is to revolutionize mobile services by incorporating Web3 technologies, offering a unique value proposition in the telecommunications market.

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