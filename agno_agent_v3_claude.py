#!/usr/bin/env python3
"""
Agno Agent V3 - Enhanced with Claude AI Integration
Combines code generation capabilities with natural language understanding
"""

import os
import sys
import sqlite3
import subprocess
import json
from typing import Dict, List, Optional, Any
from functools import wraps

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Try to import Claude
try:
    import anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False

# Try to load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def tool(func):
    """Decorator to mark functions as agent tools"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    
    wrapper._is_tool = True
    wrapper._tool_name = func.__name__
    wrapper._tool_description = func.__doc__ or f"Tool: {func.__name__}"
    
    return wrapper


class AgnoAgentV3:
    """
    Agno Agent V3 - The Ultimate HR Compensation Agent
    Features:
    - Natural language understanding via Claude AI
    - Dynamic code generation for complex analyses
    - Direct database queries for simple questions
    - Intelligent query parsing and execution
    """
    
    def __init__(self):
        """Initialize the agent"""
        self.db_path = os.path.join(os.path.dirname(__file__), 'compensation_data.db')
        self.generated_scripts_dir = os.path.join(os.path.dirname(__file__), 'generated_scripts')
        self.claude_client = None
        
        # Create directory for generated scripts
        os.makedirs(self.generated_scripts_dir, exist_ok=True)
        
        # Initialize Claude if available
        if CLAUDE_AVAILABLE:
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if api_key and api_key != 'your-claude-api-key-here':
                try:
                    self.claude_client = anthropic.Anthropic(api_key=api_key)
                    print("✅ Claude AI initialized")
                except Exception as e:
                    print(f"⚠️  Claude initialization failed: {e}")
        
        self.tools = self._create_tools()
        self.agent_info = {
            "name": "Agno Agent V3",
            "version": "3.0",
            "capabilities": [
                "Natural language understanding (Claude AI)",
                "Direct database queries",
                "Dynamic code generation",
                "Custom analysis scripts",
                "Intelligent query parsing"
            ]
        }
    
    def _create_tools(self):
        """Create the agent tools"""
        
        @tool
        def parse_question_with_ai(question: str) -> Dict[str, Any]:
            """
            Use Claude AI to intelligently parse compensation questions.
            Falls back to keyword matching if Claude is unavailable.
            """
            if not self.claude_client:
                return self._parse_question_simple(question)
            
            try:
                prompt = f"""You are a compensation data query parser. Extract structured information from this question:

Question: "{question}"

Extract and return ONLY a JSON object with these fields:
- job_function: (e.g., "Finance", "Engineering", "Human Resources", "Corporate & Business Services")
- job_level: (e.g., "Manager (M3)", "Sr Manager (M4)", "Director (M5)", "Entry (P1)", "Career (P3)")
- job_focus: (e.g., "Payroll", "Billing Operations", "Applications Development Engineering", "Software")
- percentile: (e.g., "p10", "p25", "p50", "p75", "p90")
- query_type: (e.g., "salary", "compare", "range", "employee_count", "progression", "generate_script")
- analysis_type: (e.g., "salary_ranges", "comparison", "progression") - only if generating script
- spread: (integer, default 20) - only for salary ranges

