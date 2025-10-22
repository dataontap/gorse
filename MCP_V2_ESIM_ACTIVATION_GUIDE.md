# eSIM Activation via MCP v2 Server - Complete Guide

## Overview

The DOTM Platform now supports AI-driven eSIM activation through ChatGPT and Gemini AI using the Model Context Protocol (MCP) v2 server. This enables users to activate their eSIMs by simply asking an AI assistant, with full payment verification and OXIO integration.

## Architecture

```
User → AI Assistant (ChatGPT/Gemini) 
      ↓ JSON-RPC 2.0
MCP v2 Server (/mcp/v2/messages)
      ↓ Payment Verification
Stripe Purchase Database (esim_beta)
      ↓ eSIM Provisioning
OXIO API Integration
      ↓ Email Delivery
User receives eSIM QR code
```

## Features

### ✅ Implemented Components

1. **MCP v2 Server Integration** (`mcp_server_v2.py`)
   - JSON-RPC 2.0 protocol support
   - 5 Tools: calculate_pricing, search_services, get_service_details, compare_memberships, **activate_esim**
   - 7 Resources: Service catalog, pricing, membership plans
   - 3 Prompts: Plan recommendations, service explanations, cost optimization

2. **Stripe Payment Verification**
   - Queries `purchases` table for `esim_beta` product
   - Verifies user paid $1 before activation
   - Returns clear error message if payment missing
   - Secure Firebase UID → Stripe purchase linkage

3. **OXIO Integration**
   - Reuses existing `activate_esim_for_user()` function
   - Provisions eSIM via OXIO staging API
   - Assigns phone number
   - Generates eSIM QR code
   - Sends confirmation email with activation details

4. **Security & Validation**
   - Firebase authentication (Bearer token)
   - Email verification against Firebase UID
   - Payment verification before activation
   - Duplicate activation prevention

## API Endpoints

### 1. MCP Server Info
```bash
GET http://localhost:5000/mcp/v2
```

**Response:**
```json
{
  "server": "DOTM MCP Server",
  "version": "2.0.0",
  "protocol_version": "2024-11-05",
  "endpoints": {
    "messages": "/mcp/v2/messages"
  }
}
```

### 2. eSIM Activation via JSON-RPC

```bash
POST http://localhost:5000/mcp/v2/messages
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "activate_esim",
    "arguments": {
      "email": "user@example.com",
      "firebase_uid": "firebase_user_123"
    }
  }
}
```

**Success Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [{
      "type": "text",
      "text": "{
        \"success\": true,
        \"message\": \"eSIM activation successful!\",
        \"details\": {
          \"email\": \"user@example.com\",
          \"phone_number\": \"+1234567890\",
          \"plan\": \"OXIO Base Plan (Basic Membership)\",
          \"status\": \"Active\",
          \"activation_id\": \"line_abc123\",
          \"purchase_verified\": true
        },
        \"next_steps\": [
          \"Check your email for eSIM activation details and QR code\",
          \"Log into your DOTM dashboard to view your phone number\",
          \"Scan the QR code with your device to activate eSIM\"
        ]
      }"
    }]
  }
}
```

**Invoice Sent Response (No Payment Found):**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [{
      "type": "text",
      "text": "{
        \"success\": false,
        \"status\": \"invoice_sent\",
        \"message\": \"I've sent a $1 invoice to user@example.com for eSIM activation. Please check your email and pay the invoice, then ask me to activate again.\",
        \"invoice_url\": \"https://invoice.stripe.com/i/acct_.../...\",
        \"invoice_id\": \"in_1ABC123...\",
        \"amount_due\": 1.00,
        \"next_steps\": [
          \"Check user@example.com for the Stripe invoice\",
          \"Pay the $1 invoice\",
          \"Come back and say 'activate my eSIM' again\"
        ]
      }"
    }]
  }
}
```

## How AI Assistants Use It

### ChatGPT Workflow

#### First Attempt (New User, No Payment)

1. **User Request:** "I want to activate my eSIM"
2. **ChatGPT:** Authenticates user with Firebase Bearer token
3. **ChatGPT:** Connects to `/mcp/v2/messages` endpoint
4. **ChatGPT:** Calls `initialize` method to establish connection
5. **ChatGPT:** Calls `tools/list` to discover `activate_esim` tool
6. **ChatGPT:** Calls `tools/call` with user's email and Firebase UID
7. **Server:** Checks if user exists - **not found**
8. **Server:** **Auto-creates new user** with email from ChatGPT ✨
9. **Server:** Checks database for `esim_beta` purchase - **not found**
10. **Server:** Creates Stripe invoice for $1 and sends to user's email
11. **Server:** Returns `invoice_sent` status with invoice URL
12. **ChatGPT:** Tells user: "I've sent a $1 invoice to your email. Please pay it and come back!"
13. **User:** Receives email, clicks link, pays $1 via Stripe
14. **Stripe:** Sends webhook to DOTM → Purchase recorded in database

#### Second Attempt (After Payment)

13. **User:** "I paid the invoice, activate my eSIM"
14. **ChatGPT:** Calls `activate_esim` tool again
15. **Server:** Checks database - **payment found!** ✅
16. **Server:** Activates eSIM via OXIO integration
17. **Server:** Returns success response with phone number
18. **ChatGPT:** "Your eSIM is activated! Your phone number is +1..."

### Gemini Workflow

