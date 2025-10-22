#!/usr/bin/env python3
"""
Test Suite: ChatGPT Integration with MCP v2 Server - eSIM Activation
Simulates how ChatGPT would interact with the DOTM MCP v2 server to activate eSIMs
for authenticated users.
"""

import requests
import json
from typing import Dict, Any, Optional
import os

# Configuration
BASE_URL = os.getenv("MCP_BASE_URL", "http://localhost:5000/mcp/v2")
MESSAGES_ENDPOINT = f"{BASE_URL}/messages"

# Test user data (replace with actual test Firebase UIDs)
TEST_USERS = {
    "verified_user": {
        "email": "verified@dotm.test",
        "firebase_uid": "test_verified_uid_123",
        "firebase_token": "test_token_verified",  # Replace with actual test token
        "expected_result": "success"
    },
    "unverified_user": {
        "email": "unverified@dotm.test",
        "firebase_uid": "test_unverified_uid_456",
        "firebase_token": "test_token_unverified",
        "expected_result": "failure"
    },
    "invalid_user": {
        "email": "invalid@dotm.test",
        "firebase_uid": "invalid_uid_789",
        "firebase_token": "invalid_token",
        "expected_result": "error"
    }
}


class ChatGPTMCPClient:
    """Simulates ChatGPT's interaction with MCP v2 server"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session_id = None
        self.request_id = 1
    
    def create_json_rpc_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a JSON-RPC 2.0 request"""
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method
        }
        if params:
            request["params"] = params
        
        self.request_id += 1
        return request
    
    def send_request(self, request: Dict[str, Any], auth_token: Optional[str] = None) -> Dict[str, Any]:
        """Send JSON-RPC request to MCP server"""
        headers = {
            "Content-Type": "application/json"
        }
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        
        try:
            response = requests.post(
                self.base_url,
                json=request,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32603,
                    "message": f"Request failed: {str(e)}"
                }
            }
    
    def initialize_connection(self) -> Dict[str, Any]:
        """Initialize MCP connection (as ChatGPT would)"""
        print("\n🤖 ChatGPT: Initializing MCP connection...")
        request = self.create_json_rpc_request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "ChatGPT",
                    "version": "gpt-4"
                }
            }
        )
        return self.send_request(request)
    
    def list_tools(self, auth_token: Optional[str] = None) -> Dict[str, Any]:
        """List available tools"""
        print("\n🤖 ChatGPT: Requesting available tools...")
        request = self.create_json_rpc_request("tools/list")
        return self.send_request(request, auth_token)
    
    def activate_esim(self, email: str, firebase_uid: str, auth_token: Optional[str] = None) -> Dict[str, Any]:
        """Activate eSIM for user"""
        print(f"\n🤖 ChatGPT: Activating eSIM for {email}...")
        request = self.create_json_rpc_request(
            "tools/call",
            {
                "name": "activate_esim",
                "arguments": {
                    "email": email,
                    "firebase_uid": firebase_uid
                }
            }
        )
        return self.send_request(request, auth_token)


def test_chatgpt_initialization():
    """Test 1: ChatGPT initializes connection to MCP server"""
    print("\n" + "="*60)
    print("TEST 1: ChatGPT Initialization")
    print("="*60)
    
    client = ChatGPTMCPClient(MESSAGES_ENDPOINT)
    result = client.initialize_connection()
    
    if "result" in result:
        print("✅ Initialization successful")
        print(f"   Server: {result['result'].get('serverInfo', {}).get('name')}")
        print(f"   Protocol: {result['result'].get('protocolVersion')}")
        return True
    else:
        print(f"❌ Initialization failed: {result.get('error', {}).get('message')}")
        return False


def test_chatgpt_list_tools():
    """Test 2: ChatGPT discovers activate_esim tool"""
    print("\n" + "="*60)
    print("TEST 2: ChatGPT Discovers Tools")
    print("="*60)
    
    client = ChatGPTMCPClient(MESSAGES_ENDPOINT)
    client.initialize_connection()
    result = client.list_tools()
    
    if "result" in result:
        tools = result["result"].get("tools", [])
        activate_esim_tool = next((t for t in tools if t["name"] == "activate_esim"), None)
        
        if activate_esim_tool:
            print("✅ Found activate_esim tool")
            print(f"   Description: {activate_esim_tool['description']}")
            print(f"   Required params: {activate_esim_tool['inputSchema'].get('required', [])}")
            return True
        else:
            print("❌ activate_esim tool not found in tool list")
            print(f"   Available tools: {[t['name'] for t in tools]}")
            return False
    else:
        print(f"❌ Failed to list tools: {result.get('error', {}).get('message')}")
        return False


def test_chatgpt_activate_verified_user():
    """Test 3: ChatGPT activates eSIM for verified user"""
    print("\n" + "="*60)
    print("TEST 3: Activate eSIM for Verified User")
    print("="*60)
    
    user = TEST_USERS["verified_user"]
    client = ChatGPTMCPClient(MESSAGES_ENDPOINT)
    client.initialize_connection()
    
    result = client.activate_esim(
        email=user["email"],
        firebase_uid=user["firebase_uid"],
        auth_token=user.get("firebase_token")
    )
    
    if "result" in result:
        content = result["result"].get("content", [])
        if content:
            response_data = json.loads(content[0].get("text", "{}"))
            
            if response_data.get("success"):
                print("✅ eSIM activation successful")
                print(f"   Email: {response_data['details']['email']}")
                print(f"   Phone: {response_data['details']['phone_number']}")
                print(f"   Plan: {response_data['details']['plan']}")
                print(f"   Next Steps: {len(response_data['next_steps'])} actions")
                return True
            else:
                print(f"❌ Activation failed: {response_data.get('message')}")
                return False
    else:
        print(f"❌ Tool call failed: {result.get('error', {}).get('message')}")
        return False


