#!/usr/bin/env python3
"""
Paws-on-MCP Test Runner
Comprehensive test suite for the organized MCP server implementation with enhanced testing.
"""

import subprocess
import sys
import time
import requests
import json
from pathlib import Path

def start_server():
    """Start the MCP server in the background or use existing one."""
    print("🚀 Checking MCP Server...")
    
    # First check if server is already running
    try:
        response = requests.get("http://127.0.0.1:8000/", timeout=5)
        print("✅ Server already running - using existing server")
        return None  # Return None to indicate we're using existing server
    except:
        pass  # Server not running, we'll start it
    
    print("🚀 Starting new MCP Server...")
    try:
        # Start server in src directory (go up one level from tests/)
        server_process = subprocess.Popen(
            [sys.executable, "../src/mcp_server.py"],
            cwd=Path.cwd().parent,  # Run from project root
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for server to start
        time.sleep(3)
        
        # Check if server is running
        try:
            response = requests.get("http://127.0.0.1:8000/", timeout=5)
            print("✅ New server started successfully")
            return server_process
        except:
            print("❌ Server failed to start")
            server_process.terminate()
            return False  # Return False to indicate failure
            
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return False

def stop_server(process):
    """Stop the MCP server only if we started it."""
    if process:  # Only stop if we have a process (we started it)
        process.terminate()
        process.wait()
        print("🛑 Server stopped")
    else:
        print("🔄 Using existing server - not stopping")

def run_test_file(test_file):
    """Run a specific test file and return results."""
    print(f"\n📋 Running {test_file}...")
    print("=" * 50)
    
    try:
        result = subprocess.run(
            [sys.executable, test_file],  # Run from tests directory
            cwd=Path.cwd(),  # Current directory (tests/)
            capture_output=True,
            text=True,
            timeout=60  # Increased timeout for comprehensive tests
        )
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
            
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print(f"❌ {test_file} timed out")
        return False
    except Exception as e:
        print(f"❌ Error running {test_file}: {e}")
        return False

def main():
    """Run all tests in the organized structure."""
    print("🧪 Paws-on-MCP Comprehensive Test Suite")
    print("=" * 60)
    print("Testing organized project structure with:")
    print("  • src/ - Source code")
    print("  • tests/ - Comprehensive component test suite") 
    print("  • docs/ - Documentation")
    print()
    
    # Check project structure (relative to parent directory)
    project_root = Path.cwd().parent
    required_dirs = ["src", "tests", "docs"]
    required_files = [
        "src/mcp_server.py",
        "src/mcp_cli_client.py",
        "tests/test_mcp_tools.py",
        "tests/test_mcp_resources.py", 
        "tests/test_mcp_prompts.py",
        "tests/test_mcp_roots.py",
        "tests/test_enhanced_sampling.py",
        "tests/test_mcp_cli_client.py",
        "docs/architecture.md",
        "README.md"
    ]
    
    print("📁 Checking project structure...")
    for dir_name in required_dirs:
        if (project_root / dir_name).exists():
            print(f"✅ {dir_name}/ directory exists")
        else:
            print(f"❌ {dir_name}/ directory missing")
            return False
    
    for file_path in required_files:
        if (project_root / file_path).exists():
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")
            return False
    
    print("\n✅ Project structure validated")
    
    # Start server
    server_process = start_server()
    if server_process is False:  # Failed to start
        return False
    
    try:
        # Run comprehensive test suite
        test_files = [
            "test_mcp_tools.py",      # Tests all 9 MCP tools
            "test_mcp_resources.py",  # Tests all 6 resource types
            "test_mcp_prompts.py",    # Tests all 5 prompt templates
            "test_mcp_roots.py",      # Tests MCP 2025-03-26 roots functionality
            "test_enhanced_sampling.py",  # Tests 8 sampling scenarios with model preferences
            "test_mcp_cli_client.py"  # Tests MCP CLI client functionality
        ]
        
        test_results = {}
        
        for test_file in test_files:
            test_results[test_file] = run_test_file(test_file)
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE TEST RESULTS SUMMARY")
        print("=" * 60)
        
        passed = 0
        total = len(test_files)
        
        test_descriptions = {
            "test_mcp_tools.py": "MCP Tools (9 tools)",
            "test_mcp_resources.py": "MCP Resources (6 types)", 
            "test_mcp_prompts.py": "MCP Prompts (5 templates)",
            "test_mcp_roots.py": "MCP Roots (2025-03-26)",
            "test_enhanced_sampling.py": "Enhanced Sampling (8 scenarios)",
            "test_mcp_cli_client.py": "MCP CLI Client (comprehensive)"
        }
        
        for test_file, result in test_results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            description = test_descriptions.get(test_file, test_file)
            print(f"{description:35} {status}")
            if result:
                passed += 1
        
        print(f"\nOverall Test Results: {passed}/{total} test suites passed")
        
        # Component breakdown
        print("\nComponent Test Coverage:")
        print("  🔧 Tools:     All 9 MCP tools tested")
        print("  📁 Resources: All 6 resource types tested")
        print("  📝 Prompts:   All 5 prompt templates tested")
        print("  🌳 Roots:     MCP 2025-03-26 compliance tested")
        print("  🎯 Sampling:  Enhanced features with model preferences tested")
        print("  🖥️  CLI Client: Interactive client interface tested")
        
        if passed == total:
            print("\n🎉 All comprehensive tests passed! The MCP server is fully functional.")
            print("✅ Tools, Resources, Prompts, Roots, Enhanced Sampling, and CLI Client all working correctly.")
            return True
        else:
            print(f"\n⚠️  {total - passed} test suite(s) failed. Check the output above for details.")
            return False
            
    finally:
        stop_server(server_process)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 