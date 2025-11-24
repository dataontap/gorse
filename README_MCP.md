
# DOTM Platform MCP Server Documentation

## Overview

The DOTM Platform MCP (Model Context Protocol) Server provides detailed service information for AI assistants and automated systems. This server exposes a comprehensive catalog of services, pricing, and platform capabilities.

## MCP Features

### 🚀 Core Capabilities

**Comprehensive Service Catalog**
- **20+ Services** across 7 categories (Connectivity, Memberships, Physical Products, Network Features, Token Services, API Services, Support)
- **Real-time Pricing** with dynamic cost calculations
- **Service Availability** tracking (Available, Beta, Limited Edition, Invitation Only)
- **Feature Listings** with detailed descriptions for each service

**Multi-Format Access**
- **Interactive Web Interface** - Responsive HTML with Bootstrap styling at `/mcp`
- **JSON API** - RESTful endpoints for programmatic access at `/mcp/api`
- **Service-Specific Endpoints** - Individual service details at `/mcp/service/{service_id}`
- **Pricing Calculator** - Dynamic cost computation at `/mcp/calculate`

**Privacy-First Architecture**
- **Zero User Data Exposure** - Only public service information is accessible
- **Static Service Catalog** - No dynamic user data retrieval
- **Compliant Error Handling** - Generic responses without system internals
- **Regular Privacy Audits** - Quarterly compliance reviews

### 🛠 Advanced Features

**Dynamic Pricing Engine**
- **Cost Overview Dashboard** - Free tier ($0/month) to maximum configuration (~$30-40/month)
- **Flexible Billing Cycles** - One-time, monthly, and annual options
- **Multi-Currency Support** - USD and CAD pricing
- **Service Bundling** - Calculate total costs for service combinations

**Developer Integration**
- **RESTful API Design** - Standard HTTP methods and status codes
- **Multiple Response Formats** - JSON for APIs, HTML for interactive use
- **Caching Strategy** - Static catalog data optimized for performance
- **Error Handling** - Graceful degradation with informative messages

**Service Categories Covered**
1. **Connectivity Services** - Global eSIM and data plans (10GB packages, beta programs)
2. **Membership Plans** - Basic ($24/year) and Full ($66/year) annual subscriptions
3. **Physical Products** - DOTM Metal Card ($99.99) and hardware items
4. **Network Features** - VPN ($8/month), Security ($5/month), Optimization add-ons
5. **Token Services** - DOTM cryptocurrency rewards and founding member benefits
6. **API Services** - OXIO integration, Stripe payment processing
7. **Support Services** - Tiered customer assistance (Standard, Priority, Premium)

### 📊 Analytics & Monitoring

**Real-Time Metrics**
- Service availability tracking
- Pricing trend analysis
- Category performance monitoring
- API usage statistics

**Business Intelligence**
- Cost structure analysis
- Service adoption patterns
- Revenue optimization insights
- Market positioning data

## Features

- **Service Catalog**: Complete listing of all platform services
- **Pricing Information**: Real-time pricing for all services and memberships
- **API Endpoints**: RESTful JSON API for programmatic access
- **Pricing Calculator**: Dynamic cost calculation for service combinations
- **Privacy Compliant**: No user data exposure, only public service information

## Live Server

The MCP server is available at: `https://gorse.dotmobile.app/mcp`

## API Endpoints

### Main Endpoints

| Endpoint | Description | Response Type |
|----------|-------------|---------------|
| `/mcp` | Interactive web interface with complete service catalog | HTML |
| `/mcp/api` | JSON API with full service data | JSON |
| `/mcp/service/{service_id}` | Details for specific service | JSON |
| `/mcp/calculate` | Pricing calculator with service selection | JSON |

### Service Categories

1. **Connectivity Services** - Global eSIM and data plans
2. **Membership Plans** - Annual subscriptions with benefits
3. **Physical Products** - Hardware and collectibles
4. **Network Features** - Add-on services and optimizations
5. **Token Services** - DOTM cryptocurrency rewards
6. **API Services** - Integration and developer tools
7. **Support Services** - Customer assistance tiers

## Usage Examples

### Get All Services
```bash
curl https://gorse.dotmobile.app/mcp/api
```

### Get Specific Service
```bash
curl https://gorse.dotmobile.app/mcp/service/basic_membership
```

### Calculate Pricing
```bash
curl "https://gorse.dotmobile.app/mcp/calculate?services=basic_membership,global_data_10gb"
```

## Cost Overview

- **Free Tier**: $0.00/month (Beta access only)
- **Basic Membership**: $24.00/year (Core connectivity)
- **Full Membership**: $66.00/year (Premium features)
- **Maximum with Add-ons**: ~$30-40/month (All network features)

## Key Services

### Membership Plans

#### Basic Membership - $24 CAD/year
- Global data access
- 2FA SMS support
- eSIM line activation
- Unlimited hotspot
- Data sharing with members
- Device insights and protection

#### Full Membership - $66 USD/year
- Unlimited talk & text (North America)
- Global Wi-Fi calling
- Satellite connectivity (2026)
- All Basic features included