def test_chatgpt_activate_unverified_user():
    """Test 4: ChatGPT attempts to activate eSIM for unverified user (should fail)"""
    print("\n" + "="*60)
    print("TEST 4: Activate eSIM for Unverified User (Expected Failure)")
    print("="*60)
    
    user = TEST_USERS["unverified_user"]
    client = ChatGPTMCPClient(MESSAGES_ENDPOINT)
    client.initialize_connection()
    
    result = client.activate_esim(
        email=user["email"],
        firebase_uid=user["firebase_uid"],
        auth_token=user.get("firebase_token")
    )
    
    if "result" in result:
        content = result["result"].get("content", [])
        if content:
            response_data = json.loads(content[0].get("text", "{}"))
            
            if not response_data.get("success"):
                print("✅ Correctly rejected unverified user")
                print(f"   Error: {response_data.get('error')}")
                print(f"   Message: {response_data.get('message')}")
                return True
            else:
                print("❌ Should not have activated unverified user")
                return False
    else:
        print(f"✅ Request correctly failed at JSON-RPC level")
        print(f"   Error: {result.get('error', {}).get('message')}")
        return True


def test_chatgpt_missing_parameters():
    """Test 5: ChatGPT sends request with missing parameters"""
    print("\n" + "="*60)
    print("TEST 5: Missing Parameters (Expected Error)")
    print("="*60)
    
    client = ChatGPTMCPClient(MESSAGES_ENDPOINT)
    client.initialize_connection()
    
    # Missing firebase_uid
    request = client.create_json_rpc_request(
        "tools/call",
        {
            "name": "activate_esim",
            "arguments": {
                "email": "test@dotm.test"
                # firebase_uid missing
            }
        }
    )
    
    result = client.send_request(request)
    
    if "result" in result:
        content = result["result"].get("content", [])
        if content:
            response_data = json.loads(content[0].get("text", "{}"))
            
            if not response_data.get("success"):
                print("✅ Correctly rejected missing parameters")
                print(f"   Error: {response_data.get('error')}")
                return True
            else:
                print("❌ Should have rejected missing parameters")
                return False
    else:
        print("✅ Request correctly failed at JSON-RPC level")
        return True


def test_chatgpt_full_conversation():
    """Test 6: Full ChatGPT conversation flow"""
    print("\n" + "="*60)
    print("TEST 6: Full ChatGPT Conversation Flow")
    print("="*60)
    
    print("\n📝 Simulating user conversation with ChatGPT:")
    print("   User: 'I want to activate my eSIM'")
    print("   ChatGPT: 'I'll help you activate your eSIM...'")
    
    user = TEST_USERS["verified_user"]
    client = ChatGPTMCPClient(MESSAGES_ENDPOINT)
    
    # Step 1: Initialize
    print("\n   → ChatGPT initializes MCP connection")
    init_result = client.initialize_connection()
    if "error" in init_result:
        print(f"   ❌ Failed to initialize: {init_result['error']}")
        return False
    
    # Step 2: List tools to find activate_esim
    print("   → ChatGPT discovers activate_esim tool")
    tools_result = client.list_tools()
    if "error" in tools_result:
        print(f"   ❌ Failed to list tools: {tools_result['error']}")
        return False
    
    # Step 3: Call activate_esim with user context
    print(f"   → ChatGPT calls activate_esim for {user['email']}")
    activation_result = client.activate_esim(
        email=user["email"],
        firebase_uid=user["firebase_uid"],
        auth_token=user.get("firebase_token")
    )
    
    if "result" in activation_result:
        content = activation_result["result"].get("content", [])
        if content:
            response_data = json.loads(content[0].get("text", "{}"))
            
            if response_data.get("success"):
                print("\n   ✅ Full conversation successful!")
                print(f"   ChatGPT response to user:")
                print(f"   '{response_data['message']}'")
                print(f"   'Your phone number: {response_data['details']['phone_number']}'")
                print(f"   'Next steps: {response_data['next_steps'][0]}'")
                return True
            else:
                print(f"   ❌ Activation failed: {response_data.get('message')}")
                return False
    else:
        print(f"   ❌ Tool call failed: {activation_result.get('error')}")
        return False


def run_all_tests():
    """Run all ChatGPT integration tests"""
    print("\n" + "🤖" * 30)
    print("ChatGPT + MCP v2 Server Integration Tests")
    print("Testing eSIM Activation via JSON-RPC 2.0")
    print("🤖" * 30)
    
    tests = [
        ("Initialization", test_chatgpt_initialization),
        ("Tool Discovery", test_chatgpt_list_tools),
        ("Verified User Activation", test_chatgpt_activate_verified_user),
        ("Unverified User Rejection", test_chatgpt_activate_unverified_user),
        ("Parameter Validation", test_chatgpt_missing_parameters),
        ("Full Conversation", test_chatgpt_full_conversation)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' raised exception: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
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
