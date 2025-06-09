#!/usr/bin/env python3
"""
Test suite for MCP Prompts functionality
Tests all available prompt templates: analyze_tech_trends, project_research,
competitive_analysis, learning_roadmap, and code_review_assistant.
"""

import requests
import json
import sys
import os
from typing import Dict, Any, Optional, List

# Removed src directory import to avoid conflicts with running server

class MCPPromptsTester:
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
        """Initialize MCP session with prompts capabilities."""
        init_data = {
            'jsonrpc': '2.0',
            'id': 'init',
            'method': 'initialize',
            'params': {
                'protocolVersion': '2025-03-26',
                'capabilities': {
                    'prompts': {},
                    'sampling': {},
                    'roots': {'listChanged': True}
                },
                'clientInfo': {'name': 'prompts-test', 'version': '1.0'}
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

    def list_prompts(self) -> Optional[List[Dict[str, Any]]]:
        """List all available prompts."""
        prompts_data = {
            'jsonrpc': '2.0',
            'id': 'list_prompts',
            'method': 'prompts/list'
        }
        
        try:
            response = requests.post(self.base_url, headers=self.headers, json=prompts_data, timeout=10)
            
            if response.status_code == 200:
                result = self.parse_sse_response(response.text)
                if result and 'result' in result:
                    return result['result'].get('prompts', [])
            
            return None
            
        except Exception as e:
            print(f"❌ Error listing prompts: {e}")
            return None

    def get_prompt(self, name: str, arguments: Dict[str, Any], test_name: str) -> bool:
        """Get a specific prompt with arguments and validate response."""
        prompt_data = {
            'jsonrpc': '2.0',
            'id': f'prompt_{name}',
            'method': 'prompts/get',
            'params': {
                'name': name,
                'arguments': arguments
            }
        }
        
        print(f"\n📝 Testing {test_name} ({name})...")
        
        try:
            response = requests.post(self.base_url, headers=self.headers, json=prompt_data, timeout=15)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                result = self.parse_sse_response(response.text)
                if result and 'result' in result:
                    messages = result['result'].get('messages', [])
                    if messages:
                        print(f"   ✅ {test_name} successful - {len(messages)} message(s)")
                        self._print_prompt_result(name, messages, test_name)
                        return True
                    else:
                        print(f"   ❌ {test_name} - No messages in response")
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

    def _print_prompt_result(self, prompt_name: str, messages: List[Dict[str, Any]], test_name: str):
        """Print formatted prompt result."""
        if messages:
            first_message = messages[0]
            role = first_message.get('role', 'unknown')
            content = first_message.get('content', {})
            
            if isinstance(content, dict) and 'text' in content:
                text = content['text']
                print(f"      Role: {role}")
                print(f"      Content length: {len(text)} characters")
                print(f"      Preview: {text[:100]}...")
                
                # Check for specific prompt characteristics
                if prompt_name == 'analyze_tech_trends':
                    if 'technology' in text.lower() and 'trends' in text.lower():
                        print(f"      ✓ Contains technology trends analysis elements")
                
                elif prompt_name == 'project_research':
                    if 'project' in text.lower() and 'research' in text.lower():
                        print(f"      ✓ Contains project research elements")
                
                elif prompt_name == 'competitive_analysis':
                    if 'competitive' in text.lower() or 'analysis' in text.lower():
                        print(f"      ✓ Contains competitive analysis elements")
                
                elif prompt_name == 'learning_roadmap':
                    if 'learning' in text.lower() and 'roadmap' in text.lower():
                        print(f"      ✓ Contains learning roadmap elements")
                
                elif prompt_name == 'code_review_assistant':
                    if 'code' in text.lower() and 'review' in text.lower():
                        print(f"      ✓ Contains code review elements")
                        
            elif isinstance(content, str):
                print(f"      Role: {role}")
                print(f"      Content length: {len(content)} characters")
                print(f"      Preview: {content[:100]}...")

def test_all_prompts():
    """Test all available MCP prompts."""
    print("📝 MCP Prompts Test Suite")
    print("=" * 50)
    
    tester = MCPPromptsTester()
    
    if not tester.initialize_session():
        return False
    
    # List available prompts first
    print("\n📋 Listing available prompts...")
    prompts = tester.list_prompts()
    if prompts:
        print(f"✅ Found {len(prompts)} available prompts:")
        for prompt in prompts:
            print(f"   • {prompt.get('name', 'Unknown')}: {prompt.get('description', 'No description')}")
            args = prompt.get('arguments', [])
            if args:
                print(f"     Arguments: {', '.join([arg.get('name', 'unknown') for arg in args])}")
    else:
        print("❌ Could not list prompts")
    
    # Test results tracking
    results = {}
    
    # Test prompt scenarios
    test_scenarios = [
        # analyze_tech_trends prompt variations
        {
            'name': 'analyze_tech_trends',
            'test_name': 'Tech Trends - AI (Default)',
            'arguments': {'technology_area': 'AI'}
        },
        {
            'name': 'analyze_tech_trends',
            'test_name': 'Tech Trends - Blockchain (Weekly)',
            'arguments': {
                'technology_area': 'blockchain',
                'time_period': 'week',
                'detail_level': 'comprehensive'
            }
        },
        {
            'name': 'analyze_tech_trends',
            'test_name': 'Tech Trends - Cloud Computing (Brief)',
            'arguments': {
                'technology_area': 'cloud computing',
                'time_period': 'month',
                'detail_level': 'brief'
            }
        },
        
        # project_research prompt variations
        {
            'name': 'project_research',
            'test_name': 'Project Research - Web App (Default)',
            'arguments': {'project_type': 'web application'}
        },
        {
            'name': 'project_research',
            'test_name': 'Project Research - Mobile App (React Native)',
            'arguments': {
                'project_type': 'mobile app',
                'tech_stack': 'React Native',
                'focus_area': 'performance'
            }
        },
        {
            'name': 'project_research',
            'test_name': 'Project Research - API (FastAPI)',
            'arguments': {
                'project_type': 'REST API',
                'tech_stack': 'FastAPI',
                'focus_area': 'best practices'
            }
        },
        
        # competitive_analysis prompt variations
        {
            'name': 'competitive_analysis',
            'test_name': 'Competitive Analysis - AI Tools (Default)',
            'arguments': {'domain': 'AI tools'}
        },
        {
            'name': 'competitive_analysis',
            'test_name': 'Competitive Analysis - Web Frameworks (Comprehensive)',
            'arguments': {
                'domain': 'web frameworks',
                'timeframe': 'trending',
                'analysis_depth': 'comprehensive'
            }
        },
        
        # learning_roadmap prompt variations
        {
            'name': 'learning_roadmap',
            'test_name': 'Learning Roadmap - Python (Default)',
            'arguments': {'skill_area': 'Python programming'}
        },
        {
            'name': 'learning_roadmap',
            'test_name': 'Learning Roadmap - Machine Learning (Advanced)',
            'arguments': {
                'skill_area': 'machine learning',
                'experience_level': 'advanced',
                'learning_style': 'project-based'
            }
        },
        {
            'name': 'learning_roadmap',
            'test_name': 'Learning Roadmap - DevOps (Intermediate)',
            'arguments': {
                'skill_area': 'DevOps',
                'experience_level': 'intermediate',
                'learning_style': 'practical'
            }
        },
        
        # code_review_assistant prompt variations
        {
            'name': 'code_review_assistant',
            'test_name': 'Code Review - General (Default)',
            'arguments': {}
        },
        {
            'name': 'code_review_assistant',
            'test_name': 'Code Review - Python Security',
            'arguments': {
                'language': 'Python',
                'review_focus': 'security',
                'project_context': 'enterprise'
            }
        },
        {
            'name': 'code_review_assistant',
            'test_name': 'Code Review - JavaScript Performance',
            'arguments': {
                'language': 'JavaScript',
                'review_focus': 'performance',
                'project_context': 'startup'
            }
        }
    ]
    
    # Test each prompt scenario
    for scenario in test_scenarios:
        test_key = f"{scenario['name']}_{scenario['test_name'].replace(' ', '_').replace('-', '_')}"
        results[test_key] = tester.get_prompt(
            scenario['name'],
            scenario['arguments'],
            scenario['test_name']
        )
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 PROMPTS TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    # Group results by prompt type
    prompt_types = {
        'analyze_tech_trends': [k for k in results.keys() if k.startswith('analyze_tech_trends')],
        'project_research': [k for k in results.keys() if k.startswith('project_research')],
        'competitive_analysis': [k for k in results.keys() if k.startswith('competitive_analysis')],
        'learning_roadmap': [k for k in results.keys() if k.startswith('learning_roadmap')],
        'code_review_assistant': [k for k in results.keys() if k.startswith('code_review_assistant')]
    }
    
    for prompt_type, test_keys in prompt_types.items():
        if test_keys:
            print(f"\n{prompt_type.upper().replace('_', ' ')} Prompts:")
            for test_key in test_keys:
                status = "✅ PASSED" if results[test_key] else "❌ FAILED"
                # Clean up display name
                display_name = test_key.replace(f"{prompt_type}_", "").replace("_", " ")
                print(f"  {display_name:40} {status}")
    
    print(f"\nOverall Prompts Tests: {passed}/{total} passed")
    
    # Print prompt type summary
    type_summary = {}
    for prompt_type, test_keys in prompt_types.items():
        if test_keys:
            type_passed = sum(1 for key in test_keys if results[key])
            type_total = len(test_keys)
            type_summary[prompt_type] = f"{type_passed}/{type_total}"
    
    if type_summary:
        print("\nBy Prompt Type:")
        for prompt_type, summary in type_summary.items():
            display_type = prompt_type.replace('_', ' ').title()
            print(f"  {display_type:20} {summary}")
    
    return passed == total

if __name__ == "__main__":
    success = test_all_prompts()
    sys.exit(0 if success else 1) 