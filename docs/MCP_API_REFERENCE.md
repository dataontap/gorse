
# MCP Server API Reference

## Base URL
```
https://get-dot-esim.replit.app/mcp
```

## Authentication
No authentication required. All endpoints are publicly accessible.

## Rate Limiting
- Standard rate limiting applies
- Recommended: 100 requests per minute
- No API key required

## Content Types
- **Requests**: `application/json` (for POST requests)
- **Responses**: `application/json` or `text/html`

---

## Endpoints

### GET `/mcp`
Interactive web interface displaying the complete service catalog.

**Response**: HTML page with responsive design
**Content-Type**: `text/html`

**Features**:
- Complete service catalog
- Interactive pricing calculator
- Responsive design
- Cost overview dashboard

---

### GET `/mcp/api`
JSON API endpoint providing programmatic access to the complete service catalog.

**Response Format**:
```json
{
  "platform": "DOTM",
  "version": "1.0",
  "timestamp": "2025-01-13T10:30:00.000Z",
  "services": {
    "esim_services": { ... },
    "membership_plans": { ... },
    "physical_products": { ... },
    "network_features": { ... },
    "token_services": { ... },
    "api_services": { ... },
    "support_services": { ... }
  },
  "cost_summary": {
    "minimum_monthly": 0.00,
    "basic_monthly": 2.00,
    "full_monthly": 5.50,
    "maximum_monthly": 28.00,
    "basic_yearly": 24.00,
    "full_yearly": 66.00,
    "maximum_yearly": 336.00
  },
  "endpoints": {
    "service_details": "/mcp/service/{service_id}",
    "pricing_calculator": "/mcp/calculate",
    "full_catalog": "/mcp"
  }
}
```

---

### GET `/mcp/service/{service_id}`
Get detailed information for a specific service.

**Parameters**:
- `service_id` (string, required): Unique identifier for the service

**Example Request**:
```bash
GET /mcp/service/basic_membership
```

**Response Format**:
```json
{
  "service": {
    "id": "basic_membership",
    "name": "Basic Membership",
    "description": "GLOBAL DATA ACCESS + 2FA SMS",
    "type": "annual_subscription",
    "price_cad": 24.0,
    "billing_cycle": "yearly",
    "features": [
      "Global data access",
      "$1 per GB of data bonus - limited availability",
      "2FA support via incoming SMS only",
      "eSIM line activation included",
      "Unlimited Hotspot",
      "Infinite data share with any member"
    ],
    "availability": "Available"
  },
  "category": "Membership Plans",
  "timestamp": "2025-01-13T10:30:00.000Z"
}
```

**Error Responses**:
- `404`: Service not found
- `503`: Service detail endpoint not available

---

### GET `/mcp/calculate`
Calculate total pricing for selected services.

**Query Parameters**:
- `services` (array): Comma-separated list of service IDs

**Example Request**:
```bash
GET /mcp/calculate?services=basic_membership,network_security_basic,vpn_access
```

**Response Format**:
```json
{
  "selected_services": [
    {
      "id": "basic_membership",
      "name": "Basic Membership",
      "price_usd": 24.00,
      "type": "annual_subscription",
      "billing_cycle": "yearly"
    },
    {
      "id": "network_security_basic",
      "name": "Network Security",
      "price_usd": 5.00,
      "type": "add_on",
      "billing_cycle": "monthly"
    }
  ],
  "pricing": {
    "one_time_total": 0.00,
    "monthly_recurring": 7.00,
    "yearly_recurring": 24.00,
    "first_year_total": 108.00
  },
  "timestamp": "2025-01-13T10:30:00.000Z"
}
```

**Error Responses**:
- `400`: No services specified (with usage instructions)

---

## Service Categories

### 1. eSIM Services (`esim_services`)
Connectivity and activation services.

**Available Services**:
- `global_data_10gb`: $10.00 one-time
- `beta_esim_activation`: $1.00 beta program

### 2. Membership Plans (`membership_plans`)
Annual subscription plans.

**Available Services**:
- `basic_membership`: $24.00 CAD/year
- `full_membership`: $66.00 USD/year
- `beta_tester`: $0.00/month (invitation only)

### 3. Physical Products (`physical_products`)
Hardware and collectibles.

**Available Services**:
- `metal_card`: $99.99 one-time

