#!/usr/bin/env python3
"""
Visualization Advisor - Uses LLM to intelligently choose best chart type
"""

import pandas as pd
from typing import Dict, Any, Optional, List
import json


class VisualizationAdvisor:
    """Uses LLM to recommend optimal visualization for data"""
    
    def __init__(self, claude_client=None):
        """
        Initialize visualization advisor.
        
        Args:
            claude_client: Anthropic Claude client for LLM decisions
        """
        self.claude = claude_client
    
    def recommend_visualization(self, data: pd.DataFrame, 
                               query: str, 
                               entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use LLM to recommend best visualization approach.
        
        Args:
            data: DataFrame with query results
            query: Original user query
            entities: Extracted entities (functions, intent, etc.)
            
        Returns:
            Dictionary with visualization recommendations:
            {
                'chart_type': 'comprehensive_overview' | 'comparison' | 'distribution' | 'progression',
                'reasoning': 'Why this chart type was chosen',
                'layout': 'single' | 'multi_panel',
                'features': ['percentile_bands', 'gradient_colors', 'employee_counts'],
                'title': 'Suggested chart title',
                'insights': ['Key insight 1', 'Key insight 2']
            }
        """
        if not self.claude:
            # Fallback to rule-based if no LLM
            return self._fallback_recommendation(data, entities)
        
        # Prepare data summary for LLM
        data_summary = self._summarize_data(data)
        
        # Create prompt for LLM
        prompt = self._create_recommendation_prompt(query, data_summary, entities)
        
        try:
            # Get LLM recommendation
            response = self.claude.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1000,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            # Parse LLM response
            recommendation = self._parse_llm_response(response.content[0].text)
            
            return recommendation
            
        except Exception as e:
            print(f"⚠️  LLM visualization recommendation failed: {e}")
            return self._fallback_recommendation(data, entities)
    
    def _summarize_data(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Create a concise summary of the data for LLM"""
        summary = {
            'row_count': len(data),
            'columns': list(data.columns),
            'column_types': {col: str(dtype) for col, dtype in data.dtypes.items()},
            'sample_rows': data.head(3).to_dict('records') if len(data) > 0 else [],
        }
        
        # Add statistical info
        if 'avg_salary' in data.columns or 'p50' in data.columns:
            salary_col = 'avg_salary' if 'avg_salary' in data.columns else 'p50'
            summary['salary_range'] = {
                'min': float(data[salary_col].min()),
                'max': float(data[salary_col].max()),
                'mean': float(data[salary_col].mean())
            }
        
        # Check for multiple functions
        if 'job_function' in data.columns:
            summary['functions'] = data['job_function'].unique().tolist()
            summary['function_count'] = len(summary['functions'])
        
        # Check for job levels
        if 'job_level' in data.columns:
            summary['level_count'] = data['job_level'].nunique()
            summary['levels'] = data['job_level'].unique().tolist()[:5]  # First 5
        
        # Check for percentile data
        percentile_cols = ['p10', 'p25', 'p50', 'p75', 'p90']
        summary['has_percentiles'] = all(col in data.columns for col in percentile_cols)
        
        # Check for employee counts
        summary['has_employee_counts'] = 'employees' in data.columns
        
        return summary
    
    def _create_recommendation_prompt(self, query: str, 
                                     data_summary: Dict[str, Any],
                                     entities: Dict[str, Any]) -> str:
        """Create prompt for LLM to recommend visualization"""
        
        prompt = f"""You are a data visualization expert. Analyze this compensation data query and recommend the BEST chart type for clear, insightful visualization.

USER QUERY: "{query}"

DATA SUMMARY:
- Rows: {data_summary['row_count']}
- Columns: {', '.join(data_summary['columns'])}
- Functions: {data_summary.get('function_count', 0)} ({', '.join(data_summary.get('functions', []))})
- Job Levels: {data_summary.get('level_count', 0)}
- Has Percentiles (P10-P90): {data_summary.get('has_percentiles', False)}
- Has Employee Counts: {data_summary.get('has_employee_counts', False)}
- Salary Range: ${data_summary.get('salary_range', {}).get('min', 0):,.0f} - ${data_summary.get('salary_range', {}).get('max', 0):,.0f}

EXTRACTED INTENT: {entities.get('intent', 'query')}

AVAILABLE CHART TYPES:
1. comprehensive_overview - 3-panel dashboard (distribution with percentile bands + career progression + employee distribution)
   - Best for: Single function, has percentiles, showing complete picture
   - Features: Percentile bands, gradient colors, employee counts
   
2. comparison - Side-by-side comparison chart
   - Best for: 2+ functions, comparing across levels
   - Features: Grouped bars, clear labels, difference highlighting
   
3. distribution - Single distribution chart with percentile bands
   - Best for: Single function, showing salary spread
   - Features: Area chart, percentile lines, median markers
   
4. progression - Career progression chart
   - Best for: Showing salary growth across levels
   - Features: Gradient colors, trend line, growth percentages
   
5. simple_bar - Basic bar chart
   - Best for: Small datasets, simple comparisons
   - Features: Clean bars, value labels

RESPOND IN JSON FORMAT:
{{
  "chart_type": "one of the above types",
  "reasoning": "2-3 sentences explaining why this is the best choice",
  "layout": "single or multi_panel",
  "features": ["list", "of", "recommended", "features"],
  "title": "Suggested chart title",
  "insights": ["Key insight 1", "Key insight 2"]
}}

Consider:
- Data complexity (more data = more sophisticated viz)
- User intent (compare = comparison chart, show = comprehensive)
- Available data (percentiles = use them!, employee counts = show them!)
- Readability (avoid cramming too much into one chart)
- Professional appearance (publication-quality)

Respond ONLY with valid JSON, no other text."""

        return prompt
    
    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM JSON response"""
        try:
            # Try to extract JSON from response
            # Sometimes LLM adds markdown code blocks
            if '```json' in response_text:
                json_start = response_text.find('```json') + 7
                json_end = response_text.find('```', json_start)
                response_text = response_text[json_start:json_end].strip()
            elif '```' in response_text:
                json_start = response_text.find('```') + 3
                json_end = response_text.find('```', json_start)
                response_text = response_text[json_start:json_end].strip()
            
            recommendation = json.loads(response_text)
            
            # Validate required fields
            required_fields = ['chart_type', 'reasoning', 'layout']
            if not all(field in recommendation for field in required_fields):
                raise ValueError("Missing required fields in LLM response")
            
            return recommendation
            
        except Exception as e:
            print(f"⚠️  Failed to parse LLM response: {e}")
            print(f"Response was: {response_text[:200]}")
            return {
                'chart_type': 'simple_bar',
                'reasoning': 'Fallback due to parsing error',
                'layout': 'single',
                'features': [],
                'title': 'Compensation Analysis'
            }
    
    def _fallback_recommendation(self, data: pd.DataFrame, 
                                 entities: Dict[str, Any]) -> Dict[str, Any]:
        """Rule-based fallback when LLM unavailable"""
        
        functions = entities.get('functions', [])
        intent = entities.get('intent', 'query')
        
        # Check data characteristics
        has_percentiles = all(col in data.columns for col in ['p10', 'p25', 'p50', 'p75', 'p90'])
        has_employees = 'employees' in data.columns
        row_count = len(data)
        
        # Decision logic
        if len(functions) == 1 and has_percentiles and has_employees and row_count >= 5:
            return {
                'chart_type': 'comprehensive_overview',
                'reasoning': 'Single function with rich data - comprehensive overview best',
                'layout': 'multi_panel',
                'features': ['percentile_bands', 'gradient_colors', 'employee_counts'],
                'title': f'{functions[0]} Salary Overview'
            }
        elif len(functions) >= 2 or intent == 'compare':
            return {
                'chart_type': 'comparison',
                'reasoning': 'Multiple functions - comparison chart best',
                'layout': 'single',
                'features': ['grouped_bars', 'clear_labels'],
                'title': f'{" vs ".join(functions)} Comparison'
            }
        elif intent == 'progression':
            return {
                'chart_type': 'progression',
                'reasoning': 'Career progression intent detected',
                'layout': 'single',
                'features': ['gradient_colors', 'trend_line'],
                'title': 'Career Progression'
            }
        elif has_percentiles:
            return {
                'chart_type': 'distribution',
                'reasoning': 'Percentile data available - show distribution',
                'layout': 'single',
                'features': ['percentile_bands', 'median_line'],
                'title': 'Salary Distribution'
            }
        else:
            return {
                'chart_type': 'simple_bar',
                'reasoning': 'Simple data - clean bar chart best',
                'layout': 'single',
                'features': ['value_labels'],
                'title': 'Compensation Analysis'
            }


if __name__ == "__main__":
    # Test visualization advisor
    print("="*70)
    print("VISUALIZATION ADVISOR TEST")
    print("="*70)
    
    # Create test data
    test_data = pd.DataFrame({
        'job_function': ['Engineering'] * 5,
        'job_level': ['Entry (P1)', 'Developing (P2)', 'Career (P3)', 'Advanced (P4)', 'Manager (M3)'],
        'p10': [80000, 100000, 120000, 150000, 180000],
        'p25': [90000, 110000, 135000, 170000, 200000],
        'p50': [105000, 125000, 155000, 195000, 220000],
        'p75': [120000, 145000, 180000, 225000, 250000],
        'p90': [135000, 165000, 205000, 255000, 280000],
        'employees': [2000, 12000, 35000, 38000, 7000]
    })
    
    advisor = VisualizationAdvisor()  # No LLM for test
    
    recommendation = advisor.recommend_visualization(
        test_data,
        "show me Engineering salaries",
        {'functions': ['Engineering'], 'intent': 'visualize'}
    )
    
    print("\nRecommendation:")
    print(f"  Chart Type: {recommendation['chart_type']}")
    print(f"  Reasoning: {recommendation['reasoning']}")
    print(f"  Layout: {recommendation['layout']}")
    print(f"  Features: {', '.join(recommendation.get('features', []))}")
