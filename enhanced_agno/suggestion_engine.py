#!/usr/bin/env python3
"""
Suggestion Engine - Generates proactive suggestions for next analyses
"""

from typing import Dict, List, Any, Optional
import pandas as pd


class SuggestionEngine:
    """
    Generates context-aware suggestions for follow-up analyses.
    
    Makes the agent more helpful by proactively suggesting related queries.
    """
    
    def __init__(self):
        self.suggestion_templates = self._load_templates()
    
    def generate_suggestions(self, question: str, results: Dict[str, Any], 
                           query_type: str, conversation_history: List[Dict] = None) -> List[str]:
        """
        Generate 2-3 relevant suggestions based on current query.
        
        Args:
            question: The user's question
            results: Query results
            query_type: Type of query (salary, comparison, progression)
            conversation_history: Previous queries
            
        Returns:
            List of suggestion strings
        """
        suggestions = []
        
        # Generate suggestions based on query type
        if query_type == 'salary' or query_type == 'query':
            suggestions.extend(self._salary_suggestions(question, results))
        elif query_type == 'compare' or query_type == 'comparison':
            suggestions.extend(self._comparison_suggestions(question, results))
        elif query_type == 'progression':
            suggestions.extend(self._progression_suggestions(question, results))
        
        # Add context-aware suggestions from history
        if conversation_history:
            suggestions.extend(self._history_based_suggestions(conversation_history, results))
        
        # Limit to top 3 suggestions
        return suggestions[:3]
    
    def _salary_suggestions(self, question: str, results: Dict[str, Any]) -> List[str]:
        """Generate suggestions for salary queries"""
        suggestions = []
        
        records = results.get('data', [])
        if not records:
            return suggestions
        
        df = pd.DataFrame(records)
        
        # Suggest comparison if single function
        if 'job_function' in df.columns:
            functions = df['job_function'].unique()
            if len(functions) == 1:
                function = functions[0]
                
                # Suggest comparing with similar functions
                similar_functions = self._get_similar_functions(function)
                if similar_functions:
                    suggestions.append(
                        f"Compare {function} with {similar_functions[0]} salaries"
                    )
        
        # Suggest progression if multiple levels
        if 'job_level' in df.columns and len(df['job_level'].unique()) > 2:
            if 'job_function' in df.columns:
                function = df['job_function'].iloc[0]
                suggestions.append(
                    f"Show career progression path in {function}"
                )
        
        # Suggest specialization analysis
        if 'job_function' in df.columns:
            function = df['job_function'].iloc[0]
            suggestions.append(
                f"Analyze top specializations within {function}"
            )
        
        # Suggest visualization if not already created
        if 'chart_path' not in results:
            suggestions.append(
                "Create a visualization of this data"
            )
        
        return suggestions
    
    def _comparison_suggestions(self, question: str, results: Dict[str, Any]) -> List[str]:
        """Generate suggestions for comparison queries"""
        suggestions = []
        
        records = results.get('data', [])
        if not records:
            return suggestions
        
        df = pd.DataFrame(records)
        
        # Suggest level-specific comparison
        if 'job_function' in df.columns and 'job_level' in df.columns:
            functions = df['job_function'].unique()
            levels = df['job_level'].unique()
            
            if len(functions) >= 2 and len(levels) > 1:
                # Pick a common level
                level = levels[0]
                suggestions.append(
                    f"Compare {functions[0]} vs {functions[1]} at {level} level specifically"
                )
        
        # Suggest adding a third function
        if 'job_function' in df.columns:
            functions = df['job_function'].unique()
            if len(functions) == 2:
                other_functions = self._get_other_functions(functions)
                if other_functions:
                    suggestions.append(
                        f"Add {other_functions[0]} to the comparison"
                    )
        
        # Suggest progression comparison
        if 'job_function' in df.columns:
            functions = df['job_function'].unique()
            if len(functions) >= 2:
                suggestions.append(
                    f"Compare career progression between {functions[0]} and {functions[1]}"
                )
        
        # Suggest variable pay analysis
        suggestions.append(
            "Analyze variable pay differences between these functions"
        )
        
        return suggestions
    
    def _progression_suggestions(self, question: str, results: Dict[str, Any]) -> List[str]:
        """Generate suggestions for progression queries"""
        suggestions = []
        
        records = results.get('data', [])
        if not records:
            return suggestions
        
        df = pd.DataFrame(records)
        
        # Suggest comparing with another function's progression
        if 'job_function' in df.columns:
            function = df['job_function'].iloc[0]
            similar_functions = self._get_similar_functions(function)
            if similar_functions:
                suggestions.append(
                    f"Compare this progression with {similar_functions[0]}"
                )
        
        # Suggest focusing on specific level
        if 'job_level' in df.columns and 'avg_salary' in df.columns:
            # Find level with biggest jump
            if len(df) > 1:
                df_sorted = df.sort_values('avg_salary')
                salaries = df_sorted['avg_salary'].values
                max_jump_idx = 0
                max_jump = 0
                
                for i in range(1, len(salaries)):
                    jump = salaries[i] - salaries[i-1]
                    if jump > max_jump:
                        max_jump = jump
                        max_jump_idx = i
                
                if max_jump_idx > 0:
                    level = df_sorted.iloc[max_jump_idx]['job_level']
                    suggestions.append(
                        f"Analyze {level} in detail - shows largest salary jump"
                    )
        
        # Suggest time-to-promotion analysis
        if 'job_function' in df.columns:
            function = df['job_function'].iloc[0]
            suggestions.append(
                f"Analyze typical time-to-promotion in {function}"
            )
        
        return suggestions
    
    def _history_based_suggestions(self, history: List[Dict], 
                                   current_results: Dict[str, Any]) -> List[str]:
        """Generate suggestions based on conversation history"""
        suggestions = []
        
        if not history or len(history) < 2:
            return suggestions
        
        # Look at previous queries
        prev_query = history[-1] if history else None
        
        if prev_query:
            prev_entities = prev_query.get('entities', {})
            prev_functions = prev_entities.get('functions', [])
            
            # Suggest expanding scope
            if prev_functions:
                suggestions.append(
                    f"Broaden analysis to include more functions beyond {', '.join(prev_functions)}"
                )
        
        return suggestions
    
    def _get_similar_functions(self, function: str) -> List[str]:
        """Get similar functions for comparison suggestions"""
        # Mapping of functions to similar ones
        similar_map = {
            'Engineering': ['Product Management', 'Data Science', 'IT'],
            'Finance': ['Accounting', 'Treasury', 'FP&A'],
            'Sales': ['Marketing', 'Business Development', 'Customer Success'],
            'HR': ['Recruiting', 'People Operations', 'Talent Management'],
            'Marketing': ['Sales', 'Product Marketing', 'Communications'],
            'Product Management': ['Engineering', 'Design', 'Strategy'],
            'Legal': ['Compliance', 'Risk Management', 'Contracts'],
            'Operations': ['Supply Chain', 'Logistics', 'Manufacturing']
        }
        
        return similar_map.get(function, ['Sales', 'Marketing'])
    
    def _get_other_functions(self, existing_functions: List[str]) -> List[str]:
        """Get functions not in the existing list"""
        all_functions = [
            'Engineering', 'Finance', 'Sales', 'Marketing', 
            'HR', 'Product Management', 'Legal', 'Operations'
        ]
        
        return [f for f in all_functions if f not in existing_functions]
    
    def _load_templates(self) -> Dict[str, List[str]]:
        """Load suggestion templates"""
        return {
            'compare': [
                "Compare {function} with {other_function}",
                "See how {function} compares at {level} level"
            ],
            'progression': [
                "Show career progression in {function}",
                "Analyze growth trajectory for {level}"
            ],
            'specialization': [
                "Explore specializations within {function}",
                "Compare different {function} roles"
            ],
            'visualization': [
                "Create a chart of this data",
                "Visualize the distribution"
            ]
        }
    
    def format_suggestions(self, suggestions: List[str]) -> str:
        """Format suggestions for display"""
        if not suggestions:
            return ""
        
        output = []
        output.append("\n💡 You might also want to:")
        for i, suggestion in enumerate(suggestions, 1):
            output.append(f"   {i}. {suggestion}")
        
        return "\n".join(output)


if __name__ == "__main__":
    # Test suggestion engine
    print("="*70)
    print("SUGGESTION ENGINE TEST")
    print("="*70)
    
    engine = SuggestionEngine()
    
    # Test salary query suggestions
    print("\n1. Salary Query Suggestions:")
    test_results = {
        'data': [
            {'job_function': 'Engineering', 'job_level': 'Entry (P1)', 'avg_salary': 105000},
            {'job_function': 'Engineering', 'job_level': 'Manager (M3)', 'avg_salary': 219000},
        ]
    }
    
    suggestions = engine.generate_suggestions(
        "What's the salary for Engineering?",
        test_results,
        'salary'
    )
    
    print(engine.format_suggestions(suggestions))
    
    # Test comparison suggestions
    print("\n2. Comparison Query Suggestions:")
    test_results = {
        'data': [
            {'job_function': 'Engineering', 'job_level': 'Manager (M3)', 'avg_salary': 219000},
            {'job_function': 'Sales', 'job_level': 'Manager (M3)', 'avg_salary': 178000},
        ]
    }
    
    suggestions = engine.generate_suggestions(
        "Compare Engineering and Sales",
        test_results,
        'comparison'
    )
    
    print(engine.format_suggestions(suggestions))
