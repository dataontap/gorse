
# MCP Server API Reference

## Base URL
```
https://gorse.dotmobile.app/mcp
```

## Protocol
**Model Context Protocol (MCP) 2024-11-05**  
Message Format: JSON-RPC 2.0  
Transport: HTTP + SSE (Server-Sent Events)

## Authentication
Firebase Bearer token (optional) - enables user-specific features and auto-registration.

**Header**:
```
Authorization: Bearer <firebase_jwt_token>
```

## Rate Limiting
- Standard rate limiting applies
- Recommended: 100 requests per minute
- No hard limits for authenticated requests

---

## HTTP Endpoints

### GET `/mcp`
Server information and capabilities.

**Response Format**:
```json
{
  "server": "DOTM MCP Server",
  "version": "2.0.0",
  "protocol_version": "2024-11-05",
  "transport": "HTTP + SSE (Streamable HTTP)",
  "capabilities": {
    "resources": {"subscribe": false, "listChanged": true},
    "tools": {"listChanged": true},
    "prompts": {"listChanged": false}
  },
  "endpoints": {
    "info": "/mcp",
    "messages": "/mcp/messages",
    "docs": "/mcp/docs"
  },
  "authentication": {
    "type": "Firebase Bearer Token",
    "required": false,
    "auto_registration": true
  }
}
```

---

### POST `/mcp/messages`
JSON-RPC 2.0 endpoint for all MCP protocol operations.

**Content-Type**: `application/json`

**Request Format**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "method_name",
  "params": { ... }
}
```

**Response Format**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": { ... }
}
```

**Error Format**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32601,
    "message": "Method not found"
  }
}
```

---

### GET `/mcp/docs`
API documentation with comprehensive examples.

**Response Format**: JSON with complete API documentation, available methods, resources, tools, and prompts.

---

## JSON-RPC Methods

### `initialize`
Initialize client connection to the MCP server.

**Request**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "clientInfo": {"name": "my-client", "version": "1.0"}
  }
}
```

**Response**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "resources": {"subscribe": false, "listChanged": true},
      "tools": {"listChanged": true},
      "prompts": {"listChanged": false}
    },
    "serverInfo": {"name": "dotm-mcp-server", "version": "2.0.0"}
  }
}
```

---

### `resources/list`
Get all available resources (service catalog, pricing info, etc.).

**Request**:
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "resources/list"
}
```

**Response**:
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "resources": [
      {
        "uri": "dotm://services/catalog",
        "name": "Service Catalog",
        "description": "Complete DOTM service catalog",
        "mimeType": "application/json"
      },
      {
        "uri": "dotm://services/membership",
        "name": "Membership Plans",
        "description": "Annual subscription plans",
        "mimeType": "application/json"
      },
      {
        "uri": "dotm://services/network",
        "name": "Network Features",
        "description": "Network add-on services",
        "mimeType": "application/json"
      },
      {
        "uri": "dotm://pricing/summary",
        "name": "Pricing Summary",
        "description": "Cost calculations and summaries",
        "mimeType": "application/json"
      }
    ]
  }
}
```

---

### `resources/read`
Read content from a specific resource.

**Request**:
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "resources/read",
  "params": {
    "uri": "dotm://services/catalog"
  }
}
```

**Response**:
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "contents": [
      {
        "uri": "dotm://services/catalog",
        "mimeType": "application/json",
        "text": "{\"services\": {...}, \"categories\": [...]}"
      }
    ]
  }
}
```

---

### `tools/list`
Get all available tools.

**Request**:
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "tools/list"
}
```

