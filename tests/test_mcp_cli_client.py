#!/usr/bin/env python3
"""
Test suite for MCP CLI Client

Tests the command-line interface for interacting with MCP servers.
"""

import unittest
import json
import sys
import io
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock, call
from contextlib import redirect_stdout, redirect_stderr
import argparse

# Add src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import modules to test
import mcp_cli_client
from mcp_cli_client import MCPClient


class TestMCPClient(unittest.TestCase):
    """Test cases for the MCPClient class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_session = Mock()
        self.mock_response = Mock()
        self.mock_response.status_code = 200
        self.mock_response.headers = {'mcp-session-id': 'test-session-123'}
        
        # Mock successful initialization response
        init_response_data = {
            "jsonrpc": "2.0",
            "id": "init",
            "result": {
                "protocolVersion": "2025-03-26",
                "capabilities": {
                    "logging": {},
                    "prompts": {"listChanged": True},
                    "resources": {"subscribe": True, "listChanged": True},
                    "tools": {"listChanged": True},
                    "sampling": {},
                    "roots": {"listChanged": True},
                    "experimental": {}
                },
                "serverInfo": {
                    "name": "test-server",
                    "version": "1.0.0"
                }
            }
        }
        
        self.mock_response.text = f"data: {json.dumps(init_response_data)}\n\n"
        self.mock_session.post.return_value = self.mock_response
    
    @patch('mcp_cli_client.requests.Session')
    def test_client_initialization_success(self, mock_session_class):
        """Test successful client initialization."""
        mock_session_class.return_value = self.mock_session
        
        client = MCPClient("http://test-server:8000")
        
        # Verify initialization call was made
        self.mock_session.post.assert_called()
        init_call = self.mock_session.post.call_args_list[0]
        init_payload = init_call[1]['json']
        
        self.assertEqual(init_payload['method'], 'initialize')
        self.assertEqual(init_payload['params']['protocolVersion'], '2024-11-05')
        self.assertIn('capabilities', init_payload['params'])
        
        # Verify session was established
        self.assertEqual(client.session_id, 'test-session-123')
        self.assertIsNotNone(client.server_info)
    
    @patch('mcp_cli_client.requests.Session')
    def test_client_initialization_failure(self, mock_session_class):
        """Test client initialization failure."""
        mock_session_class.return_value = self.mock_session
        self.mock_response.status_code = 500
        self.mock_response.text = "Internal Server Error"
        
        with patch('sys.exit') as mock_exit:
            with patch('mcp_cli_client.console.print') as mock_print:
                MCPClient("http://test-server:8000")
                mock_exit.assert_called_with(1)
                mock_print.assert_called()
    
    def test_parse_sse_response_valid(self):
        """Test parsing valid SSE response."""
        client = MCPClient.__new__(MCPClient)  # Create instance without __init__
        
        sse_content = "data: {\"jsonrpc\": \"2.0\", \"result\": {\"test\": \"value\"}}\n\n"
        result = client._parse_sse_response(sse_content)
        
        self.assertEqual(result['jsonrpc'], '2.0')
        self.assertEqual(result['result']['test'], 'value')
    
    def test_parse_sse_response_invalid(self):
        """Test parsing invalid SSE response."""
        client = MCPClient.__new__(MCPClient)  # Create instance without __init__
        
        sse_content = "invalid content"
        result = client._parse_sse_response(sse_content)
        
        self.assertIsNone(result)
    
    @patch('mcp_cli_client.requests.Session')
    def test_make_request_success(self, mock_session_class):
        """Test successful request to server."""
        mock_session_class.return_value = self.mock_session
        client = MCPClient("http://test-server:8000")
        
        # Mock successful tool list response
        tool_response = {
            "jsonrpc": "2.0",
            "id": "test-id",
            "result": {
                "tools": [
                    {
                        "name": "test_tool",
                        "description": "A test tool",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    }
                ]
            }
        }
        
        self.mock_response.text = f"data: {json.dumps(tool_response)}\n\n"
        
        result = client._make_request("tools/list")
        
        self.assertEqual(len(result['tools']), 1)
        self.assertEqual(result['tools'][0]['name'], 'test_tool')
    
    @patch('mcp_cli_client.requests.Session')
    def test_make_request_error_response(self, mock_session_class):
        """Test request with error response from server."""
        mock_session_class.return_value = self.mock_session
        client = MCPClient("http://test-server:8000")
        
        # Mock error response
        error_response = {
            "jsonrpc": "2.0",
            "id": "test-id",
            "error": {
                "code": -32601,
                "message": "Method not found"
            }
        }
        
        self.mock_response.text = f"data: {json.dumps(error_response)}\n\n"
        
        with self.assertRaises(Exception) as context:
            client._make_request("invalid/method")
        
        self.assertIn("Method not found", str(context.exception))
    
    @patch('mcp_cli_client.requests.Session')
    def test_list_tools(self, mock_session_class):
        """Test listing tools."""
        mock_session_class.return_value = self.mock_session
        client = MCPClient("http://test-server:8000")
        
        # Mock tools response
        tools_response = {
            "jsonrpc": "2.0",
            "result": {
                "tools": [
                    {
                        "name": "search_hackernews",
                        "description": "Search HackerNews stories",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string"},
                                "limit": {"type": "integer"}
                            },
                            "required": ["query"]
                        }
                    }
                ]
            }
        }
        
        self.mock_response.text = f"data: {json.dumps(tools_response)}\n\n"
        
        tools = client.list_tools()
        
        self.assertEqual(len(tools), 1)
        self.assertEqual(tools[0]['name'], 'search_hackernews')
        self.assertIn('query', tools[0]['inputSchema']['properties'])
    
    @patch('mcp_cli_client.requests.Session')
    def test_call_tool(self, mock_session_class):
        """Test calling a tool."""
        mock_session_class.return_value = self.mock_session
        client = MCPClient("http://test-server:8000")
        
        # Mock tool call response
        tool_response = {
            "jsonrpc": "2.0",
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": "Tool executed successfully"
                    }
                ]
            }
        }
        
        self.mock_response.text = f"data: {json.dumps(tool_response)}\n\n"
        
        result = client.call_tool("test_tool", {"param": "value"})
        
        self.assertIn('content', result)
        self.assertEqual(result['content'][0]['text'], 'Tool executed successfully')
    
    @patch('mcp_cli_client.requests.Session')
    def test_list_resources(self, mock_session_class):
        """Test listing resources."""
        mock_session_class.return_value = self.mock_session
        client = MCPClient("http://test-server:8000")
        
        # Mock resources response
        resources_response = {
            "jsonrpc": "2.0",
            "result": {
                "resources": [
                    {
                        "uri": "hackernews://top/5",
                        "name": "Top HackerNews Stories",
                        "description": "Get top stories from HackerNews",
                        "mimeType": "application/json"
                    }
                ]
            }
        }
        
        self.mock_response.text = f"data: {json.dumps(resources_response)}\n\n"
        
        resources = client.list_resources()
        
        self.assertEqual(len(resources), 1)
        self.assertEqual(resources[0]['uri'], 'hackernews://top/5')
    
    @patch('mcp_cli_client.requests.Session')
    def test_get_resource(self, mock_session_class):
        """Test getting a resource."""
        mock_session_class.return_value = self.mock_session
        client = MCPClient("http://test-server:8000")
        
        # Mock resource content response
        resource_response = {
            "jsonrpc": "2.0",
            "result": {
                "contents": [
                    {
                        "uri": "hackernews://top/5",
                        "mimeType": "application/json",
                        "text": "[{\"title\": \"Test Story\", \"score\": 100}]"
                    }
                ]
            }
        }
        
        self.mock_response.text = f"data: {json.dumps(resource_response)}\n\n"
        
        result = client.get_resource("hackernews://top/5")
        
        self.assertIn('contents', result)
        self.assertEqual(len(result['contents']), 1)
    
    @patch('mcp_cli_client.requests.Session')
    def test_handle_sampling_request(self, mock_session_class):
        """Test handling sampling requests."""
        mock_session_class.return_value = self.mock_session
        client = MCPClient("http://test-server:8000")
        
        sampling_data = {
            "sampling_request": {
                "method": "sampling/createMessage",
                "params": {
                    "messages": [
                        {
                            "role": "user",
                            "content": {
                                "type": "text",
                                "text": "Analyze this data"
                            }
                        }
                    ],
                    "maxTokens": 1000,
                    "temperature": 0.7,
                    "systemPrompt": "You are a helpful assistant"
                }
            }
        }
        
        with patch('mcp_cli_client.console.print') as mock_print:
            result = client.handle_sampling_request(sampling_data)
            
            # Should print sampling request details
            mock_print.assert_called()
            
            # Should return simulated response
            self.assertIn('model', result)
            self.assertIn('content', result)
            self.assertEqual(result['role'], 'assistant')


class TestCLIFunctions(unittest.TestCase):
    """Test cases for CLI display and interaction functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_client = Mock(spec=MCPClient)
        self.mock_client.server_url = "http://test-server:8000/mcp/"
        self.mock_client.get_server_info.return_value = {
            "protocolVersion": "2025-03-26",
            "serverInfo": {
                "name": "test-server",
                "version": "1.0.0"
            }
        }
    
    @patch('mcp_cli_client.console.print')
    def test_display_server_info(self, mock_print):
        """Test displaying server information."""
        self.mock_client.list_tools.return_value = [{"name": "tool1"}]
        self.mock_client.list_resources.return_value = [{"uri": "test://resource"}]
        self.mock_client.list_roots.return_value = []
        self.mock_client.list_prompts.return_value = []
        
        mcp_cli_client.display_server_info(self.mock_client)
        
        # Should print server info
        mock_print.assert_called()
        
        # Check that client methods were called
        self.mock_client.get_server_info.assert_called_once()
        self.mock_client.list_tools.assert_called_once()
        self.mock_client.list_resources.assert_called_once()
    
    @patch('mcp_cli_client.console.print')
    def test_display_tools(self, mock_print):
        """Test displaying tools."""
        self.mock_client.list_tools.return_value = [
            {
                "name": "test_tool",
                "description": "A test tool",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "param1": {"type": "string"},
                        "param2": {"type": "integer"}
                    },
                    "required": ["param1"]
                }
            }
        ]
        
        mcp_cli_client.display_tools(self.mock_client)
        
        mock_print.assert_called()
        self.mock_client.list_tools.assert_called_once()
    
    @patch('mcp_cli_client.console.print')
    def test_display_tools_empty(self, mock_print):
        """Test displaying tools when none available."""
        self.mock_client.list_tools.return_value = []
        
        mcp_cli_client.display_tools(self.mock_client)
        
        # Should show "no tools available" message
        mock_print.assert_called()
        self.mock_client.list_tools.assert_called_once()
    
    @patch('mcp_cli_client.console.print')
    def test_display_resources(self, mock_print):
        """Test displaying resources."""
        self.mock_client.list_resources.return_value = [
            {
                "uri": "test://resource",
                "name": "Test Resource",
                "description": "A test resource",
                "mimeType": "application/json"
            }
        ]
        
        mcp_cli_client.display_resources(self.mock_client)
        
        mock_print.assert_called()
        self.mock_client.list_resources.assert_called_once()
    
    @patch('mcp_cli_client.console.print')
    @patch('builtins.input', side_effect=['test_value', '42', ''])
    def test_call_tool_interactive(self, mock_input, mock_print):
        """Test interactive tool calling."""
        self.mock_client.list_tools.return_value = [
            {
                "name": "test_tool",
                "description": "A test tool",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "param1": {"type": "string", "description": "String parameter"},
                        "param2": {"type": "integer", "description": "Integer parameter"},
                        "param3": {"type": "string", "default": "default_value"}
                    },
                    "required": ["param1"]
                }
            }
        ]
        
        self.mock_client.call_tool.return_value = {
            "content": [{"type": "text", "text": "Success"}]
        }
        
        mcp_cli_client.call_tool_interactive(self.mock_client, "test_tool")
        
        # Should call the tool with processed arguments
        self.mock_client.call_tool.assert_called_once()
        call_args = self.mock_client.call_tool.call_args[0]
        self.assertEqual(call_args[0], "test_tool")
        
        # Should have processed the input values
        args = call_args[1]
        self.assertEqual(args["param1"], "test_value")
        self.assertEqual(args["param2"], 42)  # Should be converted to int
        self.assertEqual(args["param3"], "default_value")  # Should use default
    
    @patch('mcp_cli_client.console.print')
    def test_call_tool_interactive_not_found(self, mock_print):
        """Test interactive tool calling with non-existent tool."""
        self.mock_client.list_tools.return_value = []
        
        mcp_cli_client.call_tool_interactive(self.mock_client, "nonexistent_tool")
        
        # Should print error message
        mock_print.assert_called()
        # Should not call the tool
        self.mock_client.call_tool.assert_not_called()
    
    @patch('mcp_cli_client.console.print')
    def test_get_resource_interactive(self, mock_print):
        """Test interactive resource getting."""
        self.mock_client.get_resource.return_value = {
            "contents": [
                {
                    "uri": "test://resource",
                    "mimeType": "application/json",
                    "text": "{\"data\": \"value\"}"
                }
            ]
        }
        
        mcp_cli_client.get_resource_interactive(self.mock_client, "test://resource")
        
        self.mock_client.get_resource.assert_called_once_with("test://resource")
        mock_print.assert_called()


