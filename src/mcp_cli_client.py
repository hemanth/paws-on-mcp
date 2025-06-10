#!/usr/bin/env python3
"""
MCP CLI Client

A command-line interface for interacting with MCP servers using the official MCP HTTP transport protocol.
"""

import argparse
import json
import sys
import requests
import textwrap
import uuid
from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from rich.panel import Panel
from rich import box

# Default server URL
DEFAULT_SERVER_URL = "http://127.0.0.1:8000"

# Initialize rich console for pretty output
console = Console()

class MCPClient:
    """Client for interacting with MCP servers using official MCP HTTP transport."""
    
    def __init__(self, server_url: str = DEFAULT_SERVER_URL):
        self.server_url = server_url.rstrip('/') + '/mcp/'
        self.session = requests.Session()
        self.session_id = None
        self.server_info = None
        self._initialize()
    
    def _initialize(self):
        """Initialize the MCP session."""
        try:
            # Step 1: Initialize
            init_payload = {
                "jsonrpc": "2.0",
                "id": "init",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {
                        "sampling": {}
                    },
                    "clientInfo": {
                        "name": "mcp-cli-client",
                        "version": "1.0.0"
                    }
                }
            }
            
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            }
            
            response = self.session.post(self.server_url, json=init_payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # Parse SSE format
                result = self._parse_sse_response(response.text)
                if result and "result" in result:
                    self.server_info = result.get("result", {})
                    self.session_id = response.headers.get('mcp-session-id')
                    
                    if not self.session_id:
                        raise Exception("No session ID received from server")
                    
                    # Step 2: Send initialized notification
                    initialized_payload = {
                        "jsonrpc": "2.0",
                        "method": "notifications/initialized"
                    }
                    
                    headers["MCP-Session-ID"] = self.session_id
                    notify_response = self.session.post(self.server_url, json=initialized_payload, headers=headers)
                    
                    if notify_response.status_code != 200:
                        console.print(f"[yellow]Warning: Initialized notification failed: {notify_response.status_code}[/]")
                        
                else:
                    raise Exception("Failed to parse initialization response")
            else:
                raise Exception(f"Failed to initialize: {response.status_code} - {response.text}")
                
        except Exception as e:
            console.print(f"[bold red]Error connecting to server:[/] {e}")
            sys.exit(1)
    
    def _parse_sse_response(self, content: str) -> Optional[Dict[str, Any]]:
        """Parse Server-Sent Events response format."""
        content = content.strip()
        if "data: " in content:
            lines = content.split('\n')
            for line in lines:
                if line.startswith("data: "):
                    try:
                        return json.loads(line[6:])
                    except json.JSONDecodeError:
                        continue
        return None
    
    def _make_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a request to the MCP server."""
        if not self.session_id:
            raise Exception("Not connected to server")
        
        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": method
        }
        
        if params:
            payload["params"] = params
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "MCP-Session-ID": self.session_id
        }
        
        try:
            response = self.session.post(self.server_url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = self._parse_sse_response(response.text)
                if result:
                    if "error" in result:
                        raise Exception(f"Server error: {result['error']}")
                    return result.get("result", {})
                else:
                    raise Exception("Failed to parse response")
            else:
                raise Exception(f"Request failed: {response.status_code} - {response.text}")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {e}")
        except Exception as e:
            raise Exception(f"Request error: {e}")
    
    def get_server_info(self) -> Dict[str, Any]:
        """Get information about the MCP server."""
        return self.server_info or {}
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools on the server."""
        result = self._make_request("tools/list")
        return result.get("tools", [])
    
    def list_resources(self) -> List[Dict[str, Any]]:
        """List all available resources on the server."""
        result = self._make_request("resources/list")
        return result.get("resources", [])
    
    def list_prompts(self) -> List[Dict[str, Any]]:
        """List all available prompt templates on the server."""
        try:
            # Use the tool endpoint instead of protocol endpoint
            result = self._make_request("tools/call", {
                "name": "get_server_prompts", 
                "arguments": {}
            })
            # Parse the response - each content item is a separate prompt
            content = result.get("content", [])
            prompts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    try:
                        import json
                        prompt_data = json.loads(item["text"])
                        prompts.append(prompt_data)
                    except json.JSONDecodeError:
                        continue
            return prompts
        except Exception:
            # Server might not support prompts endpoint
            return []
    
    def call_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on the server."""
        params = {
            "name": tool_name,
            "arguments": args
        }
        return self._make_request("tools/call", params)
    
    def get_resource(self, resource_uri: str) -> Dict[str, Any]:
        """Get a resource from the server."""
        params = {"uri": resource_uri}
        return self._make_request("resources/read", params)
    
    def read_root(self, root_uri: str) -> Dict[str, Any]:
        """Read a root resource from the server."""
        params = {"uri": root_uri}
        return self._make_request("resources/read", params)
    
    def get_prompt(self, prompt_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get a prompt from the server."""
        params = {
            "name": prompt_name,
            "arguments": args
        }
        return self._make_request("prompts/get", params)

    def list_roots(self) -> List[Dict[str, Any]]:
        """List all available roots on the server."""
        try:
            # Use the tool endpoint instead of protocol endpoint
            result = self._make_request("tools/call", {
                "name": "get_server_roots",
                "arguments": {}
            })
            # Parse the response - each content item is a separate root
            content = result.get("content", [])
            roots = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    try:
                        import json
                        root_data = json.loads(item["text"])
                        roots.append(root_data)
                    except json.JSONDecodeError:
                        continue
            return roots
        except Exception as e:
            print(f"Debug - roots error: {e}")
            # Server might not support roots endpoint
            return []

    def handle_sampling_request(self, sampling_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a sampling request from the server.
        
        This simulates how a real MCP client would handle sampling requests
        by showing what would be sent to an LLM.
        """
        if "sampling_request" not in sampling_data:
            return {"error": "No sampling request found in response"}
            
        request = sampling_data["sampling_request"]
        params = request.get("params", {})
        
        console.print(Panel(
            f"[bold yellow]🧠 Sampling Request Received[/]\n\n"
            f"[bold]Method:[/] {request.get('method', 'Unknown')}\n"
            f"[bold]Messages:[/] {len(params.get('messages', []))} message(s)\n"
            f"[bold]Max Tokens:[/] {params.get('maxTokens', 'Not specified')}\n"
            f"[bold]Temperature:[/] {params.get('temperature', 'Not specified')}\n"
            f"[bold]System Prompt:[/] {'Yes' if params.get('systemPrompt') else 'No'}\n"
            f"[bold]Include Context:[/] {params.get('includeContext', 'none')}\n\n"
            f"[dim]In a real implementation, this would be sent to your LLM provider.[/]",
            title="MCP Sampling Request",
            expand=False
        ))
        
        # Show the actual messages that would be sent
        messages = params.get("messages", [])
        for i, msg in enumerate(messages):
            content = msg.get("content", {})
            if isinstance(content, dict) and "text" in content:
                text = content["text"][:200] + "..." if len(content["text"]) > 200 else content["text"]
                console.print(f"[cyan]Message {i+1} ({msg.get('role', 'unknown')}):[/] {text}")
        
        # Return a simulated response
        return {
            "model": "simulated-claude-3-sonnet",
            "role": "assistant",
            "content": {
                "type": "text",
                "text": "This is a simulated LLM response. In a real implementation, this would contain the actual AI-generated analysis based on the sampling request."
            },
            "stopReason": "endTurn",
            "usage": {
                "inputTokens": sum(len(msg.get("content", {}).get("text", "")) for msg in messages) // 4,
                "outputTokens": 50
            }
        }

def display_server_info(client: MCPClient) -> None:
    """Display information about the connected MCP server."""
    server_info = client.get_server_info()
    server_details = server_info.get("serverInfo", {})
    
    console.print(Panel(
        f"[bold]Server Name:[/] {server_details.get('name', 'Unknown')}\n"
        f"[bold]Version:[/] {server_details.get('version', 'Unknown')}\n"
        f"[bold]Protocol Version:[/] {server_info.get('protocolVersion', 'Unknown')}\n"
        f"[bold]URL:[/] {client.server_url}",
        title="MCP Server Information",
        expand=False
    ))
    
    # Get actual counts
    tools = client.list_tools()
    resources = client.list_resources()
    try:
        roots = client.list_roots()
    except Exception:
        roots = []
    try:
        prompts = client.list_prompts()
    except Exception:
        prompts = []
    
    console.print(f"[bold]Available Components:[/]")
    console.print(f"  • [cyan]Tools:[/] {len(tools)}")
    console.print(f"  • [green]Resources:[/] {len(resources)}")
    if len(roots) > 0:
        console.print(f"  • [magenta]Roots:[/] {len(roots)}")
    else:
        console.print(f"  • [magenta]Roots:[/] Not supported")
    if len(prompts) > 0:
        console.print(f"  • [yellow]Prompt Templates:[/] {len(prompts)}")
    else:
        console.print(f"  • [yellow]Prompt Templates:[/] Not supported")

def display_tools(client: MCPClient) -> None:
    """Display all available tools on the server."""
    tools = client.list_tools()
    
    if not tools:
        console.print("[yellow]No tools available on this server.[/]")
        return
    
    table = Table(title="Available Tools", box=box.ROUNDED)
    table.add_column("Name", style="cyan bold")
    table.add_column("Description", style="white")
    table.add_column("Parameters", style="green")
    
    for tool in tools:
        # Parse inputSchema for parameters
        input_schema = tool.get("inputSchema", {})
        properties = input_schema.get("properties", {})
        required = input_schema.get("required", [])
        
        params = []
        for param, details in properties.items():
            param_type = details.get("type", "any")
            required_mark = "*" if param in required else ""
            params.append(f"{param}{required_mark}: {param_type}")
        
        param_str = "\n".join(params) if params else "None"
        
        table.add_row(
            tool.get("name", "Unknown"),
            tool.get("description", "No description"),
            param_str
        )
    
    console.print(table)
    console.print("\n[dim]* Parameter is required[/]")

def display_resources(client: MCPClient) -> None:
    """Display all available resources on the server."""
    resources = client.list_resources()
    
    if not resources:
        console.print("[yellow]No resources available on this server.[/]")
        return
    
    table = Table(title="Available Resources", box=box.ROUNDED)
    table.add_column("URI", style="green bold")
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="white")
    table.add_column("MIME Type", style="yellow")
    
    for resource in resources:
        table.add_row(
            resource.get("uri", "Unknown"),
            resource.get("name", "Unknown"),
            resource.get("description", "No description"),
            resource.get("mimeType", "Unknown")
        )
    
    console.print(table)

def display_roots(client: MCPClient) -> None:
    """Display all available roots on the server."""
    try:
        roots = client.list_roots()
        
        if not roots:
            console.print("[yellow]No roots available on this server.[/]")
            return
        
        table = Table(title="Available Roots (Server Sampling)", box=box.ROUNDED)
        table.add_column("URI", style="magenta bold")
        table.add_column("Name", style="cyan")
        table.add_column("Description", style="white")
        
        for root in roots:
            table.add_row(
                root.get("uri", "Unknown"),
                root.get("name", "Unknown"),
                root.get("description", "No description")
            )
        
        console.print(table)
    except Exception:
        console.print("[yellow]Roots endpoint not supported by this server.[/]")

def display_prompts(client: MCPClient) -> None:
    """Display all available prompt templates on the server."""
    try:
        prompts = client.list_prompts()
        
        if not prompts:
            console.print("[yellow]No prompt templates available on this server.[/]")
            return
        
        for prompt in prompts:
            console.print(Panel(
                f"[bold]Description:[/] {prompt.get('description', 'No description')}\n\n"
                f"[bold]Arguments:[/] {json.dumps(prompt.get('arguments', {}), indent=2)}",
                title=f"Prompt: {prompt.get('name', 'Unknown')}",
                expand=False
            ))
    except Exception:
        console.print("[yellow]Prompts endpoint not supported by this server.[/]")

def call_tool_interactive(client: MCPClient, tool_name: str, args: Optional[Dict[str, Any]] = None) -> None:
    """Call a tool interactively."""
    tools = client.list_tools()
    tool = next((t for t in tools if t["name"] == tool_name), None)
    
    if not tool:
        console.print(f"[bold red]Tool '{tool_name}' not found.[/]")
        return
    
    # If args not provided, prompt for them
    if args is None:
        args = {}
        input_schema = tool.get("inputSchema", {})
        properties = input_schema.get("properties", {})
        required = input_schema.get("required", [])
        
        if properties:
            console.print(f"[bold]Tool: {tool_name}[/]")
            console.print(f"[dim]{tool.get('description', 'No description')}[/]\n")
            
            for param, details in properties.items():
                param_type = details.get("type", "string")
                param_desc = details.get("description", "")
                default = details.get("default", None)
                required_mark = " (required)" if param in required else ""
                
                prompt_text = f"[cyan]{param}[/] ({param_type}){required_mark}"
                if param_desc:
                    prompt_text += f" - {param_desc}"
                if default is not None:
                    prompt_text += f" [default: {default}]"
                
                console.print(prompt_text)
                value = input(f"{param}: ").strip()
                
                if value:
                    # Try to convert to appropriate type
                    if param_type == "integer":
                        try:
                            args[param] = int(value)
                        except ValueError:
                            console.print(f"[yellow]Warning: '{value}' is not a valid integer[/]")
                            args[param] = value
                    elif param_type == "number":
                        try:
                            args[param] = float(value)
                        except ValueError:
                            console.print(f"[yellow]Warning: '{value}' is not a valid number[/]")
                            args[param] = value
                    elif param_type == "boolean":
                        args[param] = value.lower() in ("true", "yes", "1", "on")
                    else:
                        args[param] = value
                elif default is not None:
                    args[param] = default
    
    console.print(f"\n[bold]Calling tool:[/] {tool_name}")
    console.print(f"[bold]Arguments:[/] {json.dumps(args, indent=2)}")
    
    try:
        result = client.call_tool(tool_name, args)
        
        console.print(Panel(
            Syntax(json.dumps(result, indent=2), "json"),
            title=f"Tool Result: {tool_name}",
            expand=False
        ))
    except Exception as e:
        console.print(f"[bold red]Error calling tool:[/] {e}")

def get_resource_interactive(client: MCPClient, resource_uri: str) -> None:
    """Get a resource interactively."""
    console.print(f"\n[bold]Getting resource:[/] {resource_uri}")
    
    try:
        result = client.get_resource(resource_uri)
        
        console.print(Panel(
            Syntax(json.dumps(result, indent=2), "json"),
            title=f"Resource: {resource_uri}",
            expand=False
        ))
    except Exception as e:
        console.print(f"[bold red]Error getting resource:[/] {e}")

def render_prompt_interactive(client: MCPClient, prompt_name: str, args: Optional[Dict[str, Any]] = None) -> None:
    """Render a prompt template interactively."""
    prompts = client.list_prompts()
    prompt = next((p for p in prompts if p["name"] == prompt_name), None)
    
    if not prompt:
        console.print(f"[bold red]Prompt '{prompt_name}' not found.[/]")
        return
    
    # If args not provided, prompt for them
    if args is None:
        args = {}
        prompt_args = prompt.get("arguments", [])
        
        if prompt_args:
            console.print(f"[bold]Prompt: {prompt_name}[/]")
            console.print(f"[dim]{prompt.get('description', 'No description')}[/]\n")
            
            for arg in prompt_args:
                arg_name = arg.get("name", "")
                arg_desc = arg.get("description", "")
                required = arg.get("required", False)
                
                prompt_text = f"[cyan]{arg_name}[/]"
                if required:
                    prompt_text += " (required)"
                if arg_desc:
                    prompt_text += f" - {arg_desc}"
                
                console.print(prompt_text)
                value = input(f"{arg_name}: ").strip()
                
                if value:
                    args[arg_name] = value
    
    console.print(f"\n[bold]Rendering prompt:[/] {prompt_name}")
    console.print(f"[bold]Arguments:[/] {json.dumps(args, indent=2)}")
    
    try:
        result = client.get_prompt(prompt_name, args)
        
        console.print(Panel(
            Syntax(json.dumps(result, indent=2), "json"),
            title=f"Prompt Result: {prompt_name}",
            expand=False
        ))
    except Exception as e:
        console.print(f"[bold red]Error rendering prompt:[/] {e}")

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="MCP Client CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Server info
    subparsers.add_parser("info", help="Show server information")
    
    # List commands
    subparsers.add_parser("list-tools", help="List all available tools")
    subparsers.add_parser("list-resources", help="List all available resources")
    subparsers.add_parser("list-roots", help="List all available roots (server sampling)")
    subparsers.add_parser("list-prompts", help="List all available prompt templates")
    
    # Tool command
    tool_parser = subparsers.add_parser("tool", help="Call a tool")
    tool_parser.add_argument("name", help="Tool name")
    tool_parser.add_argument("--args", help="Tool arguments as JSON string")
    
    # Resource command
    resource_parser = subparsers.add_parser("resource", help="Get a resource")
    resource_parser.add_argument("uri", help="Resource URI")

    # Root command
    root_parser = subparsers.add_parser("root", help="Read a root resource")
    root_parser.add_argument("uri", help="Root URI")
    
    # Prompt command
    prompt_parser = subparsers.add_parser("prompt", help="Render a prompt template")
    prompt_parser.add_argument("name", help="Prompt name")
    prompt_parser.add_argument("--args", help="Prompt arguments as JSON string")
    
    # Interactive mode
    subparsers.add_parser("interactive", help="Start interactive mode")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize client
    client = MCPClient()
    
    if args.command == "info":
        display_server_info(client)
    elif args.command == "list-tools":
        display_tools(client)
    elif args.command == "list-resources":
        display_resources(client)
    elif args.command == "list-roots":
        display_roots(client)
    elif args.command == "list-prompts":
        display_prompts(client)
    elif args.command == "tool":
        # Parse arguments if provided
        tool_args = None
        if args.args:
            try:
                tool_args = json.loads(args.args)
            except json.JSONDecodeError as e:
                console.print(f"[red]Invalid JSON arguments: {e}[/]")
                return
        
        call_tool_interactive(client, args.name, tool_args)
    elif args.command == "resource":
        get_resource_interactive(client, args.uri)
    elif args.command == "root":
        read_root_interactive(client, args.uri)
    elif args.command == "prompt":
        # Parse arguments if provided
        prompt_args = None
        if args.args:
            try:
                prompt_args = json.loads(args.args)
            except json.JSONDecodeError as e:
                console.print(f"[red]Invalid JSON arguments: {e}[/]")
                return
        
        render_prompt_interactive(client, args.name, prompt_args)
    elif args.command == "interactive":
        start_interactive_mode(client)

def read_root_interactive(client: MCPClient, root_uri: str) -> None:
    """Read a root resource interactively."""
    console.print(f"[bold]Reading root:[/] {root_uri}")
    
    try:
        result = client.read_root(root_uri)
        
        console.print(Panel(
            f"[bold]URI:[/] {root_uri}\n\n"
            f"[bold]Result:[/]\n{json.dumps(result, indent=2)}",
            title="Root Resource Result",
            expand=False
        ))
        
    except Exception as e:
        console.print(f"[bold red]Error reading root '{root_uri}': {e}[/]")

def start_interactive_mode(client: MCPClient) -> None:
    """Start interactive CLI mode."""
    console.print("[bold blue]🎯 Interactive MCP Client[/]")
    console.print("Type 'help' for commands or 'quit' to exit.\n")
    
    while True:
        try:
            command = input("> ").strip().split()
            if not command:
                continue
                
            if command[0] == "quit" or command[0] == "exit":
                break
            elif command[0] == "help":
                console.print("""
[bold]Available commands:[/]
  info                    - Show server information
  list-tools             - List available tools  
  list-resources         - List available resources
  list-roots             - List available roots
  list-prompts           - List available prompts
  test-resources         - Test all resources
  test-roots             - Test all roots
  tool <name>            - Call a tool interactively
  resource <uri>         - Get a resource
  root <uri>             - Read a root resource
  prompt <name>          - Render a prompt
  help                   - Show this help
  quit/exit              - Exit interactive mode
                """)
            elif command[0] == "info":
                display_server_info(client)
            elif command[0] == "list-tools":
                display_tools(client)
            elif command[0] == "list-resources":
                display_resources(client)
            elif command[0] == "list-roots":
                display_roots(client)
            elif command[0] == "list-prompts":
                display_prompts(client)
            elif command[0] == "tool" and len(command) > 1:
                call_tool_interactive(client, command[1])
            elif command[0] == "resource" and len(command) > 1:
                get_resource_interactive(client, command[1])
            elif command[0] == "root" and len(command) > 1:
                read_root_interactive(client, command[1])
            elif command[0] == "prompt" and len(command) > 1:
                render_prompt_interactive(client, command[1])
            else:
                console.print("[yellow]Unknown command. Type 'help' for available commands.[/]")
                
        except KeyboardInterrupt:
            console.print("\n[yellow]Use 'quit' to exit.[/]")
        except EOFError:
            break
            
    console.print("\n[blue]Goodbye! 👋[/]")

if __name__ == "__main__":
    main()