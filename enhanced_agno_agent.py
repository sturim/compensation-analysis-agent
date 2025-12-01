#!/usr/bin/env python3
"""
Enhanced Agno Agent MVP
Demonstrates key improvements: fast parsing, LLM planning, auto-visualization
"""

import os
import sys
import sqlite3
import pandas as pd
from typing import Dict, Any, Optional

# Add enhanced_agno to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'enhanced_agno'))

from entity_parser import EntityParser
from conversation_manager import ConversationManager
from visualization_engine import VisualizationEngine
from llm_orchestrator import LLMOrchestrator
from tool_inventory import ToolInventory
from analysis_engine import AnalysisEngine
from result_formatter import ResultFormatter
from error_handler import ErrorHandler, with_error_handling
from suggestion_engine import SuggestionEngine
from export_manager import ExportManager
from comparison_engine import ComparisonEngine

# Try to import Claude
try:
    import anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False
    print("⚠️  anthropic not installed. Run: pip install anthropic")

# Load environment
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class EnhancedAgnoAgent:
    """
    Enhanced Agno Agent - MVP Implementation
    
    Key improvements:
    - Fast entity extraction (no LLM)
    - LLM for planning and insights
    - Auto-visualization
    - Conversation context
    """
    
    def __init__(self):
        self.db_path = 'compensation_data.db'
        
        # Initialize core components
        self.entity_parser = EntityParser()
        self.conversation = ConversationManager()
        self.viz_engine = VisualizationEngine()
        self.tool_inventory = ToolInventory()  # Discover existing tools
        self.analysis_engine = AnalysisEngine()  # Generate insights
        self.formatter = ResultFormatter()  # Format output beautifully
        
        # Initialize new components
        self.error_handler = ErrorHandler()  # Handle errors gracefully
        self.suggestion_engine = SuggestionEngine()  # Generate suggestions
        self.export_manager = ExportManager()  # Export results
        self.comparison_engine = ComparisonEngine()  # Advanced comparisons
        
        # Initialize Claude if available
        self.claude_client = None
        if CLAUDE_AVAILABLE:
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if api_key and api_key != 'your-claude-api-key-here':
                try:
                    self.claude_client = anthropic.Anthropic(api_key=api_key)
                    print("✅ Claude AI initialized")
                except Exception as e:
                    print(f"⚠️  Claude initialization failed: {e}")
        
        self.llm = LLMOrchestrator(self.claude_client, self.conversation)
        
        print("🤖 Enhanced Agno Agent Ready (Full Feature Set)")
        print(f"   Entity Parser: ✅")
        print(f"   Tool Inventory: ✅ ({len(self.tool_inventory.tools)} tools)")
        print(f"   Analysis Engine: ✅")
        print(f"   Result Formatter: ✅")
        print(f"   Visualization: ✅")
        print(f"   Error Handler: ✅")
        print(f"   Suggestion Engine: ✅")
        print(f"   Export Manager: ✅")
        print(f"   Comparison Engine: ✅")
        print(f"   Claude AI: {'✅' if self.claude_client else '⚠️  Fallback mode'}")

    def ask(self, question: str) -> str:
        """
        Process a question with enhanced capabilities.
        
        Flow:
        1. Fast entity extraction (no LLM)
        2. LLM creates execution plan
        3. Execute plan with tools
        4. LLM generates insightful response
        """
        print(f"\n🤖 Processing: {question}")
        
        # Step 1: Fast entity extraction
        print("   [1/4] Extracting entities...")
        entities = self.entity_parser.extract(question)
        print(f"         Functions: {entities['functions']}")
        print(f"         Intent: {entities['intent']}")
        
        # Check for references
        reference = self.conversation.resolve_reference(question)
        if reference:
            print(f"         Resolved reference: {reference['functions']}")
            if not entities['functions']:
                entities['functions'] = reference['functions']
        
        # Step 2: Check for existing tools (NEW!)
        print("   [2/5] Checking for existing tools...")
        existing_tool = self.tool_inventory.match_query_to_tool(question, entities)
        
        if existing_tool:
            print(f"         ✅ Found existing tool: {existing_tool}")
            print("   [3/5] Executing existing tool...")
            results = self.tool_inventory.execute_tool(existing_tool)
            
            # Skip to response generation
            print("   [4/5] Skipping new query creation (using existing tool)")
            print("   [5/5] Generating response...")
        else:
            print("         No existing tool found, creating new query...")
            
            # Step 3: LLM creates plan
            print("   [3/5] Creating execution plan...")
            plan_result = self.llm.plan_execution(question, entities)
            plan = plan_result['plan']
            print(f"         Plan: {len(plan)} steps ({plan_result['source']})")
            
            # Step 4: Execute plan
            print("   [4/5] Executing plan...")
            results = self._execute_plan(plan, entities)
            
            print("   [5/5] Generating response...")
        
        # Enhance results with analysis
        intent = entities.get('intent', 'query')
        
        # Flatten query_results to top level for analysis engine
        if 'query_results' in results and isinstance(results['query_results'], dict):
            query_data = results['query_results']
            # Copy data fields to top level
            if 'data' in query_data:
                results['data'] = query_data['data']
            if 'status' in query_data:
                results['status'] = query_data['status']
            if 'row_count' in query_data:
                results['row_count'] = query_data['row_count']
            if 'total_employees' in query_data:
                results['total_employees'] = query_data['total_employees']
        
        results = self.analysis_engine.analyze(results, intent)
        
        # Debug: Check what's in results
        # print(f"DEBUG: Results keys: {list(results.keys())}")
        # print(f"DEBUG: Has summary: {'summary' in results}")
        # print(f"DEBUG: Has insights: {'insights' in results}")
        
        # Generate response
        response = self.llm.generate_response(question, results)
        
        # Generate suggestions
        suggestions = self.suggestion_engine.generate_suggestions(
            question, 
            results, 
            intent,
            self.conversation.history
        )
        
        # Add suggestions to response
        if suggestions:
            response += "\n" + self.suggestion_engine.format_suggestions(suggestions)
        
        # Format output beautifully
        formatted_output = self.formatter.format_response(question, results, response)
        
        # Save to conversation history
        self.conversation.add_interaction(question, entities, results, response)
        
        # Save for potential export
        self._last_results = results
        self._last_question = question
        self._last_response = response
        
        return formatted_output
    
    def _execute_plan(self, plan: list, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the plan using tools (no LLM)"""
        results = {}
        
        for i, step in enumerate(plan):
            tool = step.get('tool')
            params = step.get('params', {})
            
            if tool == 'query_database':
                data = self._query_database(entities, params)
                results[f'step_{i}_data'] = data
                results['query_results'] = data
                
            elif tool == 'create_comparison':
                # Use previous query results
                results['comparison'] = 'Comparison created'
                
            elif tool == 'visualize':
                chart_path = self._create_visualization(results, entities, params)
                if chart_path:
                    results['chart_path'] = chart_path
                    print(f"         ✅ Chart saved: {chart_path}")
                    
            elif tool == 'calculate_stats':
                if 'query_results' in results:
                    stats = self._calculate_stats(results['query_results'])
                    results.update(stats)
        
        return results

    def _query_database(self, entities: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """Query database for compensation data with error handling"""
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            
            functions = entities.get('functions', [])
            levels = entities.get('levels', [])
            percentile = entities.get('percentile', 'p50')
            
            # Override with params if provided
            if 'function' in params:
                functions = [params['function']]
            
            # Build query
            where_conditions = []
            query_params = []
            
            if functions:
                placeholders = ','.join(['?' for _ in functions])
                where_conditions.append(f"jp.job_function IN ({placeholders})")
                query_params.extend(functions)
            
            if levels:
                placeholders = ','.join(['?' for _ in levels])
                where_conditions.append(f"jp.job_level IN ({placeholders})")
                query_params.extend(levels)
            
            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
            
            percentile_col = f'cm.base_salary_lfy_{percentile}'
            
            # Build ORDER BY clause - prioritize standard career levels
            order_by = "avg_salary ASC"  # Changed from DESC to ASC to get entry-level first
            
            # If querying a single function, get standard career progression levels
            if len(functions) == 1:
                # Prefer standard P/M levels over roll-ups and executive levels
                order_by = """
                CASE 
                    WHEN jp.job_level LIKE 'Entry%' THEN 1
                    WHEN jp.job_level LIKE 'Developing%' THEN 2
                    WHEN jp.job_level LIKE 'Career%' THEN 3
                    WHEN jp.job_level LIKE 'Advanced%' THEN 4
                    WHEN jp.job_level LIKE 'Manager (M3)%' THEN 5
                    WHEN jp.job_level LIKE 'Expert%' THEN 6
                    WHEN jp.job_level LIKE 'Sr Manager%' THEN 7
                    WHEN jp.job_level LIKE 'Director%' THEN 8
                    WHEN jp.job_level LIKE 'Principal%' THEN 9
                    WHEN jp.job_level LIKE 'Senior Director%' THEN 10
                    ELSE 99
                END, avg_salary ASC
                """
            
            query = f"""
            SELECT 
                jp.job_function,
                jp.job_level,
                ROUND(AVG({percentile_col}), 0) as avg_salary,
                SUM(cm.base_salary_lfy_emp_count) as employees,
                COUNT(DISTINCT jp.id) as positions
            FROM job_positions jp
            JOIN compensation_metrics cm ON jp.id = cm.job_position_id
            WHERE {where_clause}
                AND {percentile_col} IS NOT NULL
                AND {percentile_col} > 0
                AND jp.job_level NOT LIKE '%Roll-Up%'
                AND jp.job_level NOT LIKE '%Executive%'
            GROUP BY jp.job_function, jp.job_level
            ORDER BY {order_by}
            LIMIT 10
            """
            
            df = pd.read_sql_query(query, conn, params=query_params)
            conn.close()
            
            if df.empty:
                return {'status': 'no_results'}
            
            # Convert to dict for results
            return {
                'status': 'success',
                'row_count': len(df),
                'avg_salary': int(df['avg_salary'].mean()) if not df.empty else 0,
                'total_employees': int(df['employees'].sum()) if not df.empty else 0,
                'data': df.to_dict('records')
            }
            
        except Exception as e:
            # Use error handler for better error messages
            error_result = self.error_handler.handle_error(e, {
                'operation': 'database_query',
                'entities': entities,
                'params': params
            })
            
            # Print user-friendly message
            if 'user_message' in error_result:
                print(error_result['user_message'])
            
            return {'status': 'error', 'message': str(e), 'error_details': error_result}
    
    def _calculate_stats(self, query_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate statistics from query results"""
        if query_results.get('status') != 'success':
            return {}
        
        data = query_results.get('data', [])
        if not data:
            return {}
        
        salaries = [d['avg_salary'] for d in data if 'avg_salary' in d]
        
        return {
            'min_salary': min(salaries) if salaries else 0,
            'max_salary': max(salaries) if salaries else 0,
            'median_salary': sorted(salaries)[len(salaries)//2] if salaries else 0,
        }
    
    def _create_visualization(self, results: Dict[str, Any], 
                             entities: Dict[str, Any], params: Dict[str, Any]) -> Optional[str]:
        """Create visualization from results"""
        query_results = results.get('query_results', {})
        
        if query_results.get('status') != 'success':
            return None
        
        data = query_results.get('data', [])
        if not data:
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Determine chart type
        intent = entities.get('intent', 'query')
        chart_type = params.get('type', 'distribution')
        
        if intent == 'compare' or chart_type == 'comparison':
            chart_type = 'comparison'
        elif intent == 'progression':
            chart_type = 'progression'
        
        # Create title
        functions = entities.get('functions', ['All'])
        title = f"{' vs '.join(functions)} Compensation"
        
        return self.viz_engine.auto_visualize(df, chart_type, title)
    
    def interactive_mode(self):
        """Run in interactive mode"""
        print("\n" + "="*70)
        print("🤖 ENHANCED AGNO AGENT - Interactive Mode (Full Feature Set)")
        print("="*70)
        print("\nEnhancements:")
        print("  ✅ Fast entity extraction (no LLM)")
        print("  ✅ Intelligent planning with context")
        print("  ✅ Auto-visualization")
        print("  ✅ Conversation memory")
        print("  ✅ Proactive suggestions")
        print("  ✅ Error handling with retry")
        print("  ✅ Export to CSV/JSON/Markdown")
        print("  ✅ Advanced comparisons")
        print("\nExample questions:")
        print("  • What's the salary for Finance Managers?")
        print("  • Compare engineering and sales")
        print("  • Show me career progression in HR")
        print("\nSpecial commands:")
        print("  • 'export' - Export last results")
        print("  • 'history' - Show conversation history")
        print("  • 'exit' - Quit")
        print("="*70)
        
        last_results = None
        last_question = None
        
        while True:
            try:
                question = input("\n❓ Your question: ").strip()
                
                if question.lower() in ['exit', 'quit', 'q']:
                    print("\n👋 Goodbye!")
                    break
                
                if not question:
                    continue
                
                # Handle special commands
                if question.lower() == 'export':
                    if last_results and last_question:
                        print("\n📤 Exporting last results...")
                        try:
                            exports = self.export_manager.export_all(
                                last_question,
                                last_results,
                                "See exported files for details"
                            )
                            print("\n✅ Exported to:")
                            for format_type, path in exports.items():
                                print(f"   • {format_type.upper()}: {path}")
                        except Exception as e:
                            print(f"\n❌ Export failed: {e}")
                    else:
                        print("\n⚠️  No results to export. Ask a question first.")
                    continue
                
                if question.lower() == 'history':
                    print("\n📜 Conversation History:")
                    if self.conversation.history:
                        for i, item in enumerate(self.conversation.history[-5:], 1):
                            print(f"\n{i}. {item.get('question', 'Unknown')}")
                            entities = item.get('entities', {})
                            print(f"   Functions: {entities.get('functions', [])}")
                            print(f"   Intent: {entities.get('intent', 'unknown')}")
                    else:
                        print("   No history yet")
                    continue
                
                # Process normal question
                response = self.ask(question)
                print("\n" + "="*70)
                print(response)
                print("="*70)
                
                # Save for export
                if hasattr(self, '_last_results'):
                    last_results = self._last_results
                    last_question = question
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                error_result = self.error_handler.handle_error(e, {
                    'operation': 'interactive_mode',
                    'question': question
                })
                if 'user_message' in error_result:
                    print(f"\n{error_result['user_message']}")
                else:
                    print(f"\n❌ Error: {e}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced Agno Agent MVP')
    parser.add_argument('question', nargs='?', help='Your question')
    parser.add_argument('-i', '--interactive', action='store_true', 
                       help='Interactive mode')
    
    args = parser.parse_args()
    
    agent = EnhancedAgnoAgent()
    
    if args.interactive or not args.question:
        agent.interactive_mode()
    else:
        response = agent.ask(args.question)
        print("\n" + response)


if __name__ == "__main__":
    main()
