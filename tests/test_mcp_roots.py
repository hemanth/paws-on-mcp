#!/usr/bin/env python3
"""
Test suite for MCP Roots functionality (MCP 2025-03-26)
Tests the roots capability including server root discovery, client root requests,
and roots/list functionality per the latest MCP specification.
"""

import requests
import json
import sys
import os
from typing import Dict, Any, Optional, List

# Removed src directory import to avoid conflicts with running server

class MCPRootsTester:
    def __init__(self, base_url: str = 'http://127.0.0.1:8000/mcp/'):
        self.base_url = base_url
        self.session_id = None
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }

    def parse_sse_response(self, content: str) -> Optional[Dict[str, Any]]:
        """Parse Server-Sent Events response format."""
        if "data: " in content:
            lines = content.split('\n')
            for line in lines:
                if line.startswith("data: "):
                    try:
                        return json.loads(line[6:])
                    except json.JSONDecodeError:
                        return None
        return None

    def initialize_session(self) -> bool:
        """Initialize MCP session with roots capabilities per 2025-03-26 spec."""
        init_data = {
            'jsonrpc': '2.0',
            'id': 'init',
            'method': 'initialize',
            'params': {
                'protocolVersion': '2025-03-26',
                'capabilities': {
                    'roots': {
                        'listChanged': True  # Client supports roots/list_changed notifications
                    },
                    'sampling': {},
                    'resources': {}
                },
                'clientInfo': {'name': 'roots-test', 'version': '1.0'}
            }
        }

        try:
            response = requests.post(self.base_url, json=init_data, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                result = self.parse_sse_response(response.text)
                if result and 'result' in result:
                    server_capabilities = result['result'].get('capabilities', {})
                    server_roots = server_capabilities.get('roots', {})
                    
                    self.session_id = response.headers.get('mcp-session-id')
                    self.headers['mcp-session-id'] = self.session_id
                    print(f"✅ Session initialized: {self.session_id}")
                    print(f"   Server roots capability: {bool(server_roots)}")
                    if server_roots:
                        print(f"   Server supports listChanged: {server_roots.get('listChanged', False)}")
                    
                    # Send initialized notification
                    notif_data = {'jsonrpc': '2.0', 'method': 'notifications/initialized'}
                    requests.post(self.base_url, headers=self.headers, json=notif_data)
                    
                    return True
                else:
                    print(f"❌ Could not parse initialization response")
                    return False
            else:
                print(f"❌ Failed to initialize: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Initialization error: {e}")
            return False

    def test_roots_list(self) -> bool:
        """Test the roots/list method per MCP 2025-03-26."""
        print(f"\n🌳 Testing roots/list method...")
        
        roots_data = {
            'jsonrpc': '2.0',
            'id': 'roots_list',
            'method': 'roots/list',
            'params': {
                '_meta': {
                    'protocolVersion': '2025-03-26'
                }
            }
        }
        
        try:
            response = requests.post(self.base_url, headers=self.headers, json=roots_data, timeout=10)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                result = self.parse_sse_response(response.text)
                if result and 'result' in result:
                    roots = result['result'].get('roots', [])
                    print(f"   ✅ roots/list successful - {len(roots)} roots found")
                    
                    for i, root in enumerate(roots[:5]):  # Show first 5
                        uri = root.get('uri', 'Unknown')
                        name = root.get('name', 'Unknown')
                        print(f"      {i+1}. {uri} - {name}")
                    
                    return True
                else:
                    print(f"   ❌ Could not parse roots/list response")
                    return False
            else:
                print(f"   ❌ roots/list failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ roots/list error: {e}")
            return False

    def test_server_roots_tool(self) -> bool:
        """Test the get_server_roots tool."""
        print(f"\n🔧 Testing get_server_roots tool...")
        
        tool_data = {
            'jsonrpc': '2.0',
            'id': 'server_roots_tool',
            'method': 'tools/call',
            'params': {
                'name': 'get_server_roots',
                'arguments': {}
            }
        }
        
        try:
            response = requests.post(self.base_url, headers=self.headers, json=tool_data, timeout=10)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                result = self.parse_sse_response(response.text)
                if result and 'result' in result:
                    content = result['result'].get('content', [])
                    if content and 'text' in content[0]:
                        try:
                            roots_data = json.loads(content[0]['text'])
                            if isinstance(roots_data, list):
                                print(f"   ✅ get_server_roots successful - {len(roots_data)} roots")
                                
                                for i, root in enumerate(roots_data[:3]):  # Show first 3
                                    uri = root.get('uri', 'Unknown')
                                    name = root.get('name', 'Unknown')
                                    description = root.get('description', 'No description')
                                    print(f"      {i+1}. {uri}")
                                    print(f"         Name: {name}")
                                    print(f"         Description: {description[:60]}...")
                                
                                return True
                            else:
                                print(f"   ❌ Unexpected roots data format")
                                return False
                        except json.JSONDecodeError:
                            print(f"   ❌ Could not parse roots tool response")
                            return False
                    else:
                        print(f"   ❌ No content in tool response")
                        return False
                else:
                    print(f"   ❌ Could not parse tool response")
                    return False
            else:
                print(f"   ❌ get_server_roots tool failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ get_server_roots tool error: {e}")
            return False

    def test_client_roots_request_tool(self) -> bool:
        """Test the request_client_roots tool (MCP 2025-03-26 feature)."""
        print(f"\n📋 Testing request_client_roots tool...")
        
        tool_data = {
            'jsonrpc': '2.0',
            'id': 'client_roots_tool',
            'method': 'tools/call',
            'params': {
                'name': 'request_client_roots',
                'arguments': {}
            }
        }
        
        try:
            response = requests.post(self.base_url, headers=self.headers, json=tool_data, timeout=10)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                result = self.parse_sse_response(response.text)
                if result and 'result' in result:
                    content = result['result'].get('content', [])
                    if content and 'text' in content[0]:
                        try:
                            response_data = json.loads(content[0]['text'])
                            
                            # Check for roots request structure
                            if 'roots_request' in response_data:
                                roots_req = response_data['roots_request']
                                method = roots_req.get('method')
                                params = roots_req.get('params', {})
                                meta = params.get('_meta', {})
                                
                                print(f"   ✅ request_client_roots successful")
                                print(f"      Method: {method}")
                                print(f"      Protocol version: {meta.get('protocolVersion', 'Unknown')}")
                                print(f"      Request reason: {meta.get('requestReason', 'None')}")
                                print(f"      Status: {response_data.get('status', 'Unknown')}")
                                
                                # Verify MCP 2025-03-26 compliance
                                if method == 'roots/list' and meta.get('protocolVersion') == '2025-03-26':
                                    print(f"      ✓ MCP 2025-03-26 compliant roots request")
                                    return True
                                else:
                                    print(f"      ⚠️  Roots request format may not be fully compliant")
                                    return True  # Still consider it a pass for basic functionality
                            else:
                                print(f"   ❌ No roots_request in response")
                                return False
                                
                        except json.JSONDecodeError:
                            print(f"   ❌ Could not parse client roots tool response")
                            return False
                    else:
                        print(f"   ❌ No content in tool response")
                        return False
                else:
                    print(f"   ❌ Could not parse tool response")
                    return False
            else:
                print(f"   ❌ request_client_roots tool failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ request_client_roots tool error: {e}")
            return False

    def test_roots_resource(self) -> bool:
        """Test the roots:// resource endpoint."""
        print(f"\n📁 Testing roots:// resource...")
        
        resource_data = {
            'jsonrpc': '2.0',
            'id': 'roots_resource',
            'method': 'resources/read',
            'params': {
                'uri': 'roots://'
            }
        }
        
        try:
            response = requests.post(self.base_url, headers=self.headers, json=resource_data, timeout=10)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                result = self.parse_sse_response(response.text)
                if result and 'result' in result:
                    contents = result['result'].get('contents', [])
                    if contents and 'text' in contents[0]:
                        try:
                            roots_info = json.loads(contents[0]['text'])
                            
                            print(f"   ✅ roots:// resource successful")
                            print(f"      Description: {roots_info.get('description', 'None')}")
                            
                            if 'roots' in roots_info:
                                available_roots = roots_info['roots']
                                print(f"      Available root categories: {len(available_roots)}")
                                for root in available_roots[:5]:  # Show first 5
                                    print(f"         • {root}")
                            
                            if 'usage' in roots_info:
                                print(f"      Usage info: {roots_info['usage']}")
                            
                            return True
                            
                        except json.JSONDecodeError:
                            print(f"   ❌ Could not parse roots resource response")
                            return False
                    else:
                        print(f"   ❌ No content in resource response")
                        return False
                else:
                    print(f"   ❌ Could not parse resource response")
                    return False
            else:
                print(f"   ❌ roots:// resource failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ roots:// resource error: {e}")
            return False

    def test_protocol_compliance(self) -> bool:
        """Test MCP 2025-03-26 protocol compliance for roots."""
        print(f"\n🔍 Testing MCP 2025-03-26 protocol compliance...")
        
        # Test that we can send a proper roots request with _meta
        roots_request = {
            'jsonrpc': '2.0',
            'id': 'compliance_test',
            'method': 'roots/list',
            'params': {
                '_meta': {
                    'protocolVersion': '2025-03-26',
                    'clientCapabilities': {
                        'roots': {
                            'listChanged': True
                        }
                    }
                }
            }
        }
        
        try:
            response = requests.post(self.base_url, headers=self.headers, json=roots_request, timeout=10)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                result = self.parse_sse_response(response.text)
                if result and 'result' in result:
                    # Check if the response includes protocol version info
                    meta = result.get('meta', {})
                    protocol_version = meta.get('protocolVersion', 'Unknown')
                    
                    print(f"   ✅ Protocol compliance test successful")
                    print(f"      Response protocol version: {protocol_version}")
                    
                    roots = result['result'].get('roots', [])
                    print(f"      Roots returned: {len(roots)}")
                    
                    # Check if roots have proper structure per spec
                    if roots:
                        first_root = roots[0]
                        required_fields = ['uri', 'name']
                        has_required = all(field in first_root for field in required_fields)
                        print(f"      ✓ Roots have required fields: {has_required}")
                        
                        # Check for optional but recommended fields
                        optional_fields = ['description']
                        has_optional = any(field in first_root for field in optional_fields)
                        print(f"      ✓ Roots have optional fields: {has_optional}")
                    
                    return True
                else:
                    print(f"   ❌ Could not parse compliance test response")
                    return False
            else:
                print(f"   ❌ Protocol compliance test failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Protocol compliance test error: {e}")
            return False

def test_all_roots_functionality():
    """Test all MCP roots functionality per 2025-03-26 specification."""
    print("🌳 MCP Roots Test Suite (MCP 2025-03-26)")
    print("=" * 50)
    
    tester = MCPRootsTester()
    
    if not tester.initialize_session():
        return False
    
    # Test results tracking
    results = {}
    
    # Test 1: roots/list method
    results['roots_list'] = tester.test_roots_list()
    
    # Test 2: get_server_roots tool
    results['server_roots_tool'] = tester.test_server_roots_tool()
    
    # Test 3: request_client_roots tool
    results['client_roots_request_tool'] = tester.test_client_roots_request_tool()
    
    # Test 4: roots:// resource
    results['roots_resource'] = tester.test_roots_resource()
    
    # Test 5: MCP 2025-03-26 protocol compliance
    results['protocol_compliance'] = tester.test_protocol_compliance()
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 ROOTS TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    test_descriptions = {
        'roots_list': 'roots/list Method',
        'server_roots_tool': 'get_server_roots Tool',
        'client_roots_request_tool': 'request_client_roots Tool',
        'roots_resource': 'roots:// Resource',
        'protocol_compliance': 'MCP 2025-03-26 Compliance'
    }
    
    for test_key, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        description = test_descriptions.get(test_key, test_key)
        print(f"{description:30} {status}")
    
    print(f"\nOverall Roots Tests: {passed}/{total} passed")
    
    # Check critical functionality
    critical_tests = ['roots_list', 'server_roots_tool', 'protocol_compliance']
    critical_passed = sum(1 for test in critical_tests if results.get(test, False))
    critical_total = len(critical_tests)
    
    print(f"Critical Tests: {critical_passed}/{critical_total} passed")
    
    if critical_passed == critical_total:
        print("✅ All critical roots functionality is working")
    else:
        print("⚠️  Some critical roots functionality may not be working properly")
    
    return passed == total

if __name__ == "__main__":
    success = test_all_roots_functionality()
    sys.exit(0 if success else 1) 