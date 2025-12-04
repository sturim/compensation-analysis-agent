#!/usr/bin/env python3
"""
Comparison Engine - Advanced comparison and benchmarking capabilities
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple


class ComparisonEngine:
    """
    Performs sophisticated comparisons and benchmarking.
    
    Supports:
    - Side-by-side function comparisons
    - Level-specific comparisons
    - Benchmarking against market
    - Variable pay analysis
    """
    
    def __init__(self):
        pass
    
    def compare_functions(self, data1: Dict[str, Any], data2: Dict[str, Any], 
                         function1: str, function2: str, specific_level: str = None) -> Dict[str, Any]:
        """
        Create detailed side-by-side comparison of two functions.
        
        Args:
            data1: Results for first function
            data2: Results for second function
            function1: Name of first function
            function2: Name of second function
            specific_level: Optional specific job level to compare
            
        Returns:
            Comprehensive comparison dictionary
        """
        records1 = data1.get('data', [])
        records2 = data2.get('data', [])
        
        if not records1 or not records2:
            return {'status': 'error', 'message': 'Insufficient data for comparison'}
        
        df1 = pd.DataFrame(records1)
        df2 = pd.DataFrame(records2)
        
        # If specific level requested, filter to that level
        if specific_level and 'job_level' in df1.columns and 'job_level' in df2.columns:
            df1_level = df1[df1['job_level'] == specific_level]
            df2_level = df2[df2['job_level'] == specific_level]
            
            if not df1_level.empty and not df2_level.empty:
                # Use level-specific data for comparison
                df1 = df1_level
                df2 = df2_level
        
        comparison = {
            'function1': function1,
            'function2': function2,
            'specific_level': specific_level,
            'metrics': {}
        }
        
        # Compare average salaries
        if 'avg_salary' in df1.columns and 'avg_salary' in df2.columns:
            avg1 = df1['avg_salary'].mean()
            avg2 = df2['avg_salary'].mean()
            diff = avg1 - avg2
            pct_diff = (diff / avg2 * 100) if avg2 > 0 else 0
            
            comparison['metrics']['average_salary'] = {
                function1: avg1,
                function2: avg2,
                'difference': diff,
                'percent_difference': pct_diff,
                'higher': function1 if avg1 > avg2 else function2
            }
        
        # Compare salary ranges
        if 'avg_salary' in df1.columns and 'avg_salary' in df2.columns:
            range1 = df1['avg_salary'].max() - df1['avg_salary'].min()
            range2 = df2['avg_salary'].max() - df2['avg_salary'].min()
            
            comparison['metrics']['salary_range'] = {
                function1: {
                    'min': df1['avg_salary'].min(),
                    'max': df1['avg_salary'].max(),
                    'range': range1
                },
                function2: {
                    'min': df2['avg_salary'].min(),
                    'max': df2['avg_salary'].max(),
                    'range': range2
                },
                'wider_range': function1 if range1 > range2 else function2
            }
        
        # Compare employee counts
        if 'employees' in df1.columns and 'employees' in df2.columns:
            total1 = df1['employees'].sum()
            total2 = df2['employees'].sum()
            
            comparison['metrics']['workforce'] = {
                function1: total1,
                function2: total2,
                'difference': total1 - total2,
                'ratio': total1 / total2 if total2 > 0 else 0,
                'larger': function1 if total1 > total2 else function2
            }
        
        # Compare position counts
        if 'positions' in df1.columns and 'positions' in df2.columns:
            pos1 = df1['positions'].sum()
            pos2 = df2['positions'].sum()
            
            comparison['metrics']['positions'] = {
                function1: pos1,
                function2: pos2,
                'difference': pos1 - pos2,
                'more_diverse': function1 if pos1 > pos2 else function2
            }
        
        # Compare level distribution
        if 'job_level' in df1.columns and 'job_level' in df2.columns:
            levels1 = set(df1['job_level'].unique())
            levels2 = set(df2['job_level'].unique())
            
            comparison['metrics']['levels'] = {
                function1: list(levels1),
                function2: list(levels2),
                'common_levels': list(levels1 & levels2),
                'unique_to_' + function1: list(levels1 - levels2),
                'unique_to_' + function2: list(levels2 - levels1)
            }
        
        comparison['status'] = 'success'
        return comparison
    
    def compare_at_level(self, data: Dict[str, Any], level: str) -> Dict[str, Any]:
        """
        Compare functions at a specific level.
        
        Args:
            data: Combined data with multiple functions
            level: Job level to compare at
            
        Returns:
            Level-specific comparison
        """
        records = data.get('data', [])
        if not records:
            return {'status': 'error', 'message': 'No data available'}
        
        df = pd.DataFrame(records)
        
        # Filter to specific level
        if 'job_level' not in df.columns:
            return {'status': 'error', 'message': 'Level information not available'}
        
        level_df = df[df['job_level'] == level]
        
        if level_df.empty:
            return {'status': 'error', 'message': f'No data for level: {level}'}
        
        comparison = {
            'level': level,
            'functions': {}
        }
        
        # Compare each function at this level
        if 'job_function' in level_df.columns:
            for function in level_df['job_function'].unique():
                func_data = level_df[level_df['job_function'] == function]
                
                if not func_data.empty:
                    comparison['functions'][function] = {
                        'avg_salary': func_data['avg_salary'].iloc[0] if 'avg_salary' in func_data.columns else None,
                        'employees': func_data['employees'].iloc[0] if 'employees' in func_data.columns else None,
                        'positions': func_data['positions'].iloc[0] if 'positions' in func_data.columns else None
                    }
        
        # Calculate rankings
        if comparison['functions']:
            salaries = {f: d['avg_salary'] for f, d in comparison['functions'].items() if d['avg_salary']}
            if salaries:
                sorted_funcs = sorted(salaries.items(), key=lambda x: x[1], reverse=True)
                comparison['salary_ranking'] = [f for f, _ in sorted_funcs]
                comparison['highest_paid'] = sorted_funcs[0][0]
                comparison['lowest_paid'] = sorted_funcs[-1][0]
        
        comparison['status'] = 'success'
        return comparison
    
    def calculate_benchmarks(self, data: Dict[str, Any], 
                            target_function: str = None) -> Dict[str, Any]:
        """
        Calculate market positioning and percentile rankings.
        
        Args:
            data: Salary data
            target_function: Optional function to benchmark
            
        Returns:
            Benchmarking metrics
        """
        records = data.get('data', [])
        if not records:
            return {'status': 'error', 'message': 'No data available'}
        
        df = pd.DataFrame(records)
        
        if 'avg_salary' not in df.columns:
            return {'status': 'error', 'message': 'Salary data not available'}
        
        benchmarks = {}
        
        # Overall market benchmarks
        salaries = df['avg_salary'].dropna()
        
        benchmarks['market'] = {
            'p10': salaries.quantile(0.10),
            'p25': salaries.quantile(0.25),
            'p50': salaries.quantile(0.50),
            'p75': salaries.quantile(0.75),
            'p90': salaries.quantile(0.90),
            'mean': salaries.mean(),
            'std': salaries.std()
        }
        
        # Function-specific benchmarks
        if target_function and 'job_function' in df.columns:
            func_df = df[df['job_function'] == target_function]
            
            if not func_df.empty and 'avg_salary' in func_df.columns:
                func_salaries = func_df['avg_salary'].dropna()
                func_avg = func_salaries.mean()
                
                # Calculate percentile in overall market
                percentile = (salaries < func_avg).sum() / len(salaries) * 100
                
                benchmarks[target_function] = {
                    'average': func_avg,
                    'market_percentile': percentile,
                    'vs_market_mean': func_avg - benchmarks['market']['mean'],
                    'vs_market_median': func_avg - benchmarks['market']['p50'],
                    'positioning': self._get_market_position(percentile)
                }
        
        benchmarks['status'] = 'success'
        return benchmarks
    
    def analyze_variable_pay(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze variable pay components.
        
        Note: This is a placeholder - actual implementation would need
        variable pay data in the database.
        
        Args:
            data: Compensation data
            
        Returns:
            Variable pay analysis
        """
        # Placeholder implementation
        # In a real system, this would analyze bonus, equity, etc.
        
        return {
            'status': 'not_implemented',
            'message': 'Variable pay analysis requires additional data fields',
            'suggestion': 'Add variable_pay columns to database for full analysis'
        }
    
    def compare_total_compensation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare total compensation including base + variable.
        
        Note: Placeholder - needs variable pay data.
        
        Args:
            data: Compensation data
            
        Returns:
            Total compensation comparison
        """
        # Placeholder implementation
        
        return {
            'status': 'not_implemented',
            'message': 'Total compensation analysis requires variable pay data',
            'suggestion': 'Currently showing base salary only'
        }
    
    def _get_market_position(self, percentile: float) -> str:
        """Determine market position from percentile"""
        if percentile >= 90:
            return "Top tier (90th+ percentile)"
        elif percentile >= 75:
            return "Above market (75th-90th percentile)"
        elif percentile >= 50:
            return "Market rate (50th-75th percentile)"
        elif percentile >= 25:
            return "Below market (25th-50th percentile)"
        else:
            return "Bottom tier (below 25th percentile)"
    
    def format_comparison(self, comparison: Dict[str, Any]) -> str:
        """Format comparison results for display"""
        if comparison.get('status') != 'success':
            return f"Comparison failed: {comparison.get('message', 'Unknown error')}"
        
        output = []
        output.append(f"\n{'='*70}")
        output.append(f"COMPARISON: {comparison.get('function1', 'A')} vs {comparison.get('function2', 'B')}")
        output.append(f"{'='*70}\n")
        
        metrics = comparison.get('metrics', {})
        
        # Salary comparison
        if 'average_salary' in metrics:
            sal = metrics['average_salary']
            output.append("Average Salary:")
            output.append(f"  {comparison['function1']}: ${sal[comparison['function1']]:,.0f}")
            output.append(f"  {comparison['function2']}: ${sal[comparison['function2']]:,.0f}")
            output.append(f"  Difference: ${abs(sal['difference']):,.0f} ({abs(sal['percent_difference']):.1f}%)")
            output.append(f"  Higher: {sal['higher']}\n")
        
        # Workforce comparison
        if 'workforce' in metrics:
            wf = metrics['workforce']
            output.append("Workforce Size:")
            output.append(f"  {comparison['function1']}: {wf[comparison['function1']]:,} employees")
            output.append(f"  {comparison['function2']}: {wf[comparison['function2']]:,} employees")
            output.append(f"  Ratio: {wf['ratio']:.2f}x")
            output.append(f"  Larger: {wf['larger']}\n")
        
        return '\n'.join(output)


if __name__ == "__main__":
    # Test comparison engine
    print("="*70)
    print("COMPARISON ENGINE TEST")
    print("="*70)
    
    engine = ComparisonEngine()
    
    # Test data
    data1 = {
        'data': [
            {'job_function': 'Engineering', 'job_level': 'Entry (P1)', 'avg_salary': 105000, 'employees': 3368, 'positions': 18},
            {'job_function': 'Engineering', 'job_level': 'Manager (M3)', 'avg_salary': 219000, 'employees': 8133, 'positions': 26},
        ]
    }
    
    data2 = {
        'data': [
            {'job_function': 'Sales', 'job_level': 'Entry (P1)', 'avg_salary': 85000, 'employees': 2500, 'positions': 15},
            {'job_function': 'Sales', 'job_level': 'Manager (M3)', 'avg_salary': 178000, 'employees': 6000, 'positions': 20},
        ]
    }
    
    # Test function comparison
    print("\n1. Function Comparison:")
    comparison = engine.compare_functions(data1, data2, 'Engineering', 'Sales')
    print(engine.format_comparison(comparison))
    
    # Test benchmarking
    print("\n2. Benchmarking:")
    combined_data = {
        'data': data1['data'] + data2['data']
    }
    benchmarks = engine.calculate_benchmarks(combined_data, 'Engineering')
    print(f"   Market P50: ${benchmarks['market']['p50']:,.0f}")
    if 'Engineering' in benchmarks:
        print(f"   Engineering Avg: ${benchmarks['Engineering']['average']:,.0f}")
        print(f"   Market Position: {benchmarks['Engineering']['positioning']}")
