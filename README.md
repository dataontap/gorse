# DOT Services

![DOT](https://img.shields.io/badge/Status-Live-green) ![Ethereum](https://img.shields.io/badge/Ethereum-Mainnet-blue) ![Version](https://img.shields.io/badge/Version-1.0-brightgreen)

**Code, APIs and App Available for FREE. $1/month license for globally connected active users. Ask for above 100TPH access.**

## 🌐 Full MVNO framework

dotmobile is a smart tiny telecom. This gorse release is compact Alpha build of a Full MVNO. 

Available for FREE and $1 per user above 100TPH. Etheruem and blockchain parts and many other things optional. Used Stripe for invoices, catalog and payments. 

Please use this comprehensive telecommunications service toolset/framework to create better telecommunications experiences, bridge traditional mobile services with better digital and user experience, integrate newtech and AI and use our token (blockchain technology) for good. 

We provide global eSIM connectivity, automation, network services intelligence and network optimization features through a unified ecosystem in a public cloud. Our data servers are located colely in North America: N.Virginia, USA and in Montreal, Canada. We use Full MVNO type of connectivity in the USA, Mexico and in Canada soon hopefully. 

We use Firebase authentication, Gemini 1.5 Flash for AI, NeonDB for Postgresql databases, Resend for professional email delivery, ElevenLabs for voice synthesis, Bitchat for fallback connectivity and Ethereum blockchain integration. Full list of integrations below.  

### 🚀 Live Platform

- **Main Platform**: [gorse.dotmobile.app](https://gorse.dotmobile.app)
- **MCP Server**: [mcp.dotmobile.app](https://mcp.dotmobile.app)
- **API Documentation**: [gorse.dotmobile.app/mcp](https://gorse.dotmobile.app/mcp)

## 💎 DOTM Token (Ethereum Mainnet)

**Contract Address**: `0xF57ab8DEE7ebE3686DB8Bf89E8aCc15E94B97A8D`

### Token Economics
- **Token Symbol**: DOTM
- **Network**: Ethereum Mainnet
- **Max Supply**: 10,333,333 DOTM
- **Current Supply**: (mint-on-demand)
- **Decimals**: 18

### Reward System
- **10.33% Cashback**: Earn DOTM tokens on all service purchases
- **New Member Bonus**: 10.33 DOTM tokens for joining the platform
- **Usage Rewards**: Additional tokens based on service utilization
- **Founding Member Benefits**: Special perks for early adopters

### Smart Contract Features
- **ERC-20 Standard**: Full compatibility with Ethereum ecosystem
- **Mintable**: Owner-controlled token distribution
- **Reward Automation**: Automatic distribution based on platform activity
- **Supply Cap**: Fixed maximum supply with deflationary mechanics

## 🌍 Core Services

### Global eSIM Connectivity
- **Global Data Package**: **$20.00 USD for 10GB**
- **190+ Countries**: Worldwide coverage through OXIO network
- **Instant Activation**: Immediate service provisioning
- **No Roaming Fees**: Transparent, fixed pricing

### Membership Plans
- **Basic Membership**: **$24.00 USD/year**
  - Global data access
  - Standard support
  - DOTM token rewards
  - Basic network features

- **Full Membership**: **$66.00 USD/year**
  - Unlimited talk & text
  - Priority support
  - Enhanced token rewards
  - Premium network features
  - Beta access priority

### Beta Program
- **Email Approval Workflow**: Admin-managed access control
- **Phone Number Assignment**: Random North American numbers via OXIO
- **QR Code Generation**: RESIN data and phone access codes
- **Profile Integration**: Complete beta management in user profiles
- **OXIO Integration**: Automatic user provisioning and GroupID management

## 🔧 Platform Architecture

### Backend Infrastructure
- **Flask REST API**: Core application with Flask-RESTX documentation
- **PostgreSQL Database**: Connection pooling and data management
- **Firebase Authentication**: Secure user identity management
- **Stripe Integration**: Complete payment processing infrastructure
- **OXIO API**: Global eSIM and connectivity services
- **Ethereum Integration**: Web3.py for blockchain interactions
- **Resend Email API**: Professional email delivery with 99.9% deliverability

### Key Integrations
- **Firebase Admin SDK**: Server-side authentication and user management
- **Stripe Payments**: Subscription management and billing
- **OXIO Staging API**: eSIM provisioning and network services
- **Ethereum Mainnet**: DOTM token rewards and transactions
- **Resend Email API**: Professional email delivery and notifications
- **ElevenLabs**: Voice synthesis for personalized interactions
- **OpenAI API**: AI-powered customer support

## 🎙️ Advanced Communication Features

### Resend Email Service Integration
- **Professional Email Delivery**: High-deliverability email service with 99.9% uptime
- **Verified Domain**: emails sent from @dotmobile.app with proper SPF/DKIM authentication
- **Transactional Emails**: Magic link authentication, welcome messages, and notifications
- **Template Support**: HTML email templates with dynamic content injection
- **Delivery Analytics**: Real-time email delivery tracking and bounce management
- **API Integration**: RESTful email API with automatic failover to SMTP backup
- **Scalable Infrastructure**: Handle high-volume email campaigns and notifications

### ElevenLabs.io Voice Synthesis
- **Multilingual Support**: Welcome messages in English, Spanish, and French
- **Personalized Messages**: Dynamic user-specific welcome audio content
- **Premium Voices**: High-quality neural voice synthesis (default: Rachel voice)
- **Custom Voice Settings**: Adjustable stability, similarity boost, and style parameters
- **Real-time Generation**: On-demand text-to-speech conversion for user interactions
- **Integration**: Seamless voice messages for onboarding and notifications

### Bitchat Encrypted Messaging
- **Zero Registration**: No accounts, emails, or phone numbers required
- **Military-Grade Encryption**: X25519 key exchange, AES-256-GCM, Ed25519 signatures
- **Mesh Networking**: Bluetooth LE peer-to-peer communication with store-and-forward capability
- **Privacy First**: Ephemeral messages, emergency triple-tap data wipe
- **Battery Optimized**: Adaptive power modes with intelligent message compression (LZ4)
- **Offline Operation**: Complete functionality without internet or cellular connectivity
- **Cover Traffic**: Timing obfuscation and dummy messages to prevent traffic analysis

### Model Context Protocol (MCP) Server
- **AI Assistant Integration**: Structured service information access
- **Multi-Format APIs**: JSON endpoints and interactive HTML interfaces
- **Privacy-First Design**: Zero user data exposure
- **Real-Time Pricing**: Dynamic cost calculations
- **Service Catalog**: 20+ services across 7 categories

## 📱 Beta Approval System

### User Flow
1. **Request Access**: Users submit beta requests through their Profile page
2. **Admin Notification**: Automated email with approve/reject links
3. **OXIO Integration**: Phone number assignment and user provisioning
4. **QR Code Generation**: Service activation codes and RESIN data
5. **Profile Display**: Phone numbers and service details in user interface

### Technical Features
- **Email Workflow**: HTML notifications with one-click approval
- **Random Phone Generation**: North American area codes and numbers
- **GroupID Management**: Unique service identifiers for organization
- **Database Tracking**: Complete request history and status management
- **API Endpoints**: RESTful interfaces for beta management

### API Endpoints
- `POST /api/beta-request` - Submit beta access request
- `GET /api/beta-approve/<id>` - Admin approval endpoint
- `GET /api/beta-reject/<id>` - Admin rejection endpoint
- `GET /api/beta-status` - Check user beta status
- `GET /api/user-phone-numbers` - Retrieve phone numbers with QR codes

## 💰 Pricing Structure

| Service | Price | Billing | Features |
|---------|-------|---------|-----------|
| **Global Data** | **$20.00 USD** | Per 10GB | Worldwide coverage, instant activation |
| **Basic Membership** | **$24.00 USD** | Annual | Global access, standard support, token rewards |
| **Full Membership** | **$66.00 USD** | Annual | Unlimited features, priority support, enhanced rewards |
| **Network Security** | $5.00 USD | Monthly | VPN access, threat protection |
| **VPN Access** | $8.00 USD | Monthly | Global server network, unlimited bandwidth |
| **Priority Routing** | $6.00 USD | Monthly | Optimized network paths |
| **DOTM Metal Card** | $99.99 USD | One-time | Physical collectible, founding member status |

### Cost Calculator
- **Free Tier**: $0/month (Beta access only)
- **Basic Plan**: ~$2/month (Basic membership)
- **Premium Plan**: ~$5.50/month (Full membership)
- **Maximum Configuration**: ~$30-40/month (All features enabled)

## 🛡️ Security & Privacy

### Privacy Protection
- **Zero User Data Exposure**: MCP server only exposes public service information
- **Data Isolation**: Strict separation between user data and public APIs
- **Compliant Error Handling**: Generic responses without system internals
- **Regular Audits**: Quarterly compliance and security reviews

### Security Features
- **HTTPS/TLS Encryption**: All communications encrypted end-to-end
- **Firebase Authentication**: Industry-standard identity management
- **Rate Limiting**: API abuse protection and traffic management
- **Input Validation**: Comprehensive parameter sanitization
- **Audit Logging**: Complete action tracking and compliance records

## 🔌 Developer Integration

### Quick Start
```bash
# Get all services
curl https://gorse.dotmobile.app/mcp/api

# Get specific service details
curl https://gorse.dotmobile.app/mcp/service/basic_membership

# Calculate pricing for multiple services
curl "https://gorse.dotmobile.app/mcp/calculate?services=basic_membership,global_data_10gb"
```

### Python Integration
```python
import requests

# Fetch service catalog
response = requests.get('https://gorse.dotmobile.app/mcp/api')
services = response.json()['services']

# Calculate total pricing
pricing = requests.get(
    'https://gorse.dotmobile.app/mcp/calculate',
    params={'services': 'basic_membership,network_security'}
).json()

print(f"Monthly cost: ${pricing['pricing']['monthly_recurring']}")
print(f"Annual cost: ${pricing['pricing']['annual_total']}")
```

### JavaScript Integration
```javascript
// Fetch service data
const response = await fetch('https://gorse.dotmobile.app/mcp/api');
const data = await response.json();

// Display available services
console.log('Available services:', Object.keys(data.services));

// Calculate pricing
const pricing = await fetch(
    'https://gorse.dotmobile.app/mcp/calculate?services=full_membership,vpn_access'
).then(res => res.json());

console.log(`Total monthly: $${pricing.pricing.monthly_recurring}`);
```

## 📊 Service Categories

### 1. Connectivity Services
- **Global eSIM**: Worldwide mobile data access
- **Data Packages**: 10GB packages at $20 USD
- **Beta Programs**: Early access to new features
- **Network Coverage**: 190+ countries supported

### 2. Membership Plans
- **Basic**: $24/year - Essential connectivity features
- **Full**: $66/year - Premium features and unlimited access
- **Beta**: Free - Early access and testing privileges

### 3. Network Features (Monthly Add-ons)
- **Network Security**: $5/month - Advanced threat protection
- **VPN Access**: $8/month - Global server network
- **Priority Routing**: $6/month - Optimized network paths
- **Network Monitoring**: $4/month - Real-time analytics
- **Performance Optimization**: $3/month - Speed enhancements

### 4. Physical Products
- **DOTM Metal Card**: $99.99 - Premium collectible
- **Hardware Accessories**: Various pricing
- **Limited Editions**: Exclusive items for members

### 5. Token Services
- **DOTM Rewards**: 10.33% cashback on purchases
- **New Member Bonus**: 10.33 tokens for joining
- **Founding Member Benefits**: Special perks and recognition
- **Staking Rewards**: Additional benefits for token holders

### 6. API Services
- **OXIO Integration**: eSIM provisioning and management
- **Stripe Processing**: Payment handling and subscriptions
- **Developer Tools**: SDKs and documentation
- **Webhook Support**: Real-time event notifications

### 7. Support Services
- **Standard Support**: Available to all users
- **Priority Support**: Enhanced assistance for members
- **Premium Support**: Dedicated support for full members
- **Community Forums**: Peer-to-peer assistance

## 🏗️ Technical Specifications

### API Specifications
- **Base URL**: `https://gorse.dotmobile.app`
- **MCP Server**: `https://gorse.dotmobile.app/mcp`
- **Response Format**: JSON and HTML
- **Authentication**: Firebase-based for user endpoints
- **Rate Limiting**: 100 requests/minute for public APIs

### Database Schema
- **Users**: Firebase UID mapping and profile data
- **Subscriptions**: Stripe integration and billing cycles
- **Purchases**: Transaction history and product tracking
- **Beta Requests**: Approval workflow and phone assignments
- **Network Features**: User preferences and service configurations

### Blockchain Integration
- **Network**: Ethereum Mainnet
- **Token Standard**: ERC-20
- **Wallet Integration**: MetaMask and Web3 compatible
- **Transaction Tracking**: Complete on-chain activity monitoring

## 📈 Platform Statistics

- **Total Services**: 20+ across 7 categories
- **Global Coverage**: 190+ countries
- **API Uptime**: 99.9%
- **Active Integrations**: Firebase, Stripe, OXIO, Ethereum
- **Token Contract**: Live on Ethereum Mainnet
- **Beta Users**: Growing community of early adopters

## 🚀 Getting Started

### For Users
1. **Sign Up**: Create account at [gorse.dotmobile.app](https://gorse.dotmobile.app)
2. **Choose Plan**: Select Basic ($24/year) or Full ($66/year) membership
3. **Purchase Data**: Buy global data packages ($20 for 10GB)
4. **Request Beta**: Apply for beta access through your profile
5. **Earn Tokens**: Receive DOTM rewards for all activities

### For Developers
1. **Explore API**: Visit [gorse.dotmobile.app/mcp](https://gorse.dotmobile.app/mcp)
2. **Read Documentation**: Complete API reference available
3. **Test Integration**: Use public endpoints for development
4. **Build Applications**: Integrate DOTM services into your apps
5. **Join Community**: Connect with other developers

### For Business Partners
1. **API Access**: Programmatic service integration
2. **White Label**: Custom branding options available
3. **Bulk Pricing**: Volume discounts for enterprise
4. **Custom Features**: Tailored solutions for specific needs
5. **Partnership Program**: Revenue sharing opportunities

## 📞 Support & Community

### Getting Help
- **Documentation**: Comprehensive guides and API reference
- **Community Forums**: Peer-to-peer assistance and discussions
- **Email Support**: Direct assistance for technical issues
- **Priority Support**: Enhanced assistance for members
- **Emergency Support**: 24/7 availability for critical issues

### Contributing
We welcome contributions to the DOTM Platform:

1. **Fork Repository**: Create your own copy for development
2. **Create Branch**: `git checkout -b feature/improvement`
3. **Make Changes**: Implement your enhancements
4. **Test Thoroughly**: Ensure all functionality works correctly
5. **Submit PR**: Include detailed description of changes

### Resources
- **API Documentation**: [gorse.dotmobile.app/mcp](https://gorse.dotmobile.app/mcp)
- **GitHub Repository**: Source code and issue tracking
- **Technical Blog**: Implementation details and updates
- **Community Discord**: Real-time discussions and support

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Quick Links

- **Main Platform**: [gorse.dotmobile.app](https://gorse.dotmobile.app)
- **MCP Server**: [mcp.dotmobile.app](https://mcp.dotmobile.app)
- **API Documentation**: [gorse.dotmobile.app/mcp](https://gorse.dotmobile.app/mcp)
- **JSON API**: [gorse.dotmobile.app/mcp/api](https://gorse.dotmobile.app/mcp/api)
- **DOTM Token**: [0xF57ab8DEE7ebE3686DB8Bf89E8aCc15E94B97A8D](https://etherscan.io/token/0xF57ab8DEE7ebE3686DB8Bf89E8aCc15E94B97A8D)

---

**Built with**: Flask, PostgreSQL, Firebase, Stripe, OXIO, Ethereum, and ❤️

*Connecting the world through decentralized telecommunications*

---

### 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=dotmobile/dotm-platform&type=Date)](https://star-history.com/#dotmobile/dotm-platform&Date)

### 📊 Platform Status

![Platform Status](https://img.shields.io/badge/Platform-Operational-green)
![API Status](https://img.shields.io/badge/API-99.9%25_Uptime-green)
![Token Status](https://img.shields.io/badge/DOTM_Token-Live_on_Mainnet-blue)
![Beta Program](https://img.shields.io/badge/Beta_Program-Active-orange)

**Last Updated**: September 11, 2025  
**Version**: 3.0.1  
**DOTM Token Contract**: 0xF57ab8DEE7ebE3686DB8Bf89E8aCc15E94B97A8D