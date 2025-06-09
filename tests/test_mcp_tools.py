#!/usr/bin/env python3
"""
Test suite for MCP Tools functionality
Tests all available tools: search_hackernews, get_github_repo_info, get_server_roots, 
get_server_prompts, create_sampling_request, analyze_hackernews_trends_with_ai, 
code_review_with_ai, and request_client_roots.
"""

import requests
import json
import sys
import os
from typing import Dict, Any, Optional

# Removed src directory import to avoid conflicts with running server

class MCPToolsTester:
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
        """Initialize MCP session with enhanced capabilities."""
        init_data = {
            'jsonrpc': '2.0',
            'id': 'init',
            'method': 'initialize',
            'params': {
                'protocolVersion': '2025-03-26',
                'capabilities': {
                    'sampling': {},
                    'roots': {'listChanged': True},
                    'experimental': {}
                },
                'clientInfo': {'name': 'tools-test', 'version': '1.0'}
            }
        }

        try:
            response = requests.post(self.base_url, json=init_data, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                self.session_id = response.headers.get('mcp-session-id')
                self.headers['mcp-session-id'] = self.session_id
                print(f"✅ Session initialized: {self.session_id}")
                
                # Send initialized notification
                notif_data = {'jsonrpc': '2.0', 'method': 'notifications/initialized'}
                requests.post(self.base_url, headers=self.headers, json=notif_data)
                
                return True
            else:
                print(f"❌ Failed to initialize: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Initialization error: {e}")
            return False

    def call_tool(self, tool_name: str, arguments: Dict[str, Any], test_name: str) -> bool:
        """Call a specific tool and validate response."""
        tool_data = {
            'jsonrpc': '2.0',
            'id': f'tool_{tool_name}',
            'method': 'tools/call',
            'params': {
                'name': tool_name,
                'arguments': arguments
            }
        }
        
        print(f"\n🔧 Testing {test_name}...")
        
        try:
            response = requests.post(self.base_url, headers=self.headers, json=tool_data, timeout=15)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                result = self.parse_sse_response(response.text)
                if result and 'result' in result:
                    content = result['result'].get('content', [])
                    if content:
                        print(f"   ✅ {test_name} successful")
                        self._print_tool_result(tool_name, content[0], test_name)
                        return True
                    else:
                        print(f"   ❌ {test_name} - No content in response")
                        return False
                else:
                    print(f"   ❌ {test_name} - Could not parse response")
                    return False
            else:
                print(f"   ❌ {test_name} failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ {test_name} error: {e}")
            return False

    def _print_tool_result(self, tool_name: str, content: Dict[str, Any], test_name: str):
        """Print formatted tool result based on tool type."""
        if 'text' in content:
            try:
                data = json.loads(content['text'])
                
                if tool_name == 'search_hackernews':
                    if isinstance(data, list) and data:
                        print(f"      Found {len(data)} stories")
                        print(f"      Sample: {data[0].get('title', 'Unknown')[:50]}...")
                
                elif tool_name == 'get_github_repo_info':
                    if isinstance(data, dict):
                        print(f"      Repo: {data.get('name', 'Unknown')}")
                        print(f"      Stars: {data.get('stars', 0)}")
                        print(f"      Language: {data.get('language', 'Unknown')}")
                
                elif tool_name == 'get_server_roots':
                    if isinstance(data, list):
                        print(f"      Found {len(data)} roots")
                        for root in data[:3]:  # Show first 3
                            print(f"         • {root.get('uri', 'Unknown')}: {root.get('name', 'Unknown')}")
                
                elif tool_name == 'get_server_prompts':
                    if isinstance(data, list):
                        print(f"      Found {len(data)} prompts")
                        for prompt in data[:3]:  # Show first 3
                            print(f"         • {prompt.get('name', 'Unknown')}: {prompt.get('description', 'Unknown')[:40]}...")
                
                elif tool_name == 'create_sampling_request':
                    sampling_req = data.get('sampling_request', {})
                    print(f"      Method: {sampling_req.get('method', 'Unknown')}")
                    print(f"      Status: {data.get('status', 'Unknown')}")
                    params = sampling_req.get('params', {})
                    if 'modelPreferences' in params:
                        prefs = params['modelPreferences']
                        print(f"      Model prefs: Intelligence={prefs.get('intelligencePriority')}, Cost={prefs.get('costPriority')}")
                
                elif tool_name == 'analyze_hackernews_trends_with_ai':
                    analysis_req = data.get('analysis_request', {})
                    print(f"      Analysis method: {analysis_req.get('method', 'Unknown')}")
                    print(f"      Topic: {data.get('topic', 'Unknown')}")
                    print(f"      Stories analyzed: {data.get('stories_count', 0)}")
                
                elif tool_name == 'code_review_with_ai':
                    review_req = data.get('review_request', {})
                    print(f"      Review method: {review_req.get('method', 'Unknown')}")
                    print(f"      Repository: {data.get('repository', 'Unknown')}")
                    print(f"      Focus: {data.get('review_focus', 'Unknown')}")
                
                elif tool_name == 'request_client_roots':
                    roots_req = data.get('roots_request', {})
                    print(f"      Roots method: {roots_req.get('method', 'Unknown')}")
                    meta = roots_req.get('params', {}).get('_meta', {})
                    print(f"      Protocol version: {meta.get('protocolVersion', 'Unknown')}")
                    
            except json.JSONDecodeError:
                print(f"      Raw text result: {content['text'][:100]}...")

def test_all_tools():
    """Test all available MCP tools."""
    print("🔧 MCP Tools Test Suite")
    print("=" * 50)
    
    tester = MCPToolsTester()
    
    if not tester.initialize_session():
        return False
    
    # Test results tracking
    results = {}
    
    # Test 1: search_hackernews tool
    results['search_hackernews'] = tester.call_tool(
        'search_hackernews',
        {'query': 'AI', 'limit': 3},
        'HackerNews Search'
    )
    
    # Test 2: get_github_repo_info tool
    results['get_github_repo_info'] = tester.call_tool(
        'get_github_repo_info',
        {'owner': 'microsoft', 'repo': 'vscode'},
        'GitHub Repo Info'
    )
    
    # Test 3: get_server_roots tool
    results['get_server_roots'] = tester.call_tool(
        'get_server_roots',
        {},
        'Server Roots'
    )
    
    # Test 4: get_server_prompts tool
    results['get_server_prompts'] = tester.call_tool(
        'get_server_prompts',
        {},
        'Server Prompts'
    )
    
    # Test 5: create_sampling_request tool - Basic
    results['create_sampling_request_basic'] = tester.call_tool(
        'create_sampling_request',
        {
            'prompt': 'Analyze AI trends',
            'max_tokens': 500,
            'temperature': 0.7
        },
        'Basic Sampling Request'
    )
    
    # Test 6: create_sampling_request tool - Enhanced with model preferences
    results['create_sampling_request_enhanced'] = tester.call_tool(
        'create_sampling_request',
        {
            'prompt': 'Analyze technology developments',
            'context_data': {'source': 'hackernews', 'topic': 'AI'},
            'max_tokens': 1000,
            'temperature': 0.6,
            'model_hint': 'claude-3-sonnet',
            'intelligence_priority': 0.9,
            'cost_priority': 0.2,
            'speed_priority': 0.4
        },
        'Enhanced Sampling with Model Preferences'
    )
    
    # Test 7: analyze_hackernews_trends_with_ai tool
    results['analyze_hackernews_trends_with_ai'] = tester.call_tool(
        'analyze_hackernews_trends_with_ai',
        {
            'topic': 'AI',
            'count': 3,
            'analysis_type': 'detailed'
        },
        'HackerNews Trends Analysis'
    )
    
    # Test 8: code_review_with_ai tool
    results['code_review_with_ai'] = tester.call_tool(
        'code_review_with_ai',
        {
            'repo_owner': 'microsoft',
            'repo_name': 'vscode',
            'review_focus': 'security'
        },
        'AI Code Review'
    )
    
    # Test 9: request_client_roots tool
    results['request_client_roots'] = tester.call_tool(
        'request_client_roots',
        {},
        'Client Roots Request'
    )
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 TOOLS TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:35} {status}")
    
    print(f"\nTools Tests: {passed}/{total} passed")
    
    return passed == total

if __name__ == "__main__":
    success = test_all_tools()
    sys.exit(0 if success else 1) 