**Response**:
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "result": {
    "tools": [
      {
        "name": "calculate_pricing",
        "description": "Calculate total cost for selected services",
        "inputSchema": {
          "type": "object",
          "properties": {
            "service_ids": {
              "type": "array",
              "items": {"type": "string"}
            }
          },
          "required": ["service_ids"]
        }
      },
      {
        "name": "search_services",
        "description": "Search services by keyword, type, or price",
        "inputSchema": {
          "type": "object",
          "properties": {
            "query": {"type": "string"},
            "max_price": {"type": "number"}
          }
        }
      },
      {
        "name": "get_service_details",
        "description": "Get detailed information about a service",
        "inputSchema": {
          "type": "object",
          "properties": {
            "service_id": {"type": "string"}
          },
          "required": ["service_id"]
        }
      },
      {
        "name": "compare_memberships",
        "description": "Compare Basic and Full membership plans",
        "inputSchema": {
          "type": "object",
          "properties": {
            "include_addons": {"type": "boolean"}
          }
        }
      }
    ]
  }
}
```

---

### `tools/call`
Execute a specific tool.

**Request (Calculate Pricing)**:
```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "method": "tools/call",
  "params": {
    "name": "calculate_pricing",
    "arguments": {
      "service_ids": ["basic_membership", "network_vpn_access"]
    }
  }
}
```

**Response**:
```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Total Cost Analysis:\n- Basic Membership: $24.00/year\n- VPN Access: $8.00/month\n\nTotal: $24.00/year + $96.00/year\nGrand Total: $120.00/year"
      }
    ]
  }
}
```

---

### `prompts/list`
Get all available prompts.

**Request**:
```json
{
  "jsonrpc": "2.0",
  "id": 6,
  "method": "prompts/list"
}
```

**Response**:
```json
{
  "jsonrpc": "2.0",
  "id": 6,
  "result": {
    "prompts": [
      {
        "name": "recommend_plan",
        "description": "Get personalized membership plan recommendation",
        "arguments": [
          {
            "name": "usage_type",
            "description": "Primary usage: data_only, talk_text, international",
            "required": true
          },
          {
            "name": "budget",
            "description": "Monthly budget in USD",
            "required": false
          }
        ]
      }
    ]
  }
}
```

---

### `prompts/get`
Get a specific prompt with arguments.

**Request**:
```json
{
  "jsonrpc": "2.0",
  "id": 7,
  "method": "prompts/get",
  "params": {
    "name": "recommend_plan",
    "arguments": {
      "usage_type": "talk_text",
      "budget": "30"
    }
  }
}
```

**Response**:
```json
{
  "jsonrpc": "2.0",
  "id": 7,
  "result": {
    "description": "Personalized plan recommendation",
    "messages": [
      {
        "role": "user",
        "content": {
          "type": "text",
          "text": "Based on talk_text usage with a $30 budget, I recommend Full Membership..."
        }
      }
    ]
  }
}
```

---

## Available Resources

| URI | Name | Description |
|-----|------|-------------|
| `dotm://services/catalog` | Service Catalog | Complete listing of 20+ services |
| `dotm://services/membership` | Membership Plans | Basic and Full membership details |
| `dotm://services/network` | Network Features | VPN, Security, and network add-ons |
| `dotm://pricing/summary` | Pricing Summary | Cost calculations and summaries |

---

## Available Tools

| Tool Name | Description | Required Arguments |
|-----------|-------------|-------------------|
| `calculate_pricing` | Calculate total cost for services | `service_ids` (array) |
| `search_services` | Search services by criteria | `query` (string, optional) |
| `get_service_details` | Get detailed service info | `service_id` (string) |
| `compare_memberships` | Compare membership plans | `include_addons` (bool, optional) |

---

## Error Codes (JSON-RPC 2.0)

| Code | Meaning | Description |
|------|---------|-------------|
| -32700 | Parse error | Invalid JSON |
| -32600 | Invalid Request | Invalid JSON-RPC request |
| -32601 | Method not found | Method doesn't exist |
| -32602 | Invalid params | Invalid method parameters |
| -32603 | Internal error | Server-side error |

---

## Usage Examples

