# MCP Security & Authentication Guide

## Overview

The DOTM Platform MCP server now features enterprise-grade security with API key authentication and rate limiting to protect against unauthorized access and abuse.

## 🔐 Security Features

### 1. **API Key Authentication**
- All MCP endpoints require a valid API key
- Keys use cryptographic hashing (SHA-256) for secure storage
- Format: `mcp_` + 42 random characters
- Bearer token authentication: `Authorization: Bearer mcp_...`

### 2. **Rate Limiting**
- Configurable per-key rate limits (default: 1000 requests/hour)
- Automatic request tracking and quota management
- Graceful rate limit responses with retry information
- Rate limit headers included in all responses

### 3. **Request Logging & Analytics**
- Comprehensive logging of all API requests
- IP address and user agent tracking
- Request path and method recording
- Response status tracking for security auditing

### 4. **Operational Security**
- Automatic cleanup of old request logs (24-hour retention)
- Database-backed key management
- Support for key revocation
- Firebase UID linking for user-specific keys

---

## 📋 API Key Management

### Creating an API Key

**Endpoint:** `POST /api/admin/mcp-keys/create`

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "admin_key": "your_admin_key",
  "key_name": "ChatGPT Integration",
  "description": "API key for ChatGPT MCP access",
  "rate_limit": 1000,
  "firebase_uid": "optional_user_id",
  "allowed_origins": ["https://chatgpt.com"]
}
```

**Response:**
```json
{
  "success": true,
  "api_key": "mcp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "message": "API key 'ChatGPT Integration' created successfully",
  "warning": "Save this API key securely. It will not be shown again."
}
```

⚠️ **IMPORTANT:** The API key is only shown once. Store it securely immediately.

### Listing API Keys

**Endpoint:** `GET /api/admin/mcp-keys/list?admin_key=xxx`

**Response:**
```json
{
  "success": true,
  "api_keys": [
    {
      "id": 1,
      "key_name": "ChatGPT Integration",
      "description": "API key for ChatGPT MCP access",
      "rate_limit": 1000,
      "is_active": true,
      "created_at": "2025-10-27T12:00:00Z",
      "last_used_at": "2025-10-27T13:30:00Z",
      "total_requests": 245
    }
  ]
}
```

### Revoking an API Key

**Endpoint:** `POST /api/admin/mcp-keys/revoke/{key_id}`

**Request Body:**
```json
{
  "admin_key": "your_admin_key"
}
```

---

## 🔑 Using API Keys

### Authentication Header

All requests to MCP endpoints must include:

```
Authorization: Bearer mcp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Example: ChatGPT MCP Configuration

```json
{
  "mcpServers": {
    "dotm": {
      "url": "https://get-dot-eSIM.replit.app/mcp/v2/messages",
      "headers": {
        "Authorization": "Bearer mcp_your_api_key_here"
      }
    }
  }
}
```

### Example: HTTP Request

```bash
curl -X POST https://get-dot-eSIM.replit.app/mcp/v2/messages \
  -H "Authorization: Bearer mcp_xxxxx..." \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {}
  }'
```

---

## 📊 Rate Limiting

### How It Works

- Each API key has a configurable rate limit (requests per hour)
- Requests are tracked in a sliding window
- When limit is exceeded, HTTP 429 is returned
- Rate limit resets on a rolling 1-hour basis

### Rate Limit Response Headers

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 823
X-RateLimit-Reset: 2025-10-27T14:30:00Z
```

### Rate Limit Exceeded Response

```json
{
  "error": "Rate Limit Exceeded",
  "message": "API key has exceeded rate limit",
  "rate_limit": {
    "allowed": false,
    "current_usage": 1000,
    "limit": 1000,
    "percentage": 100.0,
    "reset_at": "2025-10-27T14:30:00Z"
  }
}
```

---

## 🛡️ Security Best Practices

### For API Key Holders

1. **Never commit API keys to version control**
   - Use environment variables
   - Add `.env` files to `.gitignore`
   - Use secret management systems

2. **Rotate keys regularly**
   - Create new keys periodically
   - Revoke old keys after transition
   - Update all integrations

3. **Use appropriate rate limits**
   - Set realistic limits for your use case
   - Monitor usage to detect anomalies
   - Request limit increases if needed

4. **Restrict by origin (when supported)**
   - Specify allowed domains/IPs
   - Use HTTPS for all requests
   - Implement client-side security

### For Administrators

1. **Monitor API usage**
   - Review request logs regularly
   - Check for unusual patterns
   - Track failed authentication attempts

2. **Manage keys lifecycle**
   - Revoke unused keys
   - Link keys to Firebase UIDs when possible
   - Maintain audit trail

3. **Set appropriate limits**
   - Balance security with usability
   - Increase limits for verified users
   - Lower limits for new/untrusted sources

---

## 🔄 Migration Guide

### Upgrading Existing Integrations

If you're currently using the MCP server without authentication:

1. **Create an API key** via the admin panel
2. **Update your configuration** to include the Authorization header
3. **Test the integration** with the new key
4. **Monitor rate limit usage** to ensure limits are appropriate

### Example: Updating ChatGPT Configuration

**Before:**
```json
{
  "mcpServers": {
    "dotm": {
      "url": "https://get-dot-eSIM.replit.app/mcp/v2/messages"
    }
  }
}
```

**After:**
```json
{
  "mcpServers": {
    "dotm": {
      "url": "https://get-dot-eSIM.replit.app/mcp/v2/messages",
      "headers": {
        "Authorization": "Bearer mcp_xxxxx..."
      }
    }
  }
}
```

---

## 🚀 Admin Interface

Access the MCP API key management interface at:

**URL:** `https://get-dot-eSIM.replit.app/admin/mcp-keys`

Features:
- ✅ Create new API keys
- ✅ View all keys and their usage statistics
- ✅ Revoke compromised or unused keys
- ✅ Monitor rate limit usage
- ✅ Link keys to specific users

---

## 📞 Support

For API key requests, rate limit increases, or security concerns:

- **Email:** support@dotm.app
- **Documentation:** https://get-dot-eSIM.replit.app/mcp/v2/docs
- **Status:** Monitor API health and rate limits via your admin dashboard

---

## 🔧 Technical Details

### Database Schema

```sql
-- API Keys Table
CREATE TABLE mcp_api_keys (
    id SERIAL PRIMARY KEY,
    key_hash VARCHAR(64) UNIQUE NOT NULL,
    key_name VARCHAR(255) NOT NULL,
    description TEXT,
    rate_limit INTEGER DEFAULT 1000,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP,
    total_requests BIGINT DEFAULT 0,
    firebase_uid VARCHAR(128),
    allowed_origins TEXT[],
    metadata JSONB
);

-- Request Tracking Table
CREATE TABLE mcp_api_requests (
    id SERIAL PRIMARY KEY,
    key_hash VARCHAR(64) NOT NULL,
    request_path VARCHAR(255),
    request_method VARCHAR(10),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT,
    response_status INTEGER
);
```

### Key Hashing

API keys are hashed using SHA-256 before storage:
- Original key: `mcp_abcdef123456...`
- Stored hash: `a1b2c3d4e5f6...` (64 characters)
- Hash algorithm: SHA-256
- No salt (keys are cryptographically random)

---

## ✅ Compliance & Audit

- All API requests are logged with timestamps
- IP addresses are tracked for security auditing
- Request/response pairs can be reviewed
- 24-hour log retention (configurable)
- GDPR-compliant data handling
