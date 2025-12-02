#!/usr/bin/env python3
"""
Enhanced Agno Agent MVP
Demonstrates key improvements: fast parsing, LLM planning, auto-visualization
"""

import os
import sys
import sqlite3
import pandas as pd
from typing import Dict, Any, Optional, List

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
from result_validator import ResultValidator
from query_logger import QueryLogger

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
    
    def __init__(self, debug: bool = False):
        self.db_path = 'compensation_data.db'
        self.debug = debug  # Debug flag for verbose output
        
        # Initialize Claude first (needed for LLM-guided visualization)
        self.claude_client = None
        if CLAUDE_AVAILABLE:
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if api_key and api_key != 'your-claude-api-key-here':
                try:
                    self.claude_client = anthropic.Anthropic(api_key=api_key)
                    print("✅ Claude AI initialized")
                except Exception as e:
                    print(f"⚠️  Claude initialization failed: {e}")
        
        # Initialize core components
        self.entity_parser = EntityParser()
        self.conversation = ConversationManager()
        self.viz_engine = VisualizationEngine(db_path=self.db_path, claude_client=self.claude_client)
        self.tool_inventory = ToolInventory()  # Discover existing tools
        self.analysis_engine = AnalysisEngine()  # Generate insights
        self.formatter = ResultFormatter()  # Format output beautifully
        
        # Initialize new components
        self.error_handler = ErrorHandler()  # Handle errors gracefully
        self.suggestion_engine = SuggestionEngine()  # Generate suggestions
        self.export_manager = ExportManager()  # Export results
        self.comparison_engine = ComparisonEngine()  # Advanced comparisons
        self.result_validator = ResultValidator()  # Validate query results
        self.query_logger = QueryLogger(enabled=debug, verbose=debug)  # Log queries
        
        # Initialize LLM orchestrator
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
        print(f"   Result Validator: ✅")
        print(f"   Query Logger: ✅")
        print(f"   Claude AI: {'✅' if self.claude_client else '⚠️  Fallback mode'}")

    def ask(self, question: str, session_id: str = None) -> str:
        """
        Process a question with enhanced capabilities.
        
        Args:
            question: User's question
            session_id: Optional session ID for context retention
        
        Flow:
        1. Fast entity extraction (no LLM)
        2. LLM creates execution plan
        3. Execute plan with tools
        4. LLM generates insightful response
        """
        print(f"\n🤖 Processing: {question}")
        
        # Set session if provided
        if session_id:
            self.conversation.set_session(session_id)
            print(f"   📋 Session: {session_id}")
        
        # Step 1: Fast entity extraction
        print("   [1/4] Extracting entities...")
        entities = self.entity_parser.extract(question)
        print(f"         Functions: {entities['functions']}")
        print(f"         Intent: {entities['intent']}")
        
        # Check for validation suggestions
        validation = entities.get('validation', {})
        if validation.get('has_suggestions'):
            suggestions = validation.get('suggestions', [])
            for suggestion in suggestions:
                original = suggestion['original']
                alternatives = suggestion['alternatives']
                
                # Format suggestion message
                alt_list = ', '.join(f"'{alt}'" for alt in alternatives)
                suggestion_msg = (
                    f"\n⚠️  Job function '{original}' not found in database.\n"
                    f"   Did you mean: {alt_list}?\n"
                    f"   Please confirm which one you'd like to use, or rephrase your query."
                )
                
                return suggestion_msg
        
        # Check for references (use session context if available)
        reference = self.conversation.resolve_reference(question, session_id)
        if reference:
            print(f"         Resolved reference: {reference['functions']}")
            if not entities['functions']:
                entities['functions'] = reference['functions']
        
        # Step 2: Handle comparison queries specially
        if entities['intent'] == 'compare' and len(entities['functions']) == 2:
            print("   [2/5] Detected comparison query...")
            print("   [3/5] Querying both functions...")
            
            # Query both functions
            func1, func2 = entities['functions']
            
            # Query first function
            entities_func1 = entities.copy()
            entities_func1['functions'] = [func1]
            data1 = self._query_database(entities_func1, {})
            
            # Query second function
            entities_func2 = entities.copy()
            entities_func2['functions'] = [func2]
            data2 = self._query_database(entities_func2, {})
            
            print("   [4/5] Creating comparison...")
            # Use comparison engine
            comparison = self.comparison_engine.compare_functions(data1, data2, func1, func2)
            
            # Create visualization
            chart_path = self._create_comparison_visualization(data1, data2, func1, func2)
            
            results = {
                'query_results': {
                    'data': data1.get('data', []) + data2.get('data', []),
                    'status': 'success',
                    'row_count': data1.get('row_count', 0) + data2.get('row_count', 0)
                },
                'comparison': comparison,
                'chart_path': chart_path,
                'function1_data': data1,
                'function2_data': data2
            }
            
            print("   [5/5] Generating response...")
        else:
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
            if 'query_type' in query_data:
                results['query_type'] = query_data['query_type']
            if 'module' in query_data:
                results['module'] = query_data['module']
            if 'summary' in query_data and isinstance(query_data['summary'], dict):
                results['summary'] = query_data['summary']
            if 'breakdown' in query_data:
                results['breakdown'] = query_data['breakdown']
        
        results = self.analysis_engine.analyze(results, intent)
        
        # Debug: Check what's in results
        # print(f"DEBUG: Results keys: {list(results.keys())}")
        # print(f"DEBUG: Has summary: {'summary' in results}")
        # print(f"DEBUG: Has insights: {'insights' in results}")
        
        # Generate response
        response = self.llm.generate_response(question, results)
        
        # Generate suggestions (use session history if available)
        history = (self.conversation.sessions[session_id]['history'] 
                  if session_id and session_id in self.conversation.sessions 
                  else self.conversation.history)
        suggestions = self.suggestion_engine.generate_suggestions(
            question, 
            results, 
            intent,
            history
        )
        
        # Add suggestions to response
        if suggestions:
            response += "\n" + self.suggestion_engine.format_suggestions(suggestions)
        
        # Format output beautifully
        formatted_output = self.formatter.format_response(question, results, response)
        
        # Save to conversation history (with session if provided)
        self.conversation.add_interaction(question, entities, results, response, session_id)
        
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
                # Check if this is a module query
                if entities.get('modules'):
                    data = self._query_by_module(entities, params)
                else:
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

    def _query_database(
        self, 
        entities: Dict[str, Any], 
        params: Dict[str, Any],
        limit: Optional[int] = None,
        include_rollups: bool = True,
        include_executives: bool = True
    ) -> Dict[str, Any]:
        """
        Query database for compensation data with error handling.
        
        Args:
            entities: Extracted entities from user query
            params: Additional query parameters
            limit: Maximum number of results (None for no limit)
            include_rollups: Whether to include Roll-Up job levels
            include_executives: Whether to include Executive job levels
            
        Returns:
            Dictionary with query results and metadata
        """
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            
            functions = entities.get('functions', [])
            levels = entities.get('levels', [])
            percentile = entities.get('percentile', 'p50')
            
            # Override with params if provided
            if 'function' in params:
                functions = [params['function']]
            if 'limit' in params:
                limit = params['limit']
            if 'include_rollups' in params:
                include_rollups = params['include_rollups']
            if 'include_executives' in params:
                include_executives = params['include_executives']
            
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
            order_by = "avg_salary ASC"
            
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
            
            # Build filter conditions for job levels
            level_filters = []
            if not include_rollups:
                level_filters.append("jp.job_level NOT LIKE '%Roll-Up%'")
            if not include_executives:
                level_filters.append("jp.job_level NOT LIKE '%Executive%'")
            
            # Combine all WHERE conditions
            all_conditions = [where_clause]
            all_conditions.append(f"{percentile_col} IS NOT NULL")
            all_conditions.append(f"{percentile_col} > 0")
            all_conditions.extend(level_filters)
            
            final_where_clause = " AND ".join(all_conditions)
            
            # Build LIMIT clause
            limit_clause = f"LIMIT {limit}" if limit is not None else ""
            
            query = f"""
            SELECT 
                jp.job_function,
                jp.job_level,
                ROUND(AVG({percentile_col}), 0) as avg_salary,
                SUM(cm.base_salary_lfy_emp_count) as employees,
                COUNT(DISTINCT jp.id) as positions
            FROM job_positions jp
            JOIN compensation_metrics cm ON jp.id = cm.job_position_id
            WHERE {final_where_clause}
            GROUP BY jp.job_function, jp.job_level
            ORDER BY {order_by}
            {limit_clause}
            """
            
            # Log query before execution
            self.query_logger.log_query(query, query_params)
            
            # Get total count without LIMIT for transparency
            count_query = f"""
            SELECT COUNT(*) as total_count
            FROM (
                SELECT jp.job_function, jp.job_level
                FROM job_positions jp
                JOIN compensation_metrics cm ON jp.id = cm.job_position_id
                WHERE {final_where_clause}
                GROUP BY jp.job_function, jp.job_level
            ) subquery
            """
            
            cursor = conn.cursor()
            cursor.execute(count_query, query_params)
            total_available = cursor.fetchone()[0]
            
            self.query_logger.log_result_count(total_available, 'total_available')
            
            # Debug output
            if self.debug:
                print("\n" + "="*70)
                print("🔍 DEBUG: SQL QUERY")
                print("="*70)
                print(query)
                print("\n📋 Query Parameters:", query_params)
                print(f"\n📊 Total available records: {total_available}")
                print(f"📊 Limit applied: {limit if limit else 'None'}")
                print("\n📊 Column Mappings:")
                print("  Report Column          → Database Column")
                print("  " + "-"*66)
                print("  job_function           → jp.job_function")
                print("  job_level              → jp.job_level")
                print(f"  avg_salary             → ROUND(AVG({percentile_col}), 0)")
                print("  employees              → SUM(cm.base_salary_lfy_emp_count)")
                print("  positions              → COUNT(DISTINCT jp.id)")
                print("\n📁 Tables:")
                print("  jp  = job_positions")
                print("  cm  = compensation_metrics")
                print("="*70 + "\n")
            
            df = pd.read_sql_query(query, conn, params=query_params)
            
            self.query_logger.log_result_count(len(df), 'query_result')
            conn.close()
            
            if self.debug:
                print(f"📊 Query returned {len(df)} rows (of {total_available} total)")
                if not df.empty:
                    print(f"📋 Columns: {list(df.columns)}")
                    print(f"📈 Sample row: {df.iloc[0].to_dict()}")
            
            if df.empty:
                # Get available job functions for suggestions
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT job_function FROM job_positions ORDER BY job_function LIMIT 10")
                available_functions = [row[0] for row in cursor.fetchall()]
                
                return {
                    'status': 'no_results',
                    'total_available': total_available,
                    'message': 'No results found for the specified criteria',
                    'suggestions': available_functions,
                    'help': 'Try one of the available job functions listed above'
                }
            
            # Check if results were limited
            is_limited = limit is not None and len(df) < total_available
            
            # Convert to dict for results
            result = {
                'status': 'success',
                'row_count': len(df),
                'total_available': total_available,
                'is_limited': is_limited,
                'avg_salary': int(df['avg_salary'].mean()) if not df.empty else 0,
                'total_employees': int(df['employees'].sum()) if not df.empty else 0,
                'data': df.to_dict('records')
            }
            
            # Validate results
            validation = self.result_validator.validate_query_result(
                result,
                expected_record_count=total_available if not is_limited else None
            )
            
            # Log validation results
            self.query_logger.log_validation(validation)
            
            # Add validation to result
            result['validation'] = {
                'is_complete': validation.is_complete,
                'discrepancies': validation.discrepancies,
                'warnings': validation.warnings
            }
            
            # Add warning if results are limited
            if is_limited:
                result['warning'] = f"Showing {len(df)} of {total_available} total records"
            
            # Add warnings for validation issues
            if validation.discrepancies:
                if 'warning' in result:
                    result['warning'] += f" | Validation issues: {', '.join(validation.discrepancies)}"
                else:
                    result['warning'] = f"Validation issues: {', '.join(validation.discrepancies)}"
            
            return result
            
        except Exception as e:
            # Log error
            self.query_logger.log_error(e, {
                'operation': 'database_query',
                'entities': entities,
                'params': params
            })
            
            # Use error handler for better error messages
            error_result = self.error_handler.handle_error(e, {
                'operation': 'database_query',
                'entities': entities,
                'params': params
            })
            
            # Print user-friendly message
            if 'user_message' in error_result:
                print(error_result['user_message'])
            
            # Return structured error response
            return {
                'status': 'error',
                'message': str(e),
                'error_type': type(e).__name__,
                'error_details': error_result,
                'help': 'Please check your query parameters and try again'
            }
    
    def _query_by_module(
        self,
        entities: Dict[str, Any],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Query database by job module with comprehensive breakdown.
        
        Args:
            entities: Extracted entities including modules
            params: Additional query parameters
            
        Returns:
            Dictionary with module query results and breakdown
        """
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            
            modules = entities.get('modules', [])
            percentile = entities.get('percentile', 'p50')
            percentile_col = f'cm.base_salary_lfy_{percentile}'
            
            if not modules:
                return {'status': 'error', 'message': 'No module specified'}
            
            module = modules[0]  # Use first module
            
            # Get summary statistics for the module
            summary_query = f"""
            SELECT 
                COUNT(DISTINCT jp.job_function) as unique_functions,
                COUNT(DISTINCT jp.job_level) as unique_levels,
                COUNT(DISTINCT jp.id) as total_positions,
                SUM(cm.base_salary_lfy_emp_count) as total_employees,
                ROUND(AVG({percentile_col}), 0) as avg_salary,
                ROUND(MIN({percentile_col}), 0) as min_salary,
                ROUND(MAX({percentile_col}), 0) as max_salary
            FROM job_positions jp
            JOIN compensation_metrics cm ON jp.id = cm.job_position_id
            WHERE jp.job_module = ?
                AND {percentile_col} IS NOT NULL
                AND {percentile_col} > 0
            """
            
            summary_df = pd.read_sql_query(summary_query, conn, params=[module])
            
            # Get breakdown by function
            breakdown_query = f"""
            SELECT 
                jp.job_function,
                COUNT(DISTINCT jp.job_level) as levels,
                COUNT(DISTINCT jp.id) as positions,
                SUM(cm.base_salary_lfy_emp_count) as employees,
                ROUND(AVG({percentile_col}), 0) as avg_salary,
                ROUND(MIN({percentile_col}), 0) as min_salary,
                ROUND(MAX({percentile_col}), 0) as max_salary
            FROM job_positions jp
            JOIN compensation_metrics cm ON jp.id = cm.job_position_id
            WHERE jp.job_module = ?
                AND {percentile_col} IS NOT NULL
                AND {percentile_col} > 0
            GROUP BY jp.job_function
            ORDER BY employees DESC
            """
            
            breakdown_df = pd.read_sql_query(breakdown_query, conn, params=[module])
            
            conn.close()
            
            if summary_df.empty or breakdown_df.empty:
                return {
                    'status': 'no_results',
                    'message': f'No data found for module: {module}'
                }
            
            # Format results
            summary = summary_df.iloc[0].to_dict()
            
            return {
                'status': 'success',
                'query_type': 'module',
                'module': module,
                'summary': summary,
                'breakdown': breakdown_df.to_dict('records'),
                'row_count': len(breakdown_df),
                'total_employees': int(summary['total_employees']),
                'avg_salary': int(summary['avg_salary'])
            }
            
        except Exception as e:
            self.query_logger.log_error(e, {
                'operation': 'module_query',
                'entities': entities,
                'params': params
            })
            
            return {
                'status': 'error',
                'message': str(e),
                'error_type': type(e).__name__,
                'help': 'Please check your module name and try again'
            }
    
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
    
    def _create_comparison_visualization(self, data1: Dict[str, Any], data2: Dict[str, Any], 
                                        func1: str, func2: str) -> Optional[str]:
        """Create comparison visualization for two functions"""
        try:
            chart_path = self.viz_engine.create_comparison_chart(func1, func2)
            if chart_path:
                print(f"         ✅ Chart saved: {chart_path}")
            return chart_path
        except Exception as e:
            print(f"         ⚠️  Visualization failed: {e}")
            return None
    
    def _create_visualization(self, results: Dict[str, Any], 
                             entities: Dict[str, Any], params: Dict[str, Any]) -> Optional[str]:
        """Create visualization from results"""
        query_results = results.get('query_results', {})
        
        if query_results.get('status') != 'success':
            return None
        
        functions = entities.get('functions', [])
        intent = entities.get('intent', 'query')
        
        # Route to comprehensive overview for single function
        if len(functions) == 1 and intent in ['query', 'visualize', 'progression']:
            job_function = functions[0]
            chart_path = self.viz_engine.create_salary_overview(job_function)
            if chart_path:
                return chart_path
        
        # Route to comparison for multiple functions
        elif len(functions) >= 2 and intent == 'compare':
            chart_path = self.viz_engine.create_comparison_chart(functions[0], functions[1])
            if chart_path:
                return chart_path
        
        # Fallback to basic visualization
        data = query_results.get('data', [])
        if not data:
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Determine chart type
        chart_type = params.get('type', 'distribution')
        
        if intent == 'compare' or chart_type == 'comparison':
            chart_type = 'comparison'
        elif intent == 'progression':
            chart_type = 'progression'
        
        # Create title
        title = f"{' vs '.join(functions)} Compensation"
        
        # Pass query and entities for LLM-guided visualization
        query = entities.get('original_question', '')
        
        return self.viz_engine.auto_visualize(df, chart_type, title, query=query, entities=entities)
    
    def create_session(self, session_id: str = None) -> str:
        """Create a new session and return its ID"""
        return self.conversation.create_session(session_id)
    
    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for a specific session"""
        return self.conversation.get_session_history(session_id)
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all active sessions"""
        return self.conversation.list_sessions()
    
    def interactive_mode(self):
        """Run in interactive mode"""
        print("\n" + "="*70)
        print("🤖 ENHANCED AGNO AGENT - Interactive Mode (Full Feature Set)")
        if self.debug:
            print("🔍 DEBUG MODE ENABLED")
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
        if self.debug:
            print("  ✅ Debug mode (SQL queries & column mappings)")
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
                            # Handle Interaction objects (dataclass)
                            if hasattr(item, 'question'):
                                print(f"\n{i}. {item.question}")
                                print(f"   Functions: {item.entities.get('functions', [])}")
                                print(f"   Intent: {item.entities.get('intent', 'unknown')}")
                            else:
                                # Fallback for dict format
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
    parser.add_argument('-d', '--debug', action='store_true',
                       help='Enable debug mode (shows SQL queries and column mappings)')
    
    args = parser.parse_args()
    
    agent = EnhancedAgnoAgent(debug=args.debug)
    
    if args.interactive or not args.question:
        agent.interactive_mode()
    else:
        response = agent.ask(args.question)
        print("\n" + response)


if __name__ == "__main__":
    main()
