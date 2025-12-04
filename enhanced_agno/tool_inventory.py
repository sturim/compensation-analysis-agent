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
    
    def matches(self, functions: List[str], intent: str, question: str = "", claude_client=None) -> bool:
        """
        Check if this tool matches the query using LLM for intelligent matching.
        Falls back to rule-based matching if LLM unavailable.
        
        Args:
            functions: Extracted function names
            intent: Query intent (compare, query, visualize, etc.)
            question: Original user question for context
            claude_client: Optional Claude client for LLM matching
            
        Returns:
            True if tool matches the query
        """
        # Use LLM matching if available
        if claude_client and question:
            return self._llm_matches(functions, intent, question, claude_client)
        
        # Fallback to rule-based matching
        return self._rule_based_matches(functions, intent)
    
    def _llm_matches(self, functions: List[str], intent: str, question: str, claude_client) -> bool:
        """Use LLM to intelligently match tool to query"""
        try:
            prompt = f"""You are a tool matching assistant. Determine if a tool matches a user's query.

User Question: "{question}"
Extracted Intent: {intent}
Extracted Functions: {functions}

Available Tool:
- Name: {self.name}
- Description: {self.description}
- Capabilities: {self.capabilities}

CRITICAL Matching Rules:
1. Report generation tools (pay_transparency, pay_range, job_architecture) work with ANY function
   - If query asks for "pay transparency report for Sales", match generate_pay_transparency_report
   - If query asks for "pay range report for Engineering", match generate_pay_range_report
   - These tools accept function names as parameters - they are NOT function-specific
   
2. Match based on REPORT TYPE, not function name:
   - "pay transparency" or "range width" → generate_pay_transparency_report
   - "pay range" or "market data" → generate_pay_range_report
   - "job architecture" or "career ladder" → generate_job_architecture_report
   - "salary overview" (general) → salary overview tools
   
3. Comparison tools (with "compare", "vs") ONLY match comparison queries with 2+ functions

4. The function name (Engineering, Sales, Finance, etc.) is a PARAMETER, not a requirement
   - generate_pay_transparency_report works for ANY function
   - generate_pay_range_report works for ANY function
   - generate_job_architecture_report works for ANY function

Should this tool be used for this query?
Respond with ONLY "YES" or "NO" followed by a brief reason.

Example responses:
YES - Tool generates pay transparency reports for any function, query asks for pay transparency for Sales
YES - Tool generates pay range reports for any function, query asks for pay range for Engineering
NO - Tool is for salary overview but query specifically asks for pay transparency report
NO - Tool is for market data but query asks for transparency report"""

            response = claude_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=100,
                messages=[{"role": "user", "content": prompt}]
            )
            
            answer = response.content[0].text.strip()
            # Debug output
            # print(f"   🤖 LLM Tool Match for '{self.name}': {answer}")
            return answer.upper().startswith("YES")
            
        except Exception as e:
            # Fallback to rule-based on error
            return self._rule_based_matches(functions, intent)
    
    def _rule_based_matches(self, functions: List[str], intent: str) -> bool:
        """Fallback rule-based matching"""
        name_lower = self.name.lower()
        
        # For comparison tools, require compare intent and multiple functions
        if 'compare' in name_lower or '_vs_' in name_lower or ' vs ' in name_lower:
            # This is a comparison tool - only match for comparison queries
            if intent != 'compare' or len(functions) < 2:
                return False
            # Check if all functions are in the tool name
            return all(func.lower() in name_lower for func in functions)
        
        # For single-function queries, ensure tool doesn't contain other function names
        if len(functions) == 1:
            func = functions[0].lower()
            if func not in name_lower:
                return False
            
            # Make sure tool doesn't contain other function names (indicating it's a comparison)
            # Check for common abbreviations too
            function_patterns = {
                'engineering': ['engineering', 'eng'],
                'finance': ['finance', 'fin'],
                'sales': ['sales'],
                'marketing': ['marketing', 'mkt'],
                'hr': ['hr', 'human'],
            }
            
            # Get patterns for current function
            current_patterns = []
            for key, patterns in function_patterns.items():
                if func in patterns or key == func:
                    current_patterns = patterns
                    break
            
            # Check if tool contains other function names
            for key, patterns in function_patterns.items():
                # Skip current function
                if func in patterns or key == func:
                    continue
                # Check if any pattern for other functions is in tool name
                for pattern in patterns:
                    if pattern in name_lower:
                        return False
            
            # Match intent
            if intent in ['query', 'analyze'] and ('analysis' in name_lower or 'salary' in name_lower):
                return True
            if intent in ['visualize', 'show', 'display'] and ('chart' in name_lower or 'viz' in name_lower):
                return True
            # For general queries, match if tool name contains the function
            if intent == 'query':
                return True
        
        return False


class ToolInventory:
    """
    Discovers and manages available workspace tools.
    
    Key principle: Use existing tools before creating new code.
    This is how Kiro works - check what exists first!
    """
    
    def __init__(self, workspace_path: str = ".", claude_client=None):
        self.workspace_path = Path(workspace_path)
        self.tools: Dict[str, ToolInfo] = {}
        self.claude_client = claude_client
        self.scan_workspace()
    
    def scan_workspace(self):
        """Scan workspace for existing analysis scripts"""
        print("🔍 Scanning workspace for existing tools...")
        
        # Find analysis scripts
        patterns = [
            "*_analysis.py",
            "*_chart.py",
            "*_salary*.py",
            "*_report.py",
            "compare_*.py",
            "generate_*.py",
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
        
        # First, try exact keyword matching for report types
        question_lower = question.lower()
        
        # Check for specific report type keywords
        if 'transparency' in question_lower or 'range width' in question_lower:
            if 'generate_pay_transparency_report' in self.tools:
                return 'generate_pay_transparency_report'
        
        if ('pay range' in question_lower or 'market data' in question_lower) and 'transparency' not in question_lower:
            if 'generate_pay_range_report' in self.tools:
                return 'generate_pay_range_report'
        
        if 'architecture' in question_lower or 'career ladder' in question_lower:
            if 'generate_job_architecture_report' in self.tools:
                return 'generate_job_architecture_report'
        
        # Fall back to LLM matching for other cases
        for tool_name, tool_info in self.tools.items():
            if tool_info.matches(functions, intent, question, self.claude_client):
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
