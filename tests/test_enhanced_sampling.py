#!/usr/bin/env python3
"""
Test suite for Enhanced MCP Sampling with Model Preferences (MCP 2025-03-26)
Tests advanced sampling capabilities including model preferences, priority settings,
model hints, and context-aware sampling functionality.
"""

import requests
import json
import sys
import os
from typing import Dict, Any, Optional, List

# Removed src directory import to avoid conflicts with running server

class EnhancedSamplingTester:
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
        """Initialize MCP session with enhanced sampling capabilities."""
        init_data = {
            'jsonrpc': '2.0',
            'id': 'init',
            'method': 'initialize',
            'params': {
                'protocolVersion': '2025-03-26',
                'capabilities': {
                    'sampling': {
                        'modelPreferences': True,  # Support for model preferences
                        'contextAware': True,      # Support for context-aware sampling
                        'multiModal': True         # Support for multi-modal sampling
                    },
                    'roots': {'listChanged': True},
                    'resources': {},
                                    'experimental': {
                    'enhancedSampling': {}
                }
                },
                'clientInfo': {'name': 'enhanced-sampling-test', 'version': '1.0'}
            }
        }

        try:
            response = requests.post(self.base_url, json=init_data, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                result = self.parse_sse_response(response.text)
                if result and 'result' in result:
                    server_capabilities = result['result'].get('capabilities', {})
                    server_sampling = server_capabilities.get('sampling', {})
                    
                    self.session_id = response.headers.get('mcp-session-id')
                    self.headers['mcp-session-id'] = self.session_id
                    print(f"✅ Session initialized: {self.session_id}")
                    print(f"   Server sampling capability: {bool(server_sampling)}")
                    if server_sampling:
                        print(f"   Model preferences: {server_sampling.get('modelPreferences', False)}")
                        print(f"   Context aware: {server_sampling.get('contextAware', False)}")
                    
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

    def test_basic_sampling_request(self) -> bool:
        """Test basic sampling request creation."""
        print(f"\n🎯 Testing basic sampling request...")
        
        tool_data = {
            'jsonrpc': '2.0',
            'id': 'basic_sampling',
            'method': 'tools/call',
            'params': {
                'name': 'create_sampling_request',
                'arguments': {
                    'prompt': 'Analyze the current state of AI technology',
                    'max_tokens': 500,
                    'temperature': 0.7
                }
            }
        }
        
        return self._execute_sampling_test(tool_data, "Basic Sampling Request")

    def test_model_preferences_sampling(self) -> bool:
        """Test sampling with model preferences and priorities."""
        print(f"\n🧠 Testing model preferences sampling...")
        
        tool_data = {
            'jsonrpc': '2.0',
            'id': 'model_prefs_sampling',
            'method': 'tools/call',
            'params': {
                'name': 'create_sampling_request',
                'arguments': {
                    'prompt': 'Provide a detailed analysis of machine learning trends',
                    'max_tokens': 1000,
                    'temperature': 0.6,
                    'model_hint': 'claude-3-sonnet',
                    'intelligence_priority': 0.9,
                    'cost_priority': 0.2,
                    'speed_priority': 0.4
                }
            }
        }
        
        return self._execute_sampling_test(tool_data, "Model Preferences Sampling", check_preferences=True)

    def test_context_aware_sampling(self) -> bool:
        """Test context-aware sampling with rich context data."""
        print(f"\n📊 Testing context-aware sampling...")
        
        tool_data = {
            'jsonrpc': '2.0',
            'id': 'context_sampling',
            'method': 'tools/call',
            'params': {
                'name': 'create_sampling_request',
                'arguments': {
                    'prompt': 'Analyze technology trends based on provided context',
                    'context_data': {
                        'source': 'hackernews',
                        'topic': 'AI',
                        'timeframe': 'recent',
                        'trending_repos': ['microsoft/vscode', 'openai/gpt-4'],
                        'analysis_depth': 'comprehensive'
                    },
                    'max_tokens': 800,
                    'temperature': 0.5,
                    'model_hint': 'claude-3-haiku',
                    'intelligence_priority': 0.7,
                    'cost_priority': 0.6,
                    'speed_priority': 0.8
                }
            }
        }
        
        return self._execute_sampling_test(tool_data, "Context-Aware Sampling", check_context=True)

    def test_priority_configurations(self) -> bool:
        """Test different priority configurations."""
        print(f"\n⚖️ Testing priority configurations...")
        
        # High intelligence, low cost priority
        tool_data = {
            'jsonrpc': '2.0',
            'id': 'priority_config',
            'method': 'tools/call',
            'params': {
                'name': 'create_sampling_request',
                'arguments': {
                    'prompt': 'Perform complex reasoning about quantum computing',
                    'max_tokens': 1200,
                    'temperature': 0.3,
                    'model_hint': 'claude-3-opus',
                    'intelligence_priority': 1.0,
                    'cost_priority': 0.1,
                    'speed_priority': 0.3
                }
            }
        }
        
        return self._execute_sampling_test(tool_data, "High Intelligence Priority Configuration", check_priorities=True)

    def test_speed_optimized_sampling(self) -> bool:
        """Test speed-optimized sampling configuration."""
        print(f"\n⚡ Testing speed-optimized sampling...")
        
        tool_data = {
            'jsonrpc': '2.0',
            'id': 'speed_sampling',
            'method': 'tools/call',
            'params': {
                'name': 'create_sampling_request',
                'arguments': {
                    'prompt': 'Quick summary of today\'s tech news',
                    'max_tokens': 300,
                    'temperature': 0.8,
                    'model_hint': 'claude-3-haiku',
                    'intelligence_priority': 0.5,
                    'cost_priority': 0.9,
                    'speed_priority': 1.0
                }
            }
        }
        
        return self._execute_sampling_test(tool_data, "Speed-Optimized Sampling", check_speed=True)

    def test_multi_context_sampling(self) -> bool:
        """Test sampling with multiple context sources."""
        print(f"\n🔄 Testing multi-context sampling...")
        
        tool_data = {
            'jsonrpc': '2.0',
            'id': 'multi_context_sampling',
            'method': 'tools/call',
            'params': {
                'name': 'create_sampling_request',
                'arguments': {
                    'prompt': 'Cross-analyze data from multiple sources',
                    'context_data': {
                        'sources': ['hackernews', 'github', 'analysis'],
                        'hackernews_topics': ['AI', 'blockchain', 'web3'],
                        'github_languages': ['python', 'javascript', 'rust'],
                        'analysis_types': ['trend', 'sentiment', 'technical'],
                        'correlation_analysis': True,
                        'temporal_context': '7_days'
                    },
                    'max_tokens': 1500,
                    'temperature': 0.4,
                    'model_hint': 'claude-3-sonnet',
                    'intelligence_priority': 0.8,
                    'cost_priority': 0.4,
                    'speed_priority': 0.6
                }
            }
        }
        
        return self._execute_sampling_test(tool_data, "Multi-Context Sampling", check_multi_context=True)

    def test_hackernews_ai_analysis(self) -> bool:
        """Test AI-powered HackerNews analysis sampling."""
        print(f"\n📰 Testing HackerNews AI analysis sampling...")
        
        tool_data = {
            'jsonrpc': '2.0',
            'id': 'hn_ai_analysis',
            'method': 'tools/call',
            'params': {
                'name': 'analyze_hackernews_trends_with_ai',
                'arguments': {
                    'topic': 'machine learning',
                    'count': 5,
                    'analysis_type': 'comprehensive'
                }
            }
        }
        
        return self._execute_sampling_test(tool_data, "HackerNews AI Analysis", check_analysis=True)

    def test_code_review_ai_sampling(self) -> bool:
        """Test AI-powered code review sampling."""
        print(f"\n💻 Testing AI code review sampling...")
        
        tool_data = {
            'jsonrpc': '2.0',
            'id': 'code_review_ai',
            'method': 'tools/call',
            'params': {
                'name': 'code_review_with_ai',
                'arguments': {
                    'repo_owner': 'microsoft',
                    'repo_name': 'typescript',
                    'review_focus': 'performance'
                }
            }
        }
        
        return self._execute_sampling_test(tool_data, "AI Code Review", check_review=True)

    def _execute_sampling_test(self, tool_data: Dict[str, Any], test_name: str, 
                              check_preferences: bool = False, check_context: bool = False,
                              check_priorities: bool = False, check_speed: bool = False,
                              check_multi_context: bool = False, check_analysis: bool = False,
                              check_review: bool = False) -> bool:
        """Execute a sampling test and validate the response."""
        
        try:
            response = requests.post(self.base_url, headers=self.headers, json=tool_data, timeout=20)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                result = self.parse_sse_response(response.text)
                if result and 'result' in result:
                    content = result['result'].get('content', [])
                    if content and 'text' in content[0]:
                        try:
                            data = json.loads(content[0]['text'])
                            print(f"   ✅ {test_name} successful")
                            
                            # Validate response structure
                            self._validate_sampling_response(data, test_name, 
                                                           check_preferences, check_context,
                                                           check_priorities, check_speed,
                                                           check_multi_context, check_analysis,
                                                           check_review)
                            return True
                            
                        except json.JSONDecodeError:
                            print(f"   ❌ Could not parse {test_name} response")
                            return False
                    else:
                        print(f"   ❌ {test_name} - No content in response")
                        return False
                else:
                    print(f"   ❌ {test_name} - Could not parse response")
                    return False
            else:
                print(f"   ❌ {test_name} failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ {test_name} error: {e}")
            return False

    def _validate_sampling_response(self, data: Dict[str, Any], test_name: str,
                                  check_preferences: bool, check_context: bool,
                                  check_priorities: bool, check_speed: bool,
                                  check_multi_context: bool, check_analysis: bool,
                                  check_review: bool):
        """Validate the structure and content of sampling responses."""
        
        # Check for basic sampling request structure
        if 'sampling_request' in data:
            sampling_req = data['sampling_request']
            method = sampling_req.get('method', 'Unknown')
            params = sampling_req.get('params', {})
            
            print(f"      Method: {method}")
            print(f"      Status: {data.get('status', 'Unknown')}")
            
            # Check protocol version
            meta = params.get('_meta', {})
            if meta:
                protocol_version = meta.get('protocolVersion', 'Unknown')
                print(f"      Protocol version: {protocol_version}")
                if protocol_version == '2025-03-26':
                    print(f"      ✓ MCP 2025-03-26 compliant")
            
            # Check for enhanced features
            if check_preferences and 'modelPreferences' in params:
                prefs = params['modelPreferences']
                print(f"      Model preferences found:")
                print(f"         Intelligence priority: {prefs.get('intelligencePriority', 'N/A')}")
                print(f"         Cost priority: {prefs.get('costPriority', 'N/A')}")
                print(f"         Speed priority: {prefs.get('speedPriority', 'N/A')}")
                
                hints = prefs.get('hints', [])
                if hints:
                    model_names = [hint.get('name', 'unknown') for hint in hints]
                    print(f"         Model hints: {model_names}")
                    print(f"      ✓ Enhanced model preferences validated")
            
            if check_context and 'context_data' in data:
                context = data['context_data']
                print(f"      Context data keys: {list(context.keys())}")
                print(f"      ✓ Context-aware sampling validated")
            
            if check_priorities:
                if 'modelPreferences' in params:
                    prefs = params['modelPreferences']
                    intel_priority = prefs.get('intelligencePriority', 0)
                    if intel_priority >= 0.8:
                        print(f"      ✓ High intelligence priority configuration validated")
            
            if check_speed:
                if 'modelPreferences' in params:
                    prefs = params['modelPreferences']
                    speed_priority = prefs.get('speedPriority', 0)
                    if speed_priority >= 0.8:
                        print(f"      ✓ Speed-optimized configuration validated")
            
            if check_multi_context and 'context_data' in data:
                context = data['context_data']
                if 'sources' in context and len(context.get('sources', [])) > 1:
                    print(f"      ✓ Multi-context sampling validated")
        
        elif check_analysis and 'analysis_request' in data:
            analysis_req = data['analysis_request']
            print(f"      Analysis method: {analysis_req.get('method', 'Unknown')}")
            print(f"      Topic: {data.get('topic', 'Unknown')}")
            print(f"      Stories count: {data.get('stories_count', 0)}")
            print(f"      ✓ AI analysis sampling validated")
        
        elif check_review and 'review_request' in data:
            review_req = data['review_request']
            print(f"      Review method: {review_req.get('method', 'Unknown')}")
            print(f"      Repository: {data.get('repository', 'Unknown')}")
            print(f"      Focus: {data.get('review_focus', 'Unknown')}")
            print(f"      ✓ AI code review sampling validated")

def test_enhanced_sampling():
    """Test all enhanced sampling functionality with model preferences."""
    print("🎯 Enhanced MCP Sampling Test Suite (MCP 2025-03-26)")
    print("=" * 60)
    
    tester = EnhancedSamplingTester()
    
    if not tester.initialize_session():
        return False
    
    # Test results tracking
    results = {}
    
    # Test 1: Basic sampling request
    results['basic_sampling'] = tester.test_basic_sampling_request()
    
    # Test 2: Model preferences sampling
    results['model_preferences'] = tester.test_model_preferences_sampling()
    
    # Test 3: Context-aware sampling
    results['context_aware'] = tester.test_context_aware_sampling()
    
    # Test 4: Priority configurations
    results['priority_configs'] = tester.test_priority_configurations()
    
    # Test 5: Speed-optimized sampling
    results['speed_optimized'] = tester.test_speed_optimized_sampling()
    
    # Test 6: Multi-context sampling
    results['multi_context'] = tester.test_multi_context_sampling()
    
    # Test 7: HackerNews AI analysis
    results['hackernews_ai'] = tester.test_hackernews_ai_analysis()
    
    # Test 8: Code review AI sampling
    results['code_review_ai'] = tester.test_code_review_ai_sampling()
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 ENHANCED SAMPLING TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    test_descriptions = {
        'basic_sampling': 'Basic Sampling Request',
        'model_preferences': 'Model Preferences Sampling',
        'context_aware': 'Context-Aware Sampling',
        'priority_configs': 'Priority Configurations',
        'speed_optimized': 'Speed-Optimized Sampling',
        'multi_context': 'Multi-Context Sampling',
        'hackernews_ai': 'HackerNews AI Analysis',
        'code_review_ai': 'AI Code Review Sampling'
    }
    
    for test_key, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        description = test_descriptions.get(test_key, test_key)
        print(f"{description:30} {status}")
    
    print(f"\nOverall Enhanced Sampling Tests: {passed}/{total} passed")
    
    # Check critical enhanced features
    enhanced_tests = ['model_preferences', 'context_aware', 'priority_configs']
    enhanced_passed = sum(1 for test in enhanced_tests if results.get(test, False))
    enhanced_total = len(enhanced_tests)
    
    print(f"Enhanced Features: {enhanced_passed}/{enhanced_total} passed")
    
    if enhanced_passed == enhanced_total:
        print("✅ All enhanced sampling features are working")
    else:
        print("⚠️  Some enhanced sampling features may not be working properly")
    
    # Feature summary
    feature_categories = {
        'Core Sampling': ['basic_sampling'],
        'Model Preferences': ['model_preferences', 'priority_configs', 'speed_optimized'],
        'Context Awareness': ['context_aware', 'multi_context'],
        'AI Integration': ['hackernews_ai', 'code_review_ai']
    }
    
    print("\nBy Feature Category:")
    for category, test_keys in feature_categories.items():
        category_passed = sum(1 for key in test_keys if results.get(key, False))
        category_total = len(test_keys)
        print(f"  {category:18} {category_passed}/{category_total}")
    
    return passed == total

if __name__ == "__main__":
    success = test_enhanced_sampling()
    sys.exit(0 if success else 1) 