class TestCLICommands(unittest.TestCase):
    """Test cases for CLI command parsing and execution."""
    
    @patch('mcp_cli_client.MCPClient')
    @patch('mcp_cli_client.display_server_info')
    def test_main_info_command(self, mock_display, mock_client_class):
        """Test 'info' command."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        with patch('sys.argv', ['mcp_cli_client.py', 'info']):
            mcp_cli_client.main()
        
        mock_client_class.assert_called_once()
        mock_display.assert_called_once_with(mock_client)
    
    @patch('mcp_cli_client.MCPClient')
    @patch('mcp_cli_client.display_tools')
    def test_main_list_tools_command(self, mock_display, mock_client_class):
        """Test 'list-tools' command."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        with patch('sys.argv', ['mcp_cli_client.py', 'list-tools']):
            mcp_cli_client.main()
        
        mock_display.assert_called_once_with(mock_client)
    
    @patch('mcp_cli_client.MCPClient')
    @patch('mcp_cli_client.call_tool_interactive')
    def test_main_tool_command(self, mock_call_tool, mock_client_class):
        """Test 'tool' command."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        test_args = '{"param": "value"}'
        with patch('sys.argv', ['mcp_cli_client.py', 'tool', 'test_tool', '--args', test_args]):
            mcp_cli_client.main()
        
        mock_call_tool.assert_called_once()
        call_args = mock_call_tool.call_args[0]
        self.assertEqual(call_args[1], 'test_tool')
        self.assertEqual(call_args[2], {"param": "value"})
    
    @patch('mcp_cli_client.MCPClient')
    @patch('mcp_cli_client.console.print')
    def test_main_tool_command_invalid_json(self, mock_print, mock_client_class):
        """Test 'tool' command with invalid JSON args."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        with patch('sys.argv', ['mcp_cli_client.py', 'tool', 'test_tool', '--args', 'invalid_json']):
            mcp_cli_client.main()
        
        # Should print error about invalid JSON
        mock_print.assert_called()
    
    @patch('mcp_cli_client.MCPClient')
    @patch('mcp_cli_client.test_comprehensive_mcp_features')
    def test_main_test_comprehensive_command(self, mock_test, mock_client_class):
        """Test 'test-comprehensive' command."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        with patch('sys.argv', ['mcp_cli_client.py', 'test-comprehensive']):
            mcp_cli_client.main()
        
        mock_test.assert_called_once_with(mock_client)


class TestTestFunctions(unittest.TestCase):
    """Test cases for the testing functions in the CLI client."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_client = Mock(spec=MCPClient)
    
    @patch('mcp_cli_client.console.print')
    def test_test_all_resources(self, mock_print):
        """Test the test_all_resources function."""
        self.mock_client.list_resources.return_value = [
            {
                "uri": "hackernews://top/3",
                "name": "Top Stories",
                "description": "Get top HackerNews stories"
            }
        ]
        
        self.mock_client.get_resource.return_value = {
            "contents": [
                {
                    "uri": "hackernews://top/3",
                    "mimeType": "application/json",
                    "text": "[{\"title\": \"Test Story\", \"score\": 100}]"
                }
            ]
        }
        
        mcp_cli_client.test_all_resources(self.mock_client)
        
        # Should list and test resources
        self.mock_client.list_resources.assert_called_once()
        self.mock_client.get_resource.assert_called_once_with("hackernews://top/3")
        mock_print.assert_called()
    
    @patch('mcp_cli_client.console.print')
    def test_test_all_resources_empty(self, mock_print):
        """Test test_all_resources with no resources."""
        self.mock_client.list_resources.return_value = []
        
        mcp_cli_client.test_all_resources(self.mock_client)
        
        self.mock_client.list_resources.assert_called_once()
        mock_print.assert_called()
    
    @patch('mcp_cli_client.console.print')
    def test_test_all_roots(self, mock_print):
        """Test the test_all_roots function."""
        self.mock_client.list_roots.return_value = [
            {
                "uri": "sampling://ai-analysis",
                "name": "AI Analysis Root",
                "description": "Root for AI analysis sampling"
            }
        ]
        
        self.mock_client.read_root.return_value = {
            "contents": [
                {
                    "uri": "sampling://ai-analysis",
                    "mimeType": "application/json",
                    "text": "{\"capability\": \"analysis\"}"
                }
            ]
        }
        
        mcp_cli_client.test_all_roots(self.mock_client)
        
        # Should list and test roots
        self.mock_client.list_roots.assert_called_once()
        self.mock_client.read_root.assert_called_once_with("sampling://ai-analysis")
        mock_print.assert_called()
    
    @patch('mcp_cli_client.console.print')
    def test_test_comprehensive_mcp_features(self, mock_print):
        """Test comprehensive MCP feature testing."""
        # Mock all the client methods
        self.mock_client.list_tools.return_value = [{"name": "test_tool"}]
        self.mock_client.list_resources.return_value = [{"uri": "test://resource"}]
        self.mock_client.list_roots.return_value = [{"uri": "test://root"}]
        self.mock_client.list_prompts.return_value = [{"name": "test_prompt"}]
        
        self.mock_client.call_tool.return_value = {
            "content": [{"type": "text", "text": "Success"}]
        }
        
        self.mock_client.get_resource.return_value = {
            "contents": [{"text": "Resource content"}]
        }
        
        self.mock_client.get_prompt.return_value = {
            "messages": [{"role": "user", "content": {"type": "text", "text": "Test prompt"}}]
        }
        
        mcp_cli_client.test_comprehensive_mcp_features(self.mock_client)
        
        # Should call various client methods
        self.mock_client.list_tools.assert_called()
        self.mock_client.list_resources.assert_called()
        self.mock_client.call_tool.assert_called()
        mock_print.assert_called()