Same as ChatGPT, with additional capabilities:
- Multimodal context (can read user's screen showing DOTM app)
- Batch operations (can query service details and activate in one flow)
- Enhanced error recovery

## Testing

### Quick Test: List Available Tools

```bash
curl -X POST http://localhost:5000/mcp/v2/messages \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list"
  }'
```

You should see `activate_esim` in the tools list.

### End-to-End Test Suite

Run the comprehensive test suite:

```bash
python3 tests/test_end_to_end_esim_activation.py
```

**Tests included:**
1. ✅ MCP Server Health Check
2. ✅ Initialize Connection
3. ✅ Verify activate_esim Tool
4. ✅ Payment Verification Logic
5. ✅ User Validation Logic
6. ✅ Full Workflow Documentation

### ChatGPT Integration Tests

```bash
python3 tests/test_mcp_chatgpt_esim.py
```

**Tests included (6 scenarios):**
- Initialization
- Tool discovery
- Verified user activation
- Unverified user rejection
- Parameter validation
- Full conversation flow

### Gemini Integration Tests

```bash
python3 tests/test_mcp_gemini_esim.py
```

**Tests included (7 scenarios):**
- Connection establishment
- Capability discovery
- Happy path activation
- Error handling (email mismatch, missing user)
- Multimodal context simulation
- Conversation flow
- Batch operations

## Database Schema

### Purchases Table

The activation tool queries this table:

```sql
SELECT PurchaseID, DateCreated, StripeTransactionID 
FROM purchases 
WHERE FirebaseUID = %s 
AND StripeProductID = 'esim_beta'
ORDER BY DateCreated DESC 
LIMIT 1
```

**Key fields:**
- `FirebaseUID`: Links to authenticated user
- `StripeProductID`: Must be `'esim_beta'`
- `StripeTransactionID`: Stripe payment confirmation
- `DateCreated`: Purchase timestamp

## Security Considerations

### Authentication Flow

1. **Firebase Bearer Token:** AI assistant must provide valid Firebase auth token
2. **Email Verification:** Provided email must match Firebase user's email
3. **Payment Verification:** User must have valid Stripe purchase for `esim_beta`
4. **OXIO Integration:** Uses secure API credentials from environment variables

### Error Messages

All error messages are user-friendly and don't expose system internals:
- ✅ "Payment required" instead of "Database query failed"
- ✅ "User not found" instead of "Firebase lookup returned null"
- ✅ "Email mismatch" instead of "Authentication token invalid"

## Integration with Existing Systems

### Stripe Webhook Flow

When user purchases eSIM beta ($1):

1. User clicks "Buy eSIM Beta" on website
2. Stripe checkout session created
3. User completes payment
4. Stripe webhook fires → `/stripe/webhook/...`
5. `record_purchase()` inserts into `purchases` table:
   - StripeProductID: `'esim_beta'`
   - FirebaseUID: User's Firebase UID
   - Amount: 100 (cents)
6. Purchase is now available for MCP activation verification

### OXIO Activation Flow

The MCP server reuses the existing activation function:

```python
result = activate_esim_for_user(firebase_uid, mock_session)
```

This function:
1. Creates OXIO user (if doesn't exist)
2. Provisions eSIM line
3. Assigns phone number from inventory
4. Generates QR code
5. Stores activation in `oxio_activations` table
6. Sends confirmation email

## Deployment Checklist

Before enabling ChatGPT/Gemini integration:

- [ ] Verify MCP v2 server endpoint is accessible: `GET /mcp/v2`
- [ ] Test payment verification with real Stripe purchase
- [ ] Confirm OXIO API credentials are configured
- [ ] Test email delivery for activation confirmations
- [ ] Run end-to-end test suite successfully
- [ ] Configure AI assistant with MCP server URL
- [ ] Test with real user account (purchase → activation)

## Troubleshooting

### "Server object has no attribute _tool_manager"

**Fixed!** This was resolved by storing handler references in `MCPDOTMServer.handlers` dict.

### "Payment required" error for users who paid

Check:
1. User's Firebase UID matches purchase record
2. `StripeProductID` is exactly `'esim_beta'` (case-sensitive)
3. Purchase exists in database: `SELECT * FROM purchases WHERE FirebaseUID = '...'`

### "User not found" error

Check:
1. User is registered in system: `get_user_by_firebase_uid(firebase_uid)`
2. Firebase UID is correct (not email)
3. User completed signup process

### Activation succeeds but no email received

Check:
1. SMTP credentials configured in environment
2. Email service is running
3. User's email address is valid
4. Check email logs for delivery errors

## Future Enhancements

Potential improvements for v2.1:

1. **Multiple eSIM Support:** Allow users to activate multiple eSIMs
2. **Family Plans:** Support activating eSIMs for family members
3. **Real-time Status:** WebSocket updates for activation progress
4. **Retry Mechanism:** Auto-retry failed OXIO API calls
5. **Analytics:** Track activation success rates and common errors
6. **Internationalization:** Support multiple languages in AI responses

## API Specification

Full MCP v2 specification: https://modelcontextprotocol.io/specification/2024-11-05

## Support

For issues or questions:
1. Check server logs: `GET /mcp/v2` (health check)
2. Review test suites for working examples
3. Verify database connection and Stripe integration
4. Test OXIO API connectivity

---

**Built with ❤️ for the DOTM Platform**
*Revolutionizing mobile services with AI integration*
