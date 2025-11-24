
#!/usr/bin/env python3
"""
Quick test script to verify MCP server functionality
"""
import requests
import json

def test_mcp_endpoints():
    base_url = "https://gorse.dotmobile.app"  # Replace with your actual Repl URL
    
    endpoints_to_test = [
        "/mcp",
        "/mcp/api", 
        "/mcp/service/basic_membership",
        "/mcp/calculate?services=basic_membership,global_data_10gb"
    ]
    
    print("Testing MCP Server Endpoints...")
    print("=" * 50)
    
    for endpoint in endpoints_to_test:
        try:
            url = f"{base_url}{endpoint}"
            response = requests.get(url, timeout=10)
            
            print(f"✅ {endpoint}")
            print(f"   Status: {response.status_code}")
            print(f"   Content-Type: {response.headers.get('content-type', 'unknown')}")
            
            if endpoint == "/mcp/api":
                # Parse JSON response for API endpoint
                data = response.json()
                print(f"   Services: {len(data.get('services', {}))}")
                print(f"   Platform: {data.get('platform', 'unknown')}")
            
            print()
            
        except Exception as e:
            print(f"❌ {endpoint}")
            print(f"   Error: {str(e)}")
            print()

if __name__ == "__main__":
    test_mcp_endpoints()