class TestInteractiveMode(unittest.TestCase):
    """Test cases for interactive CLI mode."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_client = Mock(spec=MCPClient)
    
    @patch('builtins.input', side_effect=['help', 'quit'])
    @patch('mcp_cli_client.console.print')
    def test_interactive_mode_help(self, mock_print, mock_input):
        """Test interactive mode help command."""
        mcp_cli_client.start_interactive_mode(self.mock_client)
        
        # Should print help information
        mock_print.assert_called()
    
    @patch('builtins.input', side_effect=['info', 'quit'])
    @patch('mcp_cli_client.display_server_info')
    @patch('mcp_cli_client.console.print')
    def test_interactive_mode_info(self, mock_print, mock_display, mock_input):
        """Test interactive mode info command."""
        mcp_cli_client.start_interactive_mode(self.mock_client)
        
        # Should call display_server_info
        mock_display.assert_called_once_with(self.mock_client)
    
    @patch('builtins.input', side_effect=['unknown_command', 'quit'])
    @patch('mcp_cli_client.console.print')
    def test_interactive_mode_unknown_command(self, mock_print, mock_input):
        """Test interactive mode with unknown command."""
        mcp_cli_client.start_interactive_mode(self.mock_client)
        
        # Should print unknown command message
        mock_print.assert_called()
    
    @patch('builtins.input', side_effect=[KeyboardInterrupt, 'quit'])
    @patch('mcp_cli_client.console.print')
    def test_interactive_mode_keyboard_interrupt(self, mock_print, mock_input):
        """Test interactive mode with keyboard interrupt."""
        mcp_cli_client.start_interactive_mode(self.mock_client)
        
        # Should handle KeyboardInterrupt gracefully
        mock_print.assert_called()


class TestErrorHandling(unittest.TestCase):
    """Test cases for error handling scenarios."""
    
    @patch('mcp_cli_client.requests.Session')
    def test_network_error_handling(self, mock_session_class):
        """Test handling of network errors."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        # Mock network error
        import requests
        mock_session.post.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        with patch('sys.exit') as mock_exit:
            with patch('mcp_cli_client.console.print') as mock_print:
                MCPClient("http://unreachable-server:8000")
                mock_exit.assert_called_with(1)
    
    @patch('mcp_cli_client.requests.Session')
    def test_timeout_error_handling(self, mock_session_class):
        """Test handling of timeout errors."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        # Mock timeout error
        import requests
        mock_session.post.side_effect = requests.exceptions.Timeout("Request timed out")
        
        with patch('sys.exit') as mock_exit:
            with patch('mcp_cli_client.console.print') as mock_print:
                MCPClient("http://slow-server:8000")
                mock_exit.assert_called_with(1)
    
    @patch('mcp_cli_client.requests.Session')
    def test_invalid_json_response_handling(self, mock_session_class):
        """Test handling of invalid JSON responses."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'mcp-session-id': 'test-session'}
        mock_response.text = "data: invalid json content\n\n"
        mock_session.post.return_value = mock_response
        
        with patch('sys.exit') as mock_exit:
            with patch('mcp_cli_client.console.print') as mock_print:
                MCPClient("http://test-server:8000")
                mock_exit.assert_called_with(1)


def run_cli_client_tests():
    """Run all CLI client tests."""
    test_classes = [
        TestMCPClient,
        TestCLIFunctions,
        TestCLICommands,
        TestTestFunctions,
        TestInteractiveMode,
        TestErrorHandling
    ]
    
    suite = unittest.TestSuite()
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    print("🧪 Running MCP CLI Client Tests")
    print("=" * 50)
    
    success = run_cli_client_tests()
    
    if success:
        print("\n✅ All CLI client tests passed!")
    else:
        print("\n❌ Some CLI client tests failed!")
        sys.exit(1) 