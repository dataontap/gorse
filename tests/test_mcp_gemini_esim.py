#!/usr/bin/env python3
"""
Test Suite: Gemini AI Integration with MCP v2 Server - eSIM Activation
Simulates how Gemini would interact with the DOTM MCP v2 server to activate eSIMs
for authenticated users.
"""

import requests
import json
from typing import Dict, Any, List, Optional
import os
from datetime import datetime

# Configuration
BASE_URL = os.getenv("MCP_BASE_URL", "http://localhost:5000/mcp/v2")
MESSAGES_ENDPOINT = f"{BASE_URL}/messages"

# Test user data - Using production DOTM account
TEST_SCENARIOS = {
    "happy_path": {
        "description": "Verified user with valid email",
        "user": {
            "email": "aa@dotmobile.app",
            "firebase_uid": "dotm_verified_uid_001",
            "firebase_token": "gemini_test_token",
        },
        "expected_success": True
    },
    "email_mismatch": {
        "description": "Firebase UID with wrong email",
        "user": {
            "email": "wrong@dotm.test",
            "firebase_uid": "gemini_verified_uid_002",
            "firebase_token": "gemini_test_token",
        },
        "expected_success": False
    },
    "missing_user": {
        "description": "Non-existent Firebase UID",
        "user": {
            "email": "nonexistent@dotm.test",
            "firebase_uid": "nonexistent_uid_999",
            "firebase_token": "gemini_test_token",
        },
        "expected_success": False
    }
}


class GeminiMCPClient:
    """Simulates Gemini's interaction with MCP v2 server"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.conversation_context = []
        self.request_id = 1000  # Different from ChatGPT to distinguish
        
    def log_interaction(self, role: str, message: str):
        """Log conversation for context"""
        self.conversation_context.append({
            "timestamp": datetime.now().isoformat(),
            "role": role,
            "message": message
        })
    
    def json_rpc_call(self, method: str, params: Optional[Dict] = None, auth_token: Optional[str] = None) -> Dict[str, Any]:
        """Make JSON-RPC 2.0 call to MCP server"""
        request_payload = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method
        }
        
        if params:
            request_payload["params"] = params
        
        self.request_id += 1
        
        headers = {"Content-Type": "application/json"}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        
        try:
            response = requests.post(
                self.base_url,
                json=request_payload,
                headers=headers,
                timeout=30
            )
            return response.json()
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": request_payload["id"],
                "error": {"code": -32603, "message": str(e)}
            }
    
    def establish_connection(self) -> bool:
        """Establish MCP connection (Gemini style)"""
        print("\n🔷 Gemini: Establishing MCP v2 connection...")
        result = self.json_rpc_call(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "experimental": {}
                },
                "clientInfo": {
                    "name": "Google Gemini",
                    "version": "gemini-pro"
                }
            }
        )
        
        if "result" in result:
            self.log_interaction("system", "MCP connection established")
            return True
        return False
    
    def discover_capabilities(self) -> Dict[str, Any]:
        """Discover server capabilities and available tools"""
        print("\n🔷 Gemini: Discovering server capabilities...")
        
        # Get tools
        tools_result = self.json_rpc_call("tools/list")
        
        # Get resources
        resources_result = self.json_rpc_call("resources/list")
        
        # Get prompts
        prompts_result = self.json_rpc_call("prompts/list")
        
        return {
            "tools": tools_result.get("result", {}).get("tools", []),
            "resources": resources_result.get("result", {}).get("resources", []),
            "prompts": prompts_result.get("result", {}).get("prompts", [])
        }
    
    def execute_esim_activation(
        self,
        email: str,
        firebase_uid: str,
        auth_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute eSIM activation via MCP tool"""
        print(f"\n🔷 Gemini: Executing eSIM activation for {email}...")
        
        self.log_interaction("user", f"Activate eSIM for {email}")
        
        result = self.json_rpc_call(
            "tools/call",
            {
                "name": "activate_esim",
                "arguments": {
                    "email": email,
                    "firebase_uid": firebase_uid
                }
            },
            auth_token
        )
        
        if "result" in result:
            content = result["result"].get("content", [])
            if content:
                response_data = json.loads(content[0].get("text", "{}"))
                self.log_interaction("assistant", json.dumps(response_data, indent=2))
                return response_data
        
        return result


def test_gemini_connection():
    """Test 1: Gemini establishes MCP connection"""
    print("\n" + "="*60)
    print("TEST 1: Gemini Connection Establishment")
    print("="*60)
    
    client = GeminiMCPClient(MESSAGES_ENDPOINT)
    success = client.establish_connection()
    
    if success:
        print("✅ Gemini successfully connected to MCP server")
        return True
    else:
        print("❌ Gemini failed to connect")
        return False


