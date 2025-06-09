#!/usr/bin/env python3
"""
Test suite for MCP Resources functionality
Tests all available resources: hackernews://, github://, sampling://, 
status://, roots://, and analysis:// endpoints.
"""

import requests
import json
import sys
import os
from typing import Dict, Any, Optional, List

# Removed src directory import to avoid conflicts with running server

class MCPResourcesTester:
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
        """Initialize MCP session with resource capabilities."""
        init_data = {
            'jsonrpc': '2.0',
            'id': 'init',
            'method': 'initialize',
            'params': {
                'protocolVersion': '2025-03-26',
                'capabilities': {
                    'sampling': {},
                    'roots': {'listChanged': True},
                    'resources': {}
                },
                'clientInfo': {'name': 'resources-test', 'version': '1.0'}
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

    def list_resources(self) -> Optional[List[Dict[str, Any]]]:
        """List all available resources."""
        resource_data = {
            'jsonrpc': '2.0',
            'id': 'list_resources',
            'method': 'resources/list'
        }
        
        try:
            response = requests.post(self.base_url, headers=self.headers, json=resource_data, timeout=10)
            
            if response.status_code == 200:
                result = self.parse_sse_response(response.text)
                if result and 'result' in result:
                    return result['result'].get('resources', [])
            
            return None
            
        except Exception as e:
            print(f"❌ Error listing resources: {e}")
            return None

    def read_resource(self, uri: str, test_name: str) -> bool:
        """Read a specific resource and validate response."""
        resource_data = {
            'jsonrpc': '2.0',
            'id': f'resource_{uri.replace("://", "_").replace("/", "_")}',
            'method': 'resources/read',
            'params': {
                'uri': uri
            }
        }
        
        print(f"\n📁 Testing {test_name} ({uri})...")
        
        try:
            response = requests.post(self.base_url, headers=self.headers, json=resource_data, timeout=15)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                result = self.parse_sse_response(response.text)
                if result and 'result' in result:
                    contents = result['result'].get('contents', [])
                    if contents:
                        print(f"   ✅ {test_name} successful - {len(contents)} content items")
                        self._print_resource_result(uri, contents[0], test_name)
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

    def _print_resource_result(self, uri: str, content: Dict[str, Any], test_name: str):
        """Print formatted resource result based on resource type."""
        if 'text' in content:
            try:
                data = json.loads(content['text'])
                
                if uri.startswith('hackernews://'):
                    if isinstance(data, list) and data:
                        print(f"      Found {len(data)} HackerNews stories")
                        first_story = data[0]
                        print(f"      Sample: {first_story.get('title', 'Unknown')[:50]}...")
                        print(f"      Score: {first_story.get('score', 0)}")
                
                elif uri.startswith('github://'):
                    if isinstance(data, list) and data:
                        print(f"      Found {len(data)} GitHub repositories")
                        first_repo = data[0]
                        print(f"      Sample: {first_repo.get('name', 'Unknown')} ({first_repo.get('stars', 0)} ⭐)")
                        print(f"      Language: {first_repo.get('language', 'Unknown')}")
                
                elif uri.startswith('sampling://'):
                    if isinstance(data, list) and data:
                        print(f"      Generated {len(data)} samples")
                        first_sample = data[0]
                        if 'value' in first_sample:
                            print(f"      Sample value: {first_sample.get('value', 0):.2f}")
                        if 'category' in first_sample:
                            print(f"      Sample category: {first_sample.get('category', 'Unknown')}")
                    elif isinstance(data, dict):
                        print(f"      Sampling type: {data.get('type', 'Unknown')}")
                        print(f"      Sample count: {data.get('count', 0)}")
                
                elif uri.startswith('status://'):
                    if isinstance(data, dict):
                        print(f"      Status: {data.get('status', 'Unknown')}")
                        print(f"      Uptime: {data.get('uptime', 'Unknown')}")
                        if 'available_resources' in data:
                            print(f"      Available resources: {len(data['available_resources'])}")
                
                elif uri.startswith('roots://'):
                    if isinstance(data, dict):
                        roots = data.get('roots', [])
                        print(f"      Available roots: {len(roots)}")
                        for root in roots[:3]:
                            print(f"         • {root}")
                
                elif uri.startswith('analysis://'):
                    if isinstance(data, dict):
                        print(f"      Analysis type: {data.get('analysis_type', 'Unknown')}")
                        print(f"      Data source: {data.get('data_source', 'Unknown')}")
                        if 'results' in data:
                            print(f"      Results count: {len(data.get('results', []))}")
                        
            except json.JSONDecodeError:
                print(f"      Raw text result: {content['text'][:100]}...")
            except Exception as e:
                print(f"      Error parsing result: {e}")

def test_all_resources():
    """Test all available MCP resources."""
    print("📁 MCP Resources Test Suite")
    print("=" * 50)
    
    tester = MCPResourcesTester()
    
    if not tester.initialize_session():
        return False
    
    # List available resources first
    print("\n📋 Listing available resources...")
    resources = tester.list_resources()
    if resources:
        print(f"✅ Found {len(resources)} available resources:")
        for resource in resources:
            print(f"   • {resource.get('uri', 'Unknown')}: {resource.get('name', 'Unknown')}")
    else:
        print("❌ Could not list resources")
    
    # Test results tracking
    results = {}
    
    # Test predefined resource URIs
    test_resources = [
        # HackerNews resources
        ("hackernews://top/5", "HackerNews Top 5"),
        ("hackernews://top/10", "HackerNews Top 10"),
        
        # GitHub resources
        ("github://trending/python/daily", "GitHub Python Daily Trending"),
        ("github://trending/javascript/weekly", "GitHub JavaScript Weekly Trending"),
        
        # Sampling resources
        ("sampling://random/5", "Random Sampling (5 samples)"),
        ("sampling://sequential/3", "Sequential Sampling (3 samples)"),
        ("sampling://distribution/10", "Distribution Sampling (10 samples)"),
        ("sampling://repositories/python/3", "Repository Sampling (Python)"),
        ("sampling://hackernews/5", "HackerNews Sampling (5 stories)"),
        
        # Status resources
        ("status://server", "Server Status"),
        ("status://resources", "Resources Status"),
        
        # Roots resources
        ("roots://", "Available Roots"),
        
        # Analysis resources (if available)
        ("analysis://hackernews/AI/5", "HackerNews AI Analysis"),
        ("analysis://github/microsoft/vscode", "GitHub Repository Analysis"),
        ("sampling://ai-analysis/hackernews/topic=AI&count=3", "AI Analysis Sampling")
    ]
    
    # Test each resource
    for uri, test_name in test_resources:
        results[uri] = tester.read_resource(uri, test_name)
    
    # Test dynamic resource URIs based on available resources
    if resources:
        dynamic_tests = []
        for resource in resources[:5]:  # Test first 5 listed resources
            uri = resource.get('uri', '')
            if uri and uri not in [test[0] for test in test_resources]:
                name = resource.get('name', f'Dynamic {uri}')
                dynamic_tests.append((uri, f"Dynamic: {name}"))
        
        for uri, test_name in dynamic_tests:
            results[uri] = tester.read_resource(uri, test_name)
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 RESOURCES TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    # Group results by resource type
    resource_types = {
        'hackernews': [k for k in results.keys() if k.startswith('hackernews://')],
        'github': [k for k in results.keys() if k.startswith('github://')],
        'sampling': [k for k in results.keys() if k.startswith('sampling://')],
        'status': [k for k in results.keys() if k.startswith('status://')],
        'roots': [k for k in results.keys() if k.startswith('roots://')],
        'analysis': [k for k in results.keys() if k.startswith('analysis://')]
    }
    
    for resource_type, uris in resource_types.items():
        if uris:
            print(f"\n{resource_type.upper()} Resources:")
            for uri in uris:
                status = "✅ PASSED" if results[uri] else "❌ FAILED"
                print(f"  {uri:40} {status}")
    
    print(f"\nOverall Resources Tests: {passed}/{total} passed")
    
    # Print resource type summary
    type_summary = {}
    for resource_type, uris in resource_types.items():
        if uris:
            type_passed = sum(1 for uri in uris if results[uri])
            type_total = len(uris)
            type_summary[resource_type] = f"{type_passed}/{type_total}"
    
    if type_summary:
        print("\nBy Resource Type:")
        for resource_type, summary in type_summary.items():
            print(f"  {resource_type.capitalize():12} {summary}")
    
    return passed == total

if __name__ == "__main__":
    success = test_all_resources()
    sys.exit(0 if success else 1) 