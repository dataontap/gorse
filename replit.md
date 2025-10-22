# DOTM Platform

## Overview

The DOTM Platform is a telecommunications service platform that integrates global eSIM connectivity, cryptocurrency rewards, and network optimization. It merges traditional mobile services with blockchain technology, leveraging OXIO's infrastructure for global data and incorporating DOTM token rewards. Firebase is used for user management, and a Model Context Protocol (MCP) server enables AI assistant integration. The platform offers extensive API services and a multi-layered architecture to support features ranging from basic connectivity to advanced network management. Its business vision is to innovate mobile services through Web3 technologies, providing a unique offering in the telecommunications market.

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

### Blockchain Integration

Web3.py integrates Ethereum smart contracts for DOTM token management on Sepolia testnet and mainnet, including an automated token reward system based on service usage.

### MCP Server Architecture

A dedicated MCP server provides AI assistants with structured access to service information, pricing data, and feature catalogs through multi-format API endpoints (JSON and HTML), while maintaining strict privacy controls. It includes AI-driven eSIM activation workflows, automatically generating Stripe invoices if payment is not found, and implementing rate limiting (100 activations/hour with queue management).

### UI/UX Decisions

The user profile page is designed to display eSIM information and phone numbers clearly. API responses are formatted to match frontend expectations, including specific field mappings and JSON structures with success flags.

### Data Privacy & Security

The platform isolates public service information from sensitive user and transaction data. All sensitive credentials are managed through environment variables.

## External Dependencies

### Core Infrastructure Services

-   **OXIO API Platform**: Provides global eSIM and data services via its staging API.
-   **Firebase Authentication**: Google Firebase for user authentication and identity management.
-   **Stripe Payment Processing**: For subscriptions, product catalogs, and webhooks.

### Communication & AI Services

-   **ElevenLabs Voice Synthesis**: Provides advanced text-to-speech services with multilingual support and custom voice profiles.
-   **OpenAI Integration**: For AI-powered help desk and automated customer support.
-   **SMTP Email Services**: For transactional emails and notifications.

### Blockchain & Web3

-   **Ethereum Network**: Supports Web3 integration on Sepolia testnet and Ethereum mainnet.
-   **DOTM Smart Contract**: Custom ERC-20 token contract.

### Development & Deployment Tools

-   **PostgreSQL Database**: Primary data storage.
-   **Hardhat Development Framework**: For Ethereum smart contract development.
-   **GitHub Integration**: For source code management.
-   **Jira Integration**: For customer support ticketing.
-   **Shopify Integration**: For marketplace product management via Shopify Admin API.