def test_gemini_capability_discovery():
    """Test 2: Gemini discovers activate_esim capability"""
    print("\n" + "="*60)
    print("TEST 2: Gemini Capability Discovery")
    print("="*60)
    
    client = GeminiMCPClient(MESSAGES_ENDPOINT)
    client.establish_connection()
    
    capabilities = client.discover_capabilities()
    
    # Check for activate_esim tool
    activate_tool = next(
        (t for t in capabilities["tools"] if t["name"] == "activate_esim"),
        None
    )
    
    if activate_tool:
        print("✅ Gemini discovered activate_esim tool")
        print(f"   Description: {activate_tool['description']}")
        print(f"   Schema: {activate_tool['inputSchema']}")
        return True
    else:
        print("❌ activate_esim tool not found")
        available = [t["name"] for t in capabilities["tools"]]
        print(f"   Available tools: {available}")
        return False


def test_gemini_happy_path_activation():
    """Test 3: Gemini activates eSIM for valid user"""
    print("\n" + "="*60)
    print("TEST 3: Happy Path - Valid User Activation")
    print("="*60)
    
    scenario = TEST_SCENARIOS["happy_path"]
    user = scenario["user"]
    
    client = GeminiMCPClient(MESSAGES_ENDPOINT)
    client.establish_connection()
    
    result = client.execute_esim_activation(
        email=user["email"],
        firebase_uid=user["firebase_uid"],
        auth_token=user.get("firebase_token")
    )
    
    if isinstance(result, dict) and result.get("success"):
        print("✅ eSIM activation successful")
        print(f"   Email: {result['details']['email']}")
        print(f"   Phone: {result['details'].get('phone_number', 'N/A')}")
        print(f"   Status: {result['details']['status']}")
        return True
    else:
        print(f"❌ Activation failed: {result.get('message', 'Unknown error')}")
        return False


def test_gemini_error_handling():
    """Test 4: Gemini handles various error scenarios"""
    print("\n" + "="*60)
    print("TEST 4: Error Handling - Email Mismatch & Missing User")
    print("="*60)
    
    client = GeminiMCPClient(MESSAGES_ENDPOINT)
    client.establish_connection()
    
    test_results = []
    
    # Test email mismatch
    scenario1 = TEST_SCENARIOS["email_mismatch"]
    user1 = scenario1["user"]
    print(f"\n   Testing: {scenario1['description']}")
    
    result1 = client.execute_esim_activation(
        email=user1["email"],
        firebase_uid=user1["firebase_uid"],
        auth_token=user1.get("firebase_token")
    )
    
    if not result1.get("success"):
        print(f"   ✅ Correctly rejected: {result1.get('error')}")
        test_results.append(True)
    else:
        print("   ❌ Should have rejected email mismatch")
        test_results.append(False)
    
    # Test missing user
    scenario2 = TEST_SCENARIOS["missing_user"]
    user2 = scenario2["user"]
    print(f"\n   Testing: {scenario2['description']}")
    
    result2 = client.execute_esim_activation(
        email=user2["email"],
        firebase_uid=user2["firebase_uid"],
        auth_token=user2.get("firebase_token")
    )
    
    if not result2.get("success"):
        print(f"   ✅ Correctly rejected: {result2.get('error')}")
        test_results.append(True)
    else:
        print("   ❌ Should have rejected missing user")
        test_results.append(False)
    
    return all(test_results)


def test_gemini_multimodal_context():
    """Test 5: Gemini uses multimodal context (simulated)"""
    print("\n" + "="*60)
    print("TEST 5: Gemini Multimodal Context Handling")
    print("="*60)
    
    print("\n📱 Simulating Gemini receiving user intent:")
    print("   User uploads screenshot of DOTM app")
    print("   User says: 'Activate my eSIM please'")
    print("   Gemini extracts: email from screenshot context")
    
    client = GeminiMCPClient(MESSAGES_ENDPOINT)
    client.establish_connection()
    
    # Simulate Gemini extracting user context from multimodal input
    extracted_context = {
        "email": "aa@dotmobile.app",
        "firebase_uid": "dotm_verified_uid_001",
        "intent": "activate_esim",
        "confidence": 0.95
    }
    
    print(f"\n   → Gemini extracted context (confidence: {extracted_context['confidence']})")
    print(f"   → Calling activate_esim tool...")
    
    result = client.execute_esim_activation(
        email=extracted_context["email"],
        firebase_uid=extracted_context["firebase_uid"]
    )
    
    if result.get("success"):
        print("✅ Gemini successfully processed multimodal context")
        print(f"   Response: {result['message']}")
        return True
    else:
        print(f"❌ Failed: {result.get('message')}")
        return False