Rules:
- Use null for any field you cannot determine
- Match standard job level codes (M3, M4, M5, P1, P2, P3, P4, etc.)
- For percentiles: 10th=p10, 25th=p25, 50th/median=p50, 75th=p75, 90th=p90
- query_type "generate_script" if question asks to "create", "generate", "build" something
- Return ONLY valid JSON, no explanation"""

                message = self.claude_client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=500,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                response_text = message.content[0].text.strip()
                
                # Extract JSON from response
                if '```json' in response_text:
                    response_text = response_text.split('```json')[1].split('```')[0].strip()
                elif '```' in response_text:
                    response_text = response_text.split('```')[1].split('```')[0].strip()
                
                parsed = json.loads(response_text)
                parsed['original_question'] = question
                parsed['parsed_by'] = 'claude'
                
                return parsed
                
            except Exception as e:
                print(f"⚠️  Claude parsing failed: {e}, using keyword matching")
                return self._parse_question_simple(question)
        
        @tool
        def execute_database_query(parsed: Dict[str, Any]) -> Dict[str, Any]:
            """
            Execute a database query based on parsed question parameters.
            """
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Build WHERE clause
                where_conditions = []
                params = []
                
                if parsed.get('job_function'):
                    where_conditions.append("jp.job_function = ?")
                    params.append(parsed['job_function'])
                
                if parsed.get('job_level'):
                    where_conditions.append("jp.job_level = ?")
                    params.append(parsed['job_level'])
                
                if parsed.get('job_focus'):
                    where_conditions.append("(jp.job_focus LIKE ? OR jp.job_title LIKE ?)")
                    params.append(f"%{parsed['job_focus']}%")
                    params.append(f"%{parsed['job_focus']}%")
                
                where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
                
                # Determine percentile column
                percentile_col = 'cm.base_salary_cfy_p50'
                if parsed.get('percentile') == 'p10':
                    percentile_col = 'cm.base_salary_cfy_p10'
                elif parsed.get('percentile') == 'p25':
                    percentile_col = 'cm.base_salary_cfy_p25'
                elif parsed.get('percentile') == 'p75':
                    percentile_col = 'cm.base_salary_cfy_p75'
                elif parsed.get('percentile') == 'p90':
                    percentile_col = 'cm.base_salary_cfy_p90'
                
                query = f'''
                SELECT 
                    jp.job_title,
                    jp.job_function,
                    jp.job_level,
                    jp.job_focus,
                    cm.base_salary_cfy_p10,
                    cm.base_salary_cfy_p25,
                    cm.base_salary_cfy_p50,
                    cm.base_salary_cfy_p75,
                    cm.base_salary_cfy_p90,
                    cm.total_comp_p50,
                    cm.base_salary_cfy_emp_count,
                    cm.base_salary_cfy_company_count
                FROM job_positions jp
                JOIN compensation_metrics cm ON jp.id = cm.job_position_id
                WHERE {where_clause}
                    AND {percentile_col} IS NOT NULL
                    AND {percentile_col} > 0
                ORDER BY {percentile_col} DESC
                LIMIT 10
                '''
                
                cursor.execute(query, params)
                results = cursor.fetchall()
                conn.close()
                
                return {
                    'status': 'success',
                    'results': results,
                    'parsed': parsed,
                    'row_count': len(results)
                }
                
            except Exception as e:
                return {
                    'status': 'error',
                    'message': str(e),
                    'parsed': parsed
                }
        
        @tool
        def generate_analysis_script(parsed: Dict[str, Any]) -> Dict[str, Any]:
            """
            Generate a custom Python script for complex analyses.
            """
            try:
                analysis_type = parsed.get('analysis_type', 'salary_ranges')
                job_function = parsed.get('job_function', 'Corporate & Business Services')
                
                if analysis_type == 'salary_ranges':
                    spread = parsed.get('spread', 20)
                    script_content = self._generate_salary_range_script(job_function, spread)
                    script_name = f"salary_ranges_{job_function.replace(' ', '_').lower()}.py"
                
                elif analysis_type == 'comparison':
                    function1 = parsed.get('function1', job_function)
                    function2 = parsed.get('function2', 'Finance')
                    level = parsed.get('job_level', 'All')
                    script_content = self._generate_comparison_script(function1, function2, level)
                    script_name = f"comparison_{function1}_{function2}.py"
                
                elif analysis_type == 'progression':
                    script_content = self._generate_progression_script(job_function)
                    script_name = f"progression_{job_function.replace(' ', '_').lower()}.py"
                
                else:
                    return {
                        "status": "error",
                        "message": f"Unknown analysis type: {analysis_type}"
                    }
                
                # Save and execute script
                script_path = os.path.join(self.generated_scripts_dir, script_name)
                with open(script_path, 'w') as f:
                    f.write(script_content)
                
                os.chmod(script_path, 0o755)
                
                result = subprocess.run(
                    ['python3', script_path],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                return {
                    "status": "success",
                    "script_path": script_path,
                    "script_name": script_name,
                    "execution_output": result.stdout,
                    "execution_error": result.stderr if result.returncode != 0 else None,
                    "return_code": result.returncode
                }
                
            except Exception as e:
                return {
                    "status": "error",
                    "message": str(e)
                }
        
        return [parse_question_with_ai, execute_database_query, generate_analysis_script]
    
    def _parse_question_simple(self, question: str) -> Dict[str, Any]:
        """Fallback keyword-based parsing"""
        question_lower = question.lower()
        
        # Extract job function
        function = None
        if 'finance' in question_lower:
            function = 'Finance'
        elif 'engineering' in question_lower or 'engineer' in question_lower:
            function = 'Engineering'
        elif 'hr' in question_lower or 'human resources' in question_lower:
            function = 'Human Resources'
        elif 'business' in question_lower:
            function = 'Corporate & Business Services'
        
        # Extract job level
        level = None
        if 'm3' in question_lower or 'manager' in question_lower:
            level = 'Manager (M3)'
        elif 'm4' in question_lower:
            level = 'Sr Manager (M4)'
        elif 'm5' in question_lower or 'director' in question_lower:
            level = 'Director (M5)'
        
        # Extract focus
        focus = None
        if 'payroll' in question_lower:
            focus = 'Payroll'
        elif 'billing' in question_lower:
            focus = 'Billing Operations'
        elif 'application development' in question_lower or 'app development' in question_lower:
            focus = 'Applications Development Engineering'
        
        # Extract percentile
        percentile = None
        if '10th' in question_lower:
            percentile = 'p10'
        elif '25th' in question_lower:
            percentile = 'p25'
        elif '50th' in question_lower or 'median' in question_lower:
            percentile = 'p50'
        elif '75th' in question_lower:
            percentile = 'p75'
        elif '90th' in question_lower:
            percentile = 'p90'
        
        # Determine query type
        query_type = 'salary'
        if any(word in question_lower for word in ['create', 'generate', 'build', 'all levels', 'compare', 'progression', 'career path']):
            query_type = 'generate_script'
            
            # Determine analysis type
            if 'compare' in question_lower or 'comparison' in question_lower:
                analysis_type = 'comparison'
            elif 'progression' in question_lower or 'career' in question_lower:
                analysis_type = 'progression'
            else:
                analysis_type = 'salary_ranges'
        else:
            analysis_type = None
        
        result = {
            'job_function': function,
            'job_level': level,
            'job_focus': focus,
            'percentile': percentile,
            'query_type': query_type,
            'original_question': question,
            'parsed_by': 'keyword'
        }
        
        if analysis_type:
            result['analysis_type'] = analysis_type
            
            # For comparisons, try to extract both functions
            if analysis_type == 'comparison':
                functions = []
                for func in ['Engineering', 'Finance', 'Human Resources', 'Corporate & Business Services']:
                    if func.lower() in question_lower:
                        functions.append(func)
                
                if len(functions) >= 2:
                    result['function1'] = functions[0]
                    result['function2'] = functions[1]
                elif len(functions) == 1:
                    result['function1'] = functions[0]
                    result['function2'] = 'Finance'  # default comparison
        
        return result
    
    def _generate_salary_range_script(self, job_function: str, spread: int) -> str:
        """Generate a salary range analysis script"""
        return f'''#!/usr/bin/env python3
"""
Auto-generated: Salary Range Analysis
Function: {job_function}
Spread: {spread}%
Generated by: Agno Agent V3
"""

import sqlite3
import os

def analyze_salary_ranges():
    db_path = os.path.join(os.path.dirname(__file__), '..', 'compensation_data.db')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    query = """
    SELECT 
        jp.job_level,
        AVG(cm.total_comp_p50) as midpoint,
        COUNT(*) as position_count
    FROM job_positions jp
    JOIN compensation_metrics cm ON jp.id = cm.job_position_id
    WHERE jp.job_function = ?
        AND cm.total_comp_p50 IS NOT NULL
        AND cm.total_comp_p50 > 0
    GROUP BY jp.job_level
    ORDER BY midpoint ASC
    """
    
    cursor.execute(query, ["{job_function}"])
    results = cursor.fetchall()
    conn.close()
    
    print("=" * 80)
    print(f"SALARY RANGES: {job_function}")
    print(f"Spread: {spread}% (±{spread/2}%)")
    print("=" * 80)
    print(f"{{'Level':<30}} | {{'Min':<12}} | {{'Midpoint':<12}} | {{'Max':<12}} | Count")
    print("-" * 80)
    
    for level, midpoint, count in results:
        range_min = midpoint * (1 - {spread}/200)
        range_max = midpoint * (1 + {spread}/200)
        print(f"{{level:<30}} | ${{range_min:>10,.0f}} | ${{midpoint:>10,.0f}} | ${{range_max:>10,.0f}} | {{count:>5}}")
    
    print("=" * 80)
    print(f"Total Levels: {{len(results)}}")

if __name__ == "__main__":
    analyze_salary_ranges()
'''
    
    def _generate_comparison_script(self, function1: str, function2: str, level: str) -> str:
        """Generate a function comparison script"""
        level_filter = f"AND jp.job_level = '{level}'" if level and level != 'All' else ""
        
        return f'''#!/usr/bin/env python3
"""
Auto-generated: Function Comparison
Comparing: {function1} vs {function2}
Level: {level}
Generated by: Agno Agent V3
"""

import sqlite3
import os

def compare_functions():
    db_path = os.path.join(os.path.dirname(__file__), '..', 'compensation_data.db')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    query = """
    SELECT 
        jp.job_function,
        COUNT(*) as position_count,
        AVG(cm.base_salary_lfy_p50) as avg_base_salary,
        AVG(cm.total_comp_p50) as avg_total_comp
    FROM job_positions jp
    JOIN compensation_metrics cm ON jp.id = cm.job_position_id
    WHERE jp.job_function IN (?, ?)
        {level_filter}
        AND cm.base_salary_lfy_p50 IS NOT NULL
        AND cm.base_salary_lfy_p50 > 0
    GROUP BY jp.job_function
    ORDER BY avg_base_salary DESC
    """
    
    cursor.execute(query, ["{function1}", "{function2}"])
    results = cursor.fetchall()
    conn.close()
    
    print("=" * 80)
    print(f"FUNCTION COMPARISON: {function1} vs {function2}")
    print(f"Level Filter: {level}")
    print("=" * 80)
    
    if len(results) == 2:
        func1_data = results[0]
        func2_data = results[1]
        
        print(f"\\n{{func1_data[0]}}:")
        print(f"  Positions: {{func1_data[1]}}")
        print(f"  Avg Base Salary: ${{func1_data[2]:,.0f}}")
        print(f"  Avg Total Comp: ${{func1_data[3]:,.0f}}")
        
        print(f"\\n{{func2_data[0]}}:")
        print(f"  Positions: {{func2_data[1]}}")
        print(f"  Avg Base Salary: ${{func2_data[2]:,.0f}}")
        print(f"  Avg Total Comp: ${{func2_data[3]:,.0f}}")
        
        diff = func1_data[2] - func2_data[2]
        pct = (diff / func2_data[2]) * 100
        
        print(f"\\n📊 COMPARISON:")
        print(f"  Salary Difference: ${{diff:,.0f}}")
        print(f"  Percentage: {{pct:.1f}}%")

if __name__ == "__main__":
    compare_functions()
'''
    
    def _generate_progression_script(self, job_function: str) -> str:
        """Generate a career progression analysis script"""
        return f'''#!/usr/bin/env python3
"""
Auto-generated: Career Progression Analysis
Function: {job_function}
Generated by: Agno Agent V3
"""

import sqlite3
import os

def analyze_progression():
    db_path = os.path.join(os.path.dirname(__file__), '..', 'compensation_data.db')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    levels = ['Entry (P1)', 'Developing (P2)', 'Career (P3)', 'Advanced (P4)', 
              'Expert (P5)', 'Manager (M3)', 'Sr Manager (M4)', 'Director (M5)']
    
    print("=" * 80)
    print(f"CAREER PROGRESSION: {job_function}")
    print("=" * 80)
    print(f"{{'Level':<20}} | {{'Avg Salary':<12}} | {{'Increase':<12}} | {{'% Increase':<10}}")
    print("-" * 80)
    
    prev_salary = None
    for level in levels:
        query = """
        SELECT AVG(cm.total_comp_p50)
        FROM job_positions jp
        JOIN compensation_metrics cm ON jp.id = cm.job_position_id
        WHERE jp.job_function = ?
            AND jp.job_level = ?
            AND cm.total_comp_p50 IS NOT NULL
            AND cm.total_comp_p50 > 0
        """
        
        cursor.execute(query, ["{job_function}", level])
        result = cursor.fetchone()
        
        if result and result[0]:
            salary = result[0]
            if prev_salary:
                increase = salary - prev_salary
                pct_increase = (increase / prev_salary) * 100
                print(f"{{level:<20}} | ${{salary:>10,.0f}} | ${{increase:>10,.0f}} | {{pct_increase:>9.1f}}%")
            else:
                print(f"{{level:<20}} | ${{salary:>10,.0f}} | {{'-':<12}} | {{'-':<10}}")
            prev_salary = salary
    
    conn.close()
    print("=" * 80)

if __name__ == "__main__":
    analyze_progression()
'''
    
    def display_results(self, result: Dict[str, Any]):
        """Display query results in a user-friendly format"""
        if result['status'] == 'error':
            print(f"\n❌ Error: {result['message']}")
            return
        
        results = result.get('results', [])
        parsed = result.get('parsed', {})
        
        if not results:
            print("\n❌ No results found")
            return
        
        print("\n✅ QUERY RESULTS")
        print("=" * 100)
        print(f"Question: {parsed.get('original_question', 'N/A')}")
        print(f"Parsed by: {parsed.get('parsed_by', 'unknown').upper()}")
        print(f"Found: {len(results)} position(s)")
        print("=" * 100)
        
        for i, row in enumerate(results, 1):
            title, function, level, focus, p10, p25, p50, p75, p90, total_comp, emp_count, company_count = row
            
            print(f"\n{i}. {title}")
            print(f"   Function: {function} | Level: {level}")
            if focus:
                print(f"   Focus: {focus}")
            
            if emp_count or company_count:
                print(f"\n   📊 Survey Data:")
                if emp_count:
                    print(f"     Employees: {emp_count}")
                if company_count:
                    print(f"     Companies: {company_count}")
            
            print(f"\n   Base Salary Percentiles:")
            if p10:
                print(f"     10th: ${p10:,.0f}")
            if p25:
                print(f"     25th: ${p25:,.0f}")
            if p50:
                print(f"     50th (Median): ${p50:,.0f}")
            if p75:
                print(f"     75th: ${p75:,.0f}")
            if p90:
                print(f"     90th: ${p90:,.0f}")
            
            if total_comp:
                print(f"\n   Total Compensation (Median): ${total_comp:,.0f}")
    
    def ask(self, question: str) -> Dict[str, Any]:
        """
        Ask the agent a question and get an intelligent response.
        
        Args:
            question: Natural language compensation question
        
        Returns:
            Answer dictionary with results
        """
        print(f"\n🤖 Processing: {question}")
        
        # Step 1: Parse the question
        parsed = self.tools[0](question)
        print(f"   Parsed by: {parsed.get('parsed_by', 'unknown').upper()}")
        
        # Step 2: Determine action based on query type
        query_type = parsed.get('query_type', 'salary')
        
        if query_type == 'generate_script':
            print("   Action: Generating custom analysis script...")
            result = self.tools[2](parsed)
            
            if result['status'] == 'success':
                print(f"   ✅ Script generated: {result['script_name']}")
                print("\n" + "=" * 80)
                print(result['execution_output'])
                print("=" * 80)
            else:
                print(f"   ❌ Script generation failed: {result['message']}")
            
            return result
        else:
            print("   Action: Executing database query...")
            result = self.tools[1](parsed)
            self.display_results(result)
            return result
    
    def interactive_mode(self):
        """Run agent in interactive mode"""
        print("=" * 70)
        print("🤖 AGNO AGENT V3 - Interactive Mode")
        print("=" * 70)
        
        if self.claude_client:
            print("✅ Claude AI is active - Natural language understanding enabled")
        else:
            print("⚠️  Claude AI not available - Using keyword matching")
            print("   Install with: pip install anthropic")
            print("   Set ANTHROPIC_API_KEY in .env file")
        
        print("\nCapabilities:")
        for cap in self.agent_info['capabilities']:
            print(f"  • {cap}")
        
        print("\nExample questions:")
        print("  • What's the salary for Finance Managers in payroll?")
        print("  • Create salary ranges for all Engineering levels")
        print("  • Compare Engineering and Finance at Director level")
        print("  • Show career progression in Human Resources")
        print("\nType 'exit' or 'quit' to end")
        print("=" * 70)
        
        while True:
            try:
                question = input("\n❓ Your question: ").strip()
                
                if question.lower() in ['exit', 'quit', 'q']:
                    print("\n👋 Goodbye!")
                    break
                
                if not question:
                    continue
                
                self.ask(question)
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Agno Agent V3 - AI-Powered HR Compensation Agent',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python3 agno_agent_v3_claude.py "What is the salary for Finance Managers?"
  python3 agno_agent_v3_claude.py "Create salary ranges for Engineering"
  python3 agno_agent_v3_claude.py --interactive
        '''
    )
    
    parser.add_argument('question', nargs='?', help='Your compensation question')
    parser.add_argument('-i', '--interactive', action='store_true', 
                       help='Run in interactive mode')
    
    args = parser.parse_args()
    
    agent = AgnoAgentV3()
    
    if args.interactive or not args.question:
        agent.interactive_mode()
    else:
        agent.ask(args.question)


if __name__ == "__main__":
    main()
