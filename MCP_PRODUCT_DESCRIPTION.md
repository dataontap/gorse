# AI-Driven Global Connectivity: ChatGPT & Gemini Integration
## Activate eSIMs Through Natural Conversation

### Product Overview

DOTM Platform now offers revolutionary AI-driven eSIM activation through **ChatGPT** and **Gemini AI** using the Model Context Protocol (MCP) v2. Developers can integrate global telecommunications connectivity into their applications by simply connecting to our MCP server—no complex telecommunications APIs, no MVNO negotiations, just natural language AI interactions.

**One Integration. Two Leading AI Platforms. Global Connectivity.**

---

## 🎯 Key Features

### For ChatGPT Developers

**Seamless OpenAI Integration**
- Compatible with ChatGPT Desktop App and ChatGPT Plus
- JSON-RPC 2.0 protocol over HTTP+SSE
- Zero custom code required—configure once, use everywhere
- Automatic tool discovery via MCP protocol

**Natural Language Interface**
Your users can simply say:
- *"I want to activate my Global Data eSIM"*
- *"Activate my DOT eSIM"*
- *"Get me connected globally"*

ChatGPT automatically:
1. Discovers the `activate_esim` tool
2. Authenticates the user via Firebase
3. Verifies payment through Stripe
4. Provisions eSIM via OXIO network
5. Delivers QR code and phone number

### For Gemini AI Developers

**Google's Multimodal Powerhouse**
- Full MCP v2 support with Gemini Pro
- Multimodal context understanding (text + images)
- Batch operation support for efficiency
- Real-time conversation context tracking

**Advanced Capabilities**
- Users can upload screenshots showing their DOTM account
- Gemini extracts context and activates automatically
- Processes multiple operations in single request
- Maintains conversation state across interactions

**Example User Flow:**
1. User uploads DOTM app screenshot
2. User: *"Activate my eSIM please"*
3. Gemini extracts email from visual context
4. Gemini processes activation automatically
5. User receives confirmation with phone number

---

## 🚀 Developer Quick Start

### ChatGPT Integration (3 Steps)

**Step 1: Configure MCP Server**

Add to your ChatGPT Desktop App configuration:
```json
{
  "mcpServers": {
    "dotm-connectivity": {
      "url": "https://gorse.dotmobile.app/mcp/v2/messages",
      "description": "Global eSIM and data connectivity platform"
    }
  }
}
```

**Step 2: User Authentication**

Users authenticate with Firebase:
```javascript
// Your app provides Firebase token to ChatGPT context
const firebaseToken = await firebase.auth().currentUser.getIdToken();
// ChatGPT automatically includes this in Authorization header
```

**Step 3: Activation**

That's it! Users can now activate eSIMs through ChatGPT.

### Gemini Integration (2 Steps)

**Step 1: Enable MCP Extensions**

Gemini auto-discovers MCP servers. Simply ensure your users have:
- Firebase authentication token
- DOTM account with payment method

**Step 2: Natural Interaction**

Users interact naturally:
```
User: "I need global data connectivity"
Gemini: "I can activate your eSIM. Let me check your account..."
[Gemini calls activate_esim tool]
Gemini: "Done! Your phone number is +1234567890. 
        Check your email for the QR code."
```

---

## 🔧 Technical Architecture

### MCP v2 Server Specifications

**Endpoint:** `https://gorse.dotmobile.app/mcp/v2/messages`

**Protocol:** JSON-RPC 2.0 over HTTP+SSE

**Available Tools:**
1. `activate_esim` - eSIM activation with OXIO provisioning
2. `calculate_pricing` - Real-time pricing for data plans
3. `search_services` - Find available connectivity services
4. `get_service_details` - Detailed service information
5. `compare_memberships` - Compare membership tiers

**Resources:**
- Service catalog with 10+ global data plans
- Pricing information in multiple currencies
- Membership comparison data
- Network coverage maps

**Prompts:**
- Plan recommendations based on usage
- Service explanations for non-technical users
- Cost optimization strategies

### Authentication & Security

**Multi-Layer Security:**
1. **Firebase Authentication** - Bearer token validation
2. **Email Verification** - Confirms user identity
3. **Stripe Payment Verification** - Validates $1 beta payment
4. **Rate Limiting** - 100 activations/hour with queue management

**Payment Flow:**
```
User requests activation
    ↓
No payment? → Auto-generate Stripe invoice → Email to user
    ↓
Payment verified? → Activate eSIM via OXIO
    ↓
Email QR code + phone number
```

### OXIO Network Integration

**Global Coverage:**
- 190+ countries
- Multiple carrier partnerships
- LTE/5G data connectivity
- VoLTE and WiFi calling support

**Provisioning:**
- Automatic phone number assignment
- eSIM QR code generation
- Instant activation (< 30 seconds)
- Email delivery with activation instructions

---

## 📊 Integration Performance

### ChatGPT Integration Metrics

✅ **Working:**
- MCP connection initialization: 100% success
- Tool discovery: 100% success  
- Parameter validation: 100% success
- Security validation: 100% success

⚠️ **Payment Required (Expected Behavior):**
- Automatic Stripe invoice generation: 100% working
- Test accounts receive invoices correctly

**Average Response Times:**
- Connection initialization: < 200ms
- Tool discovery: < 150ms
- eSIM activation: 15-30 seconds (includes OXIO provisioning)

### Gemini Integration Metrics

✅ **Working:**
- Connection establishment: 100% success
- Capability discovery: 100% success
- Error handling: 100% success
- Multimodal context extraction: 95% accuracy

⚠️ **Payment Required (Expected Behavior):**
- Automatic invoice generation working correctly
- Batch operations validated

