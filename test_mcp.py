
#!/usr/bin/env python3
"""
Quick test script to verify MCP server functionality (JSON-RPC 2.0)
"""
import requests
import json

BASE_URL = "https://gorse.dotmobile.app"

def test_mcp_info():
    """Test GET /mcp - Server information"""
    try:
        response = requests.get(f"{BASE_URL}/mcp", timeout=10)
        data = response.json()
        
        print("✅ GET /mcp - Server Information")
        print(f"   Status: {response.status_code}")
        print(f"   Server: {data.get('server')}")
        print(f"   Version: {data.get('version')}")
        print(f"   Protocol: {data.get('protocol_version')}")
        print()
        return True
    except Exception as e:
        print(f"❌ GET /mcp")
        print(f"   Error: {str(e)}")
        print()
        return False

def test_json_rpc(method, params=None, test_name=None):
    """Test JSON-RPC endpoint"""
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or {}
        }
        
        response = requests.post(
            f"{BASE_URL}/mcp/messages",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        data = response.json()
        
        test_label = test_name or method
        print(f"✅ JSON-RPC: {test_label}")
        print(f"   Status: {response.status_code}")
        print(f"   Method: {method}")
        
        if "result" in data:
            result = data["result"]
            if method == "resources/list":
                print(f"   Resources: {len(result.get('resources', []))}")
            elif method == "tools/list":
                tools = result.get('tools', [])
                print(f"   Tools: {[t['name'] for t in tools]}")
            elif method == "resources/read":
                print(f"   URI: {params.get('uri')}")
            elif method == "tools/call":
                print(f"   Tool: {params.get('name')}")
        elif "error" in data:
            print(f"   Error: {data['error']}")
        
        print()
        return True
    except Exception as e:
        print(f"❌ JSON-RPC: {method}")
        print(f"   Error: {str(e)}")
        print()
        return False

def test_mcp_docs():
    """Test GET /mcp/docs - API documentation"""
    try:
        response = requests.get(f"{BASE_URL}/mcp/docs", timeout=10)
        data = response.json()
        
        print("✅ GET /mcp/docs - API Documentation")
        print(f"   Status: {response.status_code}")
        print(f"   Title: {data.get('title')}")
        print(f"   Base URL: {data.get('base_url')}")
        print()
        return True
    except Exception as e:
        print(f"❌ GET /mcp/docs")
        print(f"   Error: {str(e)}")
        print()
        return False

def test_all():
    print("=" * 60)
    print("Testing DOTM MCP Server (JSON-RPC 2.0)")
    print("=" * 60)
    print()
    
    # Test server info
    test_mcp_info()
    
    # Test API docs
    test_mcp_docs()
    
    # Test JSON-RPC methods
    test_json_rpc("initialize", {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "test-client", "version": "1.0"}
    }, "Initialize Connection")
    
    test_json_rpc("resources/list", {}, "List Resources")
    
    test_json_rpc("resources/read", {
        "uri": "dotm://services/catalog"
    }, "Read Service Catalog")
    
    test_json_rpc("tools/list", {}, "List Available Tools")
    
    test_json_rpc("tools/call", {
        "name": "calculate_pricing",
        "arguments": {
            "service_ids": ["basic_membership", "network_vpn_access"]
        }
    }, "Calculate Pricing Tool")
    
    test_json_rpc("prompts/list", {}, "List Prompts")
    
    print("=" * 60)
    print("Test suite completed!")
    print("=" * 60)

if __name__ == "__main__":
    test_all()
