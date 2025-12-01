#!/usr/bin/env python3
"""
Tool Inventory - Discovers and manages workspace tools
Critical component: Prefer existing tools over creating new code
"""

import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import re


@dataclass
class ToolInfo:
    """Information about a workspace tool"""
    name: str
    path: Path
    description: str
    capabilities: List[str]
    last_modified: datetime
    
    def matches(self, functions: List[str], intent: str) -> bool:
        """Check if this tool matches the query"""
        name_lower = self.name.lower()
        
        # Match function names
        for func in functions:
            if func.lower() in name_lower:
                # Match intent
                if intent in ['query', 'analyze'] and 'analysis' in name_lower:
                    return True
                if intent in ['visualize', 'show', 'display'] and 'chart' in name_lower:
                    return True
                if intent == 'compare' and 'compare' in name_lower:
                    return True
        
        return False


class ToolInventory:
    """
    Discovers and manages available workspace tools.
    
    Key principle: Use existing tools before creating new code.
    This is how Kiro works - check what exists first!
    """
    
    def __init__(self, workspace_path: str = "."):
        self.workspace_path = Path(workspace_path)
        self.tools: Dict[str, ToolInfo] = {}
        self.scan_workspace()
    
    def scan_workspace(self):
        """Scan workspace for existing analysis scripts"""
        print("🔍 Scanning workspace for existing tools...")
        
        # Find analysis scripts
        patterns = [
            "*_analysis.py",
            "*_chart.py",
            "*_salary*.py",
            "compare_*.py",
        ]
        
        for pattern in patterns:
            for script in self.workspace_path.glob(pattern):
                if script.name.startswith('enhanced_'):
                    continue  # Skip our own enhanced agent files
                if script.name.startswith('test_'):
                    continue  # Skip test files
                
                self._register_tool(script)
        
        print(f"   Found {len(self.tools)} tools")
        for tool_name in list(self.tools.keys())[:5]:  # Show first 5
            print(f"   • {tool_name}")
        if len(self.tools) > 5:
            print(f"   ... and {len(self.tools) - 5} more")

    def _register_tool(self, script_path: Path):
        """Register a tool with metadata"""
        try:
            # Extract description from docstring
            description = self._extract_description(script_path)
            
            # Infer capabilities from filename
            capabilities = self._infer_capabilities(script_path.stem)
            
            tool_info = ToolInfo(
                name=script_path.stem,
                path=script_path,
                description=description,
                capabilities=capabilities,
                last_modified=datetime.fromtimestamp(script_path.stat().st_mtime)
            )
            
            self.tools[script_path.stem] = tool_info
            
        except Exception as e:
            print(f"   ⚠️  Could not register {script_path.name}: {e}")
    
    def _extract_description(self, script_path: Path) -> str:
        """Extract description from script docstring"""
        try:
            with open(script_path, 'r') as f:
                content = f.read(500)  # Read first 500 chars
                
                # Look for docstring
                match = re.search(r'"""(.+?)"""', content, re.DOTALL)
                if match:
                    return match.group(1).strip().split('\n')[0]
                
                # Fallback to filename
                return f"Analysis script: {script_path.stem}"
        except:
            return f"Tool: {script_path.stem}"
    
    def _infer_capabilities(self, tool_name: str) -> List[str]:
        """Infer capabilities from tool name"""
        capabilities = []
        
        name_lower = tool_name.lower()
        
        if 'engineering' in name_lower:
            capabilities.append('engineering')
        if 'finance' in name_lower:
            capabilities.append('finance')
        if 'sales' in name_lower:
            capabilities.append('sales')
        if 'hr' in name_lower or 'human' in name_lower:
            capabilities.append('human_resources')
        
        if 'analysis' in name_lower:
            capabilities.append('analyze')
        if 'chart' in name_lower or 'graph' in name_lower:
            capabilities.append('visualize')
        if 'compare' in name_lower:
            capabilities.append('compare')
        
        return capabilities
    
    def match_query_to_tool(self, question: str, entities: Dict[str, Any]) -> Optional[str]:
        """
        Match user query to existing tool.
        
        This is the KEY function - prefer existing tools!
        
        Args:
            question: User's question
            entities: Extracted entities (functions, intent, etc.)
            
        Returns:
            Tool name if match found, None otherwise
        """
        functions = entities.get('functions', [])
        intent = entities.get('intent', 'query')
        
        if not functions:
            return None
        
        # Try exact matches first
        for tool_name, tool_info in self.tools.items():
            if tool_info.matches(functions, intent):
                return tool_name
        
        # For simple queries (not comparisons), only match if tool name
        # contains ONLY the function name (not multiple functions)
        if intent in ['query', 'analyze', 'visualize'] and len(functions) == 1:
            func = functions[0]
            func_lower = func.lower()
            
            for tool_name in self.tools.keys():
                tool_lower = tool_name.lower()
                # Only match if:
                # 1. Tool contains the function name
                # 2. Tool doesn't contain "vs" or multiple function names
                if func_lower in tool_lower and 'vs' not in tool_lower and '_vs_' not in tool_lower:
                    # Make sure it's not a comparison tool
                    other_functions = ['engineering', 'finance', 'sales', 'marketing', 'hr']
                    other_functions.remove(func_lower)
                    
                    # Check if tool contains other function names
                    has_other_functions = any(other in tool_lower for other in other_functions)
                    if not has_other_functions:
                        return tool_name
        
        # For comparison queries, match tools with "vs" or "compare"
        elif intent == 'compare' and len(functions) >= 2:
            for tool_name in self.tools.keys():
                tool_lower = tool_name.lower()
                # Check if tool contains both functions
                if all(func.lower() in tool_lower for func in functions):
                    return tool_name
        
        return None
    
    def execute_tool(self, tool_name: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute an existing tool.
        
        This is better than creating new queries because:
        - Faster (no query construction)
        - More reliable (proven code)
        - Consistent output
        """
        tool_info = self.tools.get(tool_name)
        if not tool_info:
            return {
                'status': 'error',
                'message': f'Tool not found: {tool_name}'
            }
        
        print(f"   ✅ Using existing tool: {tool_name}")
        
        try:
            result = subprocess.run(
                ['python3', str(tool_info.path)],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.workspace_path
            )
            
            return {
                'status': 'success',
                'output': result.stdout,
                'error': result.stderr if result.returncode != 0 else None,
                'tool_used': tool_name,
                'tool_description': tool_info.description
            }
            
        except subprocess.TimeoutExpired:
            return {
                'status': 'error',
                'message': f'Tool {tool_name} timed out after 30 seconds'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error executing {tool_name}: {str(e)}'
            }
    
    def get_tool_description(self, tool_name: str) -> str:
        """Get human-readable description of tool"""
        tool_info = self.tools.get(tool_name)
        if tool_info:
            return tool_info.description
        return "Unknown tool"
    
    def list_tools(self) -> List[str]:
        """List all available tools"""
        return list(self.tools.keys())
    
    def get_tools_for_function(self, function: str) -> List[str]:
        """Get all tools that work with a specific function"""
        function_lower = function.lower()
        matching_tools = []
        
        for tool_name, tool_info in self.tools.items():
            if function_lower in tool_name.lower():
                matching_tools.append(tool_name)
        
        return matching_tools


if __name__ == "__main__":
    # Test the tool inventory
    print("="*70)
    print("TOOL INVENTORY TEST")
    print("="*70)
    
    inventory = ToolInventory()
    
    print(f"\n📊 Total tools found: {len(inventory.tools)}")
    
    # Test matching
    test_queries = [
        ("engineering salaries", {'functions': ['Engineering'], 'intent': 'query'}),
        ("compare engineering and sales", {'functions': ['Engineering', 'Sales'], 'intent': 'compare'}),
        ("finance charts", {'functions': ['Finance'], 'intent': 'visualize'}),
    ]
    
    print("\n🔍 Testing query matching:")
    for question, entities in test_queries:
        match = inventory.match_query_to_tool(question, entities)
        print(f"\nQ: {question}")
        print(f"   Entities: {entities}")
        print(f"   Match: {match if match else 'No match - would create new query'}")
        
        if match:
            desc = inventory.get_tool_description(match)
            print(f"   Description: {desc}")