### Network Add-ons (Monthly)
- Network Security: $5.00
- VPN Access: $8.00
- Priority Routing: $6.00
- Network Monitoring: $4.00
- Network Optimization: $3.00

### One-time Purchases
- Global Data 10GB: $10.00
- DOTM Metal Card: $99.99
- Beta eSIM Activation: $1.00

## Privacy & Security

The MCP server strictly adheres to privacy guidelines:
- **No user data exposure** - Only public service information
- **Static service catalog** - No dynamic user data retrieval
- **Compliant responses** - Generic error handling without system internals
- **Regular audits** - Quarterly compliance reviews

## Technical Implementation

### Technologies Used
- **Flask** - Python web framework
- **Jinja2** - Template engine for HTML responses
- **JSON** - Structured data format for API responses
- **Bootstrap** - Responsive web design
- **RESTful API** - Standard HTTP methods and status codes

### Response Formats
- **HTML**: Interactive web interface with responsive design
- **JSON**: Structured data for programmatic access
- **Error Handling**: Graceful degradation with informative messages

### Caching Strategy
- Service catalog is static and can be cached
- Pricing calculations are computed on-demand
- No user-specific data caching

## Integration Examples

### Python Integration
```python
import requests

# Get all services
response = requests.get('https://gorse.dotmobile.app/mcp/api')
services = response.json()

# Calculate pricing for specific services
calc_response = requests.get(
    'https://gorse.dotmobile.app/mcp/calculate',
    params={'services': ['basic_membership', 'network_security']}
)
pricing = calc_response.json()
```

### JavaScript Integration
```javascript
// Fetch service catalog
fetch('https://gorse.dotmobile.app/mcp/api')
  .then(response => response.json())
  .then(data => console.log('Services:', data.services));

// Calculate pricing
const services = ['basic_membership', 'vpn_access'];
fetch(`https://gorse.dotmobile.app/mcp/calculate?services=${services.join(',')}`)
  .then(response => response.json())
  .then(data => console.log('Pricing:', data.pricing));
```

## Service IDs Reference

### Memberships
- `basic_membership` - Basic annual membership
- `full_membership` - Full annual membership  
- `beta_tester` - Beta testing program

### Connectivity
- `global_data_10gb` - 10GB global data package
- `beta_esim_activation` - Beta eSIM activation

### Network Features
- `network_security_basic` - Basic network security
- `network_vpn_access` - VPN access service
- `network_priority_routing` - Priority routing
- `network_monitoring` - Network monitoring
- `network_optimization` - Performance optimization

### Physical Products
- `metal_card` - DOTM Metal Card

### Token Services
- `founding_member_token` - 100 DOTM tokens
- `new_member_token` - 1 DOTM welcome token
- `purchase_rewards` - 10.33% cashback in DOTM

## Support

For technical support or integration assistance:
- Platform: [DOTM Platform](https://gorse.dotmobile.app)
- Documentation: [MCP Server](https://gorse.dotmobile.app/mcp)
- Repository: Contact for access

## License

This MCP server documentation is part of the DOTM Platform ecosystem. Usage is subject to platform terms of service.

## MCP Server v2.0 (2025 Specification)

### NEW: Protocol-Compliant MCP Server

We now offer a **fully compliant Model Context Protocol (MCP) server** following the **2024-11-05 specification**:

#### Key Features

- ✅ **JSON-RPC 2.0** messaging protocol
- ✅ **HTTP + SSE** transport (Server-Sent Events)
- ✅ **Resources**: 4 resource types (catalog, memberships, network features, pricing)
- ✅ **Tools**: 4 tools (pricing calculator, service search, details, comparisons)
- ✅ **Prompts**: 3 prompts (plan recommendations, service explanations, cost optimization)
- ✅ **Auto-Registration Authentication** via Firebase Bearer tokens

#### Base URL
```
https://gorse.dotmobile.app/mcp/v2
```

#### Quick Start

**1. Server Information:**
```bash
curl https://gorse.dotmobile.app/mcp/v2
```

**2. Initialize Connection:**
```bash
curl -X POST https://gorse.dotmobile.app/mcp/v2/messages \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {"name": "test-client", "version": "1.0.0"}
    }
  }'
```

**3. Calculate Pricing:**
```bash
curl -X POST https://gorse.dotmobile.app/mcp/v2/messages \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "calculate_pricing",
      "arguments": {"service_ids": ["basic_membership", "network_vpn_access"]}
    }
  }'
```

#### Documentation

- **Full Specification**: See `MCP_V2_SPECIFICATION.md`
- **API Reference**: https://gorse.dotmobile.app/mcp/v2/docs
- **Protocol Spec**: https://modelcontextprotocol.io/specification/2024-11-05

#### Available Methods

**Connection**: `initialize`, `ping`  
**Resources**: `resources/list`, `resources/read`  
**Tools**: `tools/list`, `tools/call`  
**Prompts**: `prompts/list`, `prompts/get`

---

## Legacy MCP v1 (Service Catalog API)

The original MCP service catalog is still available at `/mcp` for backwards compatibility.

---

*Last Updated: October 22, 2025*
*MCP v1: 1.0 | MCP v2: 2.0.0*
*Total Services: 20+ across 7 categories*