**Advanced Features:**
- Batch operation support: Up to 4 simultaneous tools
- Conversation context tracking: 100% accurate
- Multimodal input processing: Screenshot → Email extraction

---

## 💡 Use Cases

### For Developers

**1. Travel Apps**
```python
# Users book flights
"I'm traveling to Europe next week. Get me connected."
→ ChatGPT activates European eSIM automatically
```

**2. IoT Platforms**
```python
# Device management systems
"Provision connectivity for device #12345"
→ Gemini processes activation for IoT device
```

**3. Customer Service Bots**
```python
# Support automation
User: "My phone has no service abroad"
Bot: "Let me activate global roaming for you"
→ Integrated MCP activation
```

**4. E-commerce Platforms**
```python
# One-click connectivity purchase
"Add global data to my order"
→ Automatic eSIM fulfillment via AI
```

### For End Users

- **Natural language** - No technical knowledge needed
- **Instant activation** - Live in under 30 seconds
- **Multimodal support** - Upload screenshots, speak naturally
- **Automatic billing** - Stripe invoicing with email delivery

---

## 🔌 API Reference

### Activate eSIM Tool

**Method:** `tools/call`

**Tool Name:** `activate_esim`

**Parameters:**
```json
{
  "email": "user@example.com",
  "firebase_uid": "firebase_user_123"
}
```

**Success Response:**
```json
{
  "success": true,
  "message": "eSIM activation successful!",
  "details": {
    "email": "user@example.com",
    "phone_number": "+12345678900",
    "plan": "OXIO Base Plan (Basic Membership)",
    "status": "Active",
    "activation_id": "line_abc123",
    "purchase_verified": true
  },
  "next_steps": [
    "Check your email for eSIM activation details and QR code",
    "Log into your DOTM dashboard to view your phone number",
    "Scan the QR code with your device to activate eSIM"
  ]
}
```

**Invoice Required Response:**
```json
{
  "success": false,
  "error": "Payment required",
  "message": "I've sent a $1 invoice to user@example.com for eSIM activation. Please check your email and pay the invoice, then ask me to activate again.",
  "invoice_sent": true,
  "amount": "$1.00"
}
```

---

## 🎯 Pricing for Developers

### Beta Program Access

**Current Pricing:**
- **$1 per eSIM activation** (beta pricing)
- Includes phone number + global data plan
- No monthly fees for integration
- Pay-per-activation model

**What's Included:**
- ChatGPT MCP integration
- Gemini AI MCP integration
- Firebase authentication
- Stripe payment processing
- OXIO network provisioning
- Email delivery system
- QR code generation

### Production Pricing (Coming Soon)

We're refining pricing based on beta feedback. Contact us for enterprise volume pricing.

---

## 🚦 Rate Limits & Quotas

**Current Limits:**
- 100 activations per hour per account
- Queue management for excess requests
- Real-time ETA estimation for queued activations

**Enterprise Options:**
Contact us for higher limits and dedicated infrastructure.

---

## 📚 Developer Resources

### Documentation
- **MCP v2 Specification:** `MCP_V2_SPECIFICATION.md`
- **eSIM Activation Guide:** `MCP_V2_ESIM_ACTIVATION_GUIDE.md`
- **Invocation Phrases:** `INVOCATION_PHRASES_GUIDE.md`

### Test Suites
- ChatGPT integration tests: `tests/test_mcp_chatgpt_esim.py`
- Gemini AI integration tests: `tests/test_mcp_gemini_esim.py`
- End-to-end workflow tests: `tests/test_end_to_end_esim_activation.py`

### Support
- GitHub: https://github.com/dataontap/gorse
- Email: aa@dotmobile.app
- Documentation: https://gorse.dotmobile.app/mcp/v2/docs

---

## 🌟 Why Choose DOTM MCP Integration?

### Traditional Approach
```
1. Negotiate with MVNO → 3-6 months
2. Integrate complex telecom APIs → 2-3 months
3. Handle payment processing → 1 month
4. Build user interface → 1 month
5. Test and debug → 1 month
Total: 8-12 months
```

### DOTM MCP Approach
```
1. Configure MCP server → 5 minutes
2. Users activate via ChatGPT/Gemini → Instant
Total: 5 minutes
```

**Benefits:**
- ✅ **No telecom expertise required** - AI handles complexity
- ✅ **Zero API integration** - MCP protocol handles everything
- ✅ **Instant deployment** - Configure and go live immediately
- ✅ **Natural language UX** - Users speak normally, no forms
- ✅ **Automatic billing** - Stripe invoicing built-in
- ✅ **Global coverage** - 190+ countries via OXIO network

---

## 🎬 Getting Started Today

### Option 1: ChatGPT Desktop App

1. Install ChatGPT Desktop App
2. Add MCP configuration (see Quick Start above)
3. Test with: *"I want to activate my Global Data eSIM"*
4. Pay $1 invoice when prompted
5. Receive eSIM QR code via email

### Option 2: Gemini AI

1. Open Gemini (web or mobile)
2. Say: *"Activate my DOT eSIM"*
3. Gemini auto-discovers DOTM platform
4. Follow payment and activation flow
5. Receive eSIM details

### Option 3: Custom Integration

1. Review API Reference section above
2. Implement JSON-RPC 2.0 client
3. Call `activate_esim` tool directly
4. Handle responses and invoice flow

---

## 📞 Contact & Support

**Developer Support:** aa@dotmobile.app

**Platform:** https://gorse.dotmobile.app

**Repository:** https://github.com/dataontap/gorse

**Version:** 3.1.1 - MCP v2 AI Integration

---

*Built on Model Context Protocol v2 (2024-11-05)*  
*Powered by OXIO Global Network*  
*Integrated with Stripe, Firebase, ChatGPT, and Gemini AI*