### 4. Network Features (`network_features`)
Monthly add-on services.

**Available Services**:
- `network_scans`: $0.00/month (free)
- `network_security_basic`: $5.00/month
- `network_optimization`: $3.00/month
- `network_monitoring`: $4.00/month
- `network_vpn_access`: $8.00/month
- `network_priority_routing`: $6.00/month

### 5. Token Services (`token_services`)
DOTM cryptocurrency rewards.

**Available Services**:
- `founding_member_token`: 100 DOTM (founding members only)
- `new_member_token`: 1 DOTM (new registrations)
- `purchase_rewards`: 10.33% cashback in DOTM

### 6. API Services (`api_services`)
Integration and developer tools.

**Available Services**:
- `oxio_integration`: $0.00 (membership required)
- `stripe_integration`: 2.9% + $0.30 per transaction

### 7. Support Services (`support_services`)
Customer assistance tiers.

**Available Services**:
- `standard_support`: $0.00 (all users)
- `priority_support`: $0.00 (members only)
- `premium_support`: $0.00 (full members only)

---

## Service Object Schema

```json
{
  "id": "string",
  "name": "string",
  "description": "string",
  "type": "one_time_purchase|monthly_subscription|annual_subscription|beta_program|add_on|...",
  "price_usd": "number",
  "price_cad": "number (optional)",
  "billing_cycle": "monthly|yearly|one_time (optional)",
  "features": ["array of strings"],
  "availability": "Available|Beta Testing|Invitation Only|Limited Edition|Members Only",
  "token_amount": "string (optional)",
  "reward_percentage": "string (optional)",
  "processing_fee": "string (optional)",
  "response_time": "string (optional for support services)",
  "default_enabled": "boolean (optional)"
}
```

---

## Error Handling

### Standard Error Response
```json
{
  "error": "Error message",
  "message": "Detailed error description (optional)",
  "usage": "Usage instructions (optional)"
}
```

### HTTP Status Codes
- `200`: Success
- `400`: Bad Request (missing parameters)
- `404`: Not Found (service not found)
- `503`: Service Unavailable (MCP server unavailable)

---

## Usage Examples

### Python
```python
import requests

# Get all services
response = requests.get('https://get-dot-esim.replit.app/mcp/api')
data = response.json()
print(f"Platform: {data['platform']}")
print(f"Total categories: {len(data['services'])}")

# Get specific service
service_response = requests.get('https://get-dot-esim.replit.app/mcp/service/basic_membership')
service = service_response.json()
print(f"Service: {service['service']['name']} - ${service['service']['price_cad']}")

# Calculate pricing
calc_response = requests.get(
    'https://get-dot-esim.replit.app/mcp/calculate',
    params={'services': 'basic_membership,network_security_basic'}
)
pricing = calc_response.json()
print(f"Monthly cost: ${pricing['pricing']['monthly_recurring']}")
```

### JavaScript/Node.js
```javascript
const axios = require('axios');

async function getMCPData() {
  try {
    // Get all services
    const response = await axios.get('https://get-dot-esim.replit.app/mcp/api');
    console.log('Services:', Object.keys(response.data.services));
    
    // Calculate pricing
    const services = ['basic_membership', 'network_vpn_access'];
    const calcResponse = await axios.get('https://get-dot-esim.replit.app/mcp/calculate', {
      params: { services: services.join(',') }
    });
    
    console.log('Total first year cost:', calcResponse.data.pricing.first_year_total);
  } catch (error) {
    console.error('Error:', error.response?.data || error.message);
  }
}
```

### cURL
```bash
# Get service catalog
curl -X GET "https://get-dot-esim.replit.app/mcp/api" \
  -H "Accept: application/json"

# Get specific service
curl -X GET "https://get-dot-esim.replit.app/mcp/service/basic_membership" \
  -H "Accept: application/json"

# Calculate pricing for multiple services
curl -X GET "https://get-dot-esim.replit.app/mcp/calculate?services=basic_membership,network_security_basic,network_vpn_access" \
  -H "Accept: application/json"
```

---

## Changelog

### Version 1.0 (January 2025)
- Initial release of MCP server
- Complete service catalog implementation
- Pricing calculator functionality
- Privacy-compliant design
- Responsive web interface

---

*This API reference is automatically generated from the live MCP server implementation.*