def test_gemini_conversation_flow():
    """Test 6: Full Gemini conversation with context awareness"""
    print("\n" + "="*60)
    print("TEST 6: Full Gemini Conversation Flow")
    print("="*60)
    
    client = GeminiMCPClient(MESSAGES_ENDPOINT)
    
    print("\n💬 User: 'Hi Gemini, I just paid for an eSIM. Can you activate it?'")
    
    # Step 1: Connect
    print("\n🔷 Gemini: Connecting to DOTM platform...")
    if not client.establish_connection():
        print("❌ Connection failed")
        return False
    
    # Step 2: Discover capabilities
    print("🔷 Gemini: Checking what I can do...")
    capabilities = client.discover_capabilities()
    
    has_activation = any(
        t["name"] == "activate_esim"
        for t in capabilities["tools"]
    )
    
    if not has_activation:
        print("❌ eSIM activation not available")
        return False
    
    # Step 3: Get user context (simulated)
    print("🔷 Gemini: I can help with that! Let me access your account...")
    user_context = {
        "email": "aa@dotmobile.app",
        "firebase_uid": "dotm_verified_uid_001"
    }
    
    # Step 4: Execute activation
    print(f"🔷 Gemini: Activating eSIM for {user_context['email']}...")
    result = client.execute_esim_activation(**user_context)
    
    if result.get("success"):
        print("\n✅ Full conversation successful!")
        print(f"\n💬 Gemini: '{result['message']}'")
        print(f"💬 Gemini: 'Your new phone number is {result['details']['phone_number']}'")
        print(f"💬 Gemini: 'Next: {result['next_steps'][0]}'")
        
        print("\n📊 Conversation Context:")
        for entry in client.conversation_context:
            print(f"   [{entry['role']}] {entry['message'][:80]}...")
        
        return True
    else:
        print(f"❌ Activation failed: {result.get('message')}")
        return False


def test_gemini_batch_operations():
    """Test 7: Gemini handles multiple operations efficiently"""
    print("\n" + "="*60)
    print("TEST 7: Gemini Batch Operations")
    print("="*60)
    
    client = GeminiMCPClient(MESSAGES_ENDPOINT)
    client.establish_connection()
    
    print("\n🔷 Gemini: Processing batch request...")
    print("   1. List available tools")
    print("   2. Get service details")
    print("   3. Calculate pricing")
    print("   4. Activate eSIM")
    
    operations = []
    
    # Operation 1: List tools
    tools_result = client.json_rpc_call("tools/list")
    operations.append(("List Tools", "result" in tools_result))
    
    # Operation 2: Get service details
    service_result = client.json_rpc_call(
        "tools/call",
        {"name": "get_service_details", "arguments": {"service_id": "beta_esim_activation"}}
    )
    operations.append(("Service Details", "result" in service_result))
    
    # Operation 3: Calculate pricing
    pricing_result = client.json_rpc_call(
        "tools/call",
        {"name": "calculate_pricing", "arguments": {"service_ids": ["beta_esim_activation"]}}
    )
    operations.append(("Calculate Pricing", "result" in pricing_result))
    
    # Operation 4: Activate eSIM
    activation_result = client.execute_esim_activation(
        email="aa@dotmobile.app",
        firebase_uid="dotm_verified_uid_001"
    )
    operations.append(("Activate eSIM", activation_result.get("success", False)))
    
    # Results
    print("\n   Batch Results:")
    all_success = True
    for operation, success in operations:
        status = "✅" if success else "❌"
        print(f"   {status} {operation}")
        all_success = all_success and success
    
    if all_success:
        print("\n✅ All batch operations successful")
        return True
    else:
        print("\n❌ Some batch operations failed")
        return False


def run_all_tests():
    """Run all Gemini integration tests"""
    print("\n" + "🔷" * 30)
    print("Gemini AI + MCP v2 Server Integration Tests")
    print("Testing eSIM Activation with Multimodal Context")
    print("🔷" * 30)
    
    tests = [
        ("Connection Establishment", test_gemini_connection),
        ("Capability Discovery", test_gemini_capability_discovery),
        ("Happy Path Activation", test_gemini_happy_path_activation),
        ("Error Handling", test_gemini_error_handling),
        ("Multimodal Context", test_gemini_multimodal_context),
        ("Conversation Flow", test_gemini_conversation_flow),
        ("Batch Operations", test_gemini_batch_operations)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' raised exception: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY - GEMINI AI")
    print("="*60)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print("="*60 + "\n")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