### Python
```python
import requests
import json

BASE_URL = "https://gorse.dotmobile.app/mcp/messages"

# Initialize connection
init_request = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "python-client", "version": "1.0"}
    }
}

response = requests.post(BASE_URL, json=init_request)
print(response.json())

# Get service catalog
catalog_request = {
    "jsonrpc": "2.0",
    "id": 2,
    "method": "resources/read",
    "params": {"uri": "dotm://services/catalog"}
}

response = requests.post(BASE_URL, json=catalog_request)
catalog = response.json()["result"]["contents"][0]["text"]
print(catalog)

# Calculate pricing
pricing_request = {
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
        "name": "calculate_pricing",
        "arguments": {
            "service_ids": ["basic_membership", "network_vpn_access"]
        }
    }
}

response = requests.post(BASE_URL, json=pricing_request)
result = response.json()["result"]["content"][0]["text"]
print(result)
```

### JavaScript
```javascript
const BASE_URL = 'https://gorse.dotmobile.app/mcp/messages';

async function callMCP(method, params = {}) {
  const response = await fetch(BASE_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      jsonrpc: '2.0',
      id: Math.floor(Math.random() * 1000),
      method,
      params
    })
  });
  return response.json();
}

// Initialize
const initResult = await callMCP('initialize', {
  protocolVersion: '2024-11-05',
  capabilities: {},
  clientInfo: { name: 'js-client', version: '1.0' }
});

console.log('Server initialized:', initResult);

// List resources
const resources = await callMCP('resources/list');
console.log('Available resources:', resources.result.resources);

// Calculate pricing
const pricing = await callMCP('tools/call', {
  name: 'calculate_pricing',
  arguments: { service_ids: ['basic_membership'] }
});

console.log('Pricing:', pricing.result.content[0].text);
```

### cURL
```bash
# Get server information
curl https://gorse.dotmobile.app/mcp

# Initialize connection
curl -X POST https://gorse.dotmobile.app/mcp/messages \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {"name": "curl-client", "version": "1.0"}
    }
  }'

# List all resources
curl -X POST https://gorse.dotmobile.app/mcp/messages \
  -H "Content-Type": application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "resources/list"
  }'

# Read service catalog
curl -X POST https://gorse.dotmobile.app/mcp/messages \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "resources/read",
    "params": {"uri": "dotm://services/catalog"}
  }'

# Calculate pricing
curl -X POST https://gorse.dotmobile.app/mcp/messages \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 4,
    "method": "tools/call",
    "params": {
      "name": "calculate_pricing",
      "arguments": {
        "service_ids": ["basic_membership", "network_vpn_access"]
      }
    }
  }'

# With authentication
curl -X POST https://gorse.dotmobile.app/mcp/messages \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <firebase_token>" \
  -d '{
    "jsonrpc": "2.0",
    "id": 5,
    "method": "resources/read",
    "params": {"uri": "dotm://services/catalog"}
  }'
```

---

## Integration with AI Services

### ChatGPT Configuration
Add to ChatGPT custom instructions or GPTs configuration:
```
Use the DOTM MCP server at https://gorse.dotmobile.app/mcp/messages
Protocol: JSON-RPC 2.0
Available methods: initialize, resources/list, resources/read, tools/list, tools/call, prompts/list, prompts/get
```

### Claude Desktop Configuration
Add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "dotm-platform": {
      "command": "python",
      "args": ["-m", "mcp_server_v2"],
      "env": {
        "MCP_SERVER_URL": "https://gorse.dotmobile.app/mcp"
      }
    }
  }
}
```

---

## Changelog

### Version 2.0.0 (November 2024)
- Migrated to MCP 2024-11-05 specification
- Implemented JSON-RPC 2.0 protocol
- Added Resources, Tools, and Prompts
- Consolidated endpoints to /mcp structure
- Added optional Firebase authentication with auto-registration
- Removed legacy REST API endpoints

---

*Last Updated: November 24, 2025*  
*Protocol Version: MCP 2024-11-05*  
*Server Version: 2.0.0*

