
# DOTM Platform Documentation

Welcome to the comprehensive documentation for the DOTM Platform - a next-generation global connectivity ecosystem.

## 🌐 Live Platform

- **Main**: [gorse.dotmobile.app](https://gorse.dotmobile.app)
- **MCP Server**: [mcp.dotmobile.app](https://mcp.dotmobile.app) or [gorse.dotmobile.app/mcp](https://gorse.dotmobile.app/mcp)

## 📚 Documentation Structure

### Core Documentation
- **[MCP Server Documentation](README_MCP.md)** - Complete MCP server guide and features
- **[API Reference](MCP_API_REFERENCE.md)** - Detailed API endpoints and usage
- **[Architecture Guide](ARCHITECTURE.md)** - System architecture and design
- **[Deployment Guide](DEPLOYMENT.md)** - Deployment and hosting information
- **[Contributing Guide](CONTRIBUTING.md)** - How to contribute to the project

### Quick Navigation

#### For Developers
- [API Reference](MCP_API_REFERENCE.md) - Complete API documentation
- [Integration Examples](#integration-examples) - Code examples in multiple languages
- [Contributing Guide](CONTRIBUTING.md) - How to contribute

#### For Business Users
- [Service Catalog](#service-catalog) - Available services and pricing
- [Architecture Overview](ARCHITECTURE.md) - System design and capabilities
- [Security & Privacy](#security--privacy) - Platform security features

#### for System Administrators
- [Deployment Guide](DEPLOYMENT.md) - Hosting and deployment
- [Architecture Guide](ARCHITECTURE.md) - Technical architecture
- [Monitoring & Maintenance](#monitoring--maintenance) - Operations guide

## 🚀 Platform Overview

### Core Services
- **Global eSIM Connectivity** - Worldwide mobile data access
- **Membership Plans** - Tiered service offerings
- **Network Features** - VPN, Security, Optimization
- **Token Economy** - DOTM cryptocurrency rewards
- **Developer APIs** - Integration capabilities

### Key Features
- **20+ Services** across 7 categories
- **Real-time Pricing** with dynamic calculations
- **Privacy-First Design** - No user data exposure
- **RESTful APIs** - Standard HTTP endpoints
- **Interactive Interface** - Responsive web design

## 🔌 Quick Start

### Access the MCP Server
```bash
# Get all services
curl https://get-dot-esim.replit.app/mcp/api

# Get specific service
curl https://get-dot-esim.replit.app/mcp/service/basic_membership

# Calculate pricing
curl "https://get-dot-esim.replit.app/mcp/calculate?services=basic_membership,vpn_access"
```

### Integration Examples

#### Python
```python
import requests

# Fetch service catalog
response = requests.get('https://get-dot-esim.replit.app/mcp/api')
services = response.json()['services']

# Calculate pricing
pricing = requests.get(
    'https://get-dot-esim.replit.app/mcp/calculate',
    params={'services': 'basic_membership,network_security'}
).json()

print(f"Monthly cost: ${pricing['pricing']['monthly_recurring']}")
```

#### JavaScript
```javascript
// Fetch service data
const response = await fetch('https://get-dot-esim.replit.app/mcp/api');
const data = await response.json();

// Display services
console.log('Available services:', Object.keys(data.services));
```

## 💰 Pricing Overview

| Service Category | Price Range | Billing |
|-----------------|-------------|---------|
| **Basic Membership** | $24 CAD/year | Annual |
| **Full Membership** | $66 USD/year | Annual |
| **Network Features** | $3-8/month | Monthly |
| **Global Data** | $10/10GB | One-time |
| **Physical Products** | $99.99 | One-time |

### Cost Calculator
- **Free Tier**: $0/month (Beta access)
- **Basic Plan**: ~$2/month (Basic membership)
- **Full Plan**: ~$5.50/month (Full membership)
- **Maximum**: ~$30-40/month (All features)

## 🛡️ Security & Privacy

### Privacy Protection
- **Zero User Data Exposure** - Only public service information
- **Static Service Catalog** - No dynamic user data retrieval
- **Compliant Error Handling** - Generic responses only
- **Regular Audits** - Quarterly compliance reviews

### Security Features
- **HTTPS/TLS Encryption** - All communications encrypted
- **Rate Limiting** - API abuse protection
- **Input Validation** - All parameters validated
- **Audit Logging** - Complete action tracking

## 📊 Service Categories

### 1. **Connectivity Services**
- Global eSIM activation
- 10GB data packages
- Beta testing programs

### 2. **Membership Plans**
- Basic: $24 CAD/year - Global data access
- Full: $66 USD/year - Unlimited talk & text
- Beta: Free - Early access features

### 3. **Network Features** (Monthly Add-ons)
- Network Security: $5/month
- VPN Access: $8/month
- Priority Routing: $6/month
- Network Monitoring: $4/month
- Performance Optimization: $3/month

### 4. **Physical Products**
- DOTM Metal Card: $99.99
- Hardware accessories
- Limited edition items

### 5. **Token Services**
- DOTM cryptocurrency rewards
- 10.33% cashback on purchases
- Founding member benefits

### 6. **API Services**
- OXIO integration
- Stripe payment processing
- Developer tools

### 7. **Support Services**
- Standard support (all users)
- Priority support (members)
- Premium support (full members)

## 🔧 Technical Specifications

### API Endpoints
- **Base URL**: `https://get-dot-esim.replit.app/mcp`
- **Response Format**: JSON and HTML
- **Authentication**: None required
- **Rate Limiting**: 100 requests/minute

### Integration Support
- **REST API** - Standard HTTP methods
- **JSON Responses** - Structured data format
- **Error Handling** - Graceful degradation
- **CORS Support** - Cross-origin requests

## 📈 Monitoring & Maintenance

### Real-time Metrics
- Service availability tracking
- API response time monitoring
- Usage pattern analysis
- Cost optimization insights

### Maintenance Schedule
- **Monthly Updates** - Feature releases
- **Weekly Optimization** - Performance tuning
- **Daily Monitoring** - Health checks
- **Quarterly Reviews** - Security audits

## 🤝 Contributing

We welcome contributions to the DOTM Platform documentation:

1. **Fork the Repository** - Create your own copy
2. **Create Feature Branch** - `git checkout -b docs/improvement`
3. **Make Changes** - Update documentation
4. **Test Changes** - Verify all links and examples work
5. **Submit Pull Request** - Include detailed description

See our [Contributing Guide](CONTRIBUTING.md) for detailed instructions.

## 📞 Support

### Getting Help
- **Documentation Issues** - Create GitHub issue
- **Integration Support** - Contact development team
- **Business Inquiries** - Use platform contact form
- **Technical Support** - Access help system in platform

### Resources
- **API Documentation** - Complete endpoint reference
- **Code Examples** - Multiple language implementations
- **Best Practices** - Integration guidelines
- **Troubleshooting** - Common issues and solutions

## 📄 License

This documentation is part of the DOTM Platform ecosystem. Usage is subject to platform terms of service.

---

## 🔗 Quick Links

- [MCP Server Interface](https://get-dot-esim.replit.app/mcp) - Interactive service catalog
- [JSON API](https://get-dot-esim.replit.app/mcp/api) - Programmatic access
- [Main Platform](https://get-dot-esim.replit.app) - Full DOTM platform
- [API Reference](MCP_API_REFERENCE.md) - Complete endpoint documentation

---

*Last Updated: January 2025*  
*Documentation Version: 1.0*  
*Platform Status: ✅ Operational*

**Total Services**: 20+ across 7 categories  
**API Uptime**: 99.9%  
**Global Coverage**: 190+ countries  
**Active Integrations**: OXIO, Stripe, Firebase, Ethereum

