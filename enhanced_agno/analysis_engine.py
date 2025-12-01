#!/usr/bin/env python3
"""
Analysis Engine - Generates insights and summaries from data
This is what makes responses intelligent, not just data dumps
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional


class AnalysisEngine:
    """
    Performs sophisticated data analysis and generates insights.
    
    This is the key to better responses - turning data into insights.
    """
    
    def __init__(self):
        self.insight_templates = self._load_insight_templates()
    
    def analyze(self, data: Dict[str, Any], query_type: str) -> Dict[str, Any]:
        """
        Main analysis method - generates insights from data.
        
        Args:
            data: Query results
            query_type: Type of query (salary, comparison, progression)
            
        Returns:
            Enhanced data with insights and summary
        """
        if not data or data.get('status') != 'success':
            return data
        
        # Skip analysis for module queries - they have their own format
        if data.get('query_type') == 'module':
            return data
        
        # Generate insights based on query type
        insights = self.generate_insights(data, query_type)
        
        # Generate executive summary
        summary = self.generate_summary(data, insights, query_type)
        
        # Add to results
        data['insights'] = insights
        data['summary'] = summary
        
        return data
    
    def generate_insights(self, data: Dict[str, Any], query_type: str) -> List[str]:
        """
        Generate natural language insights from data.
        
        This is what makes responses intelligent!
        """
        insights = []
        
        if query_type == 'salary' or query_type == 'query':
            insights.extend(self._salary_insights(data))
        elif query_type == 'compare' or query_type == 'comparison':
            insights.extend(self._comparison_insights(data))
        elif query_type == 'progression':
            insights.extend(self._progression_insights(data))
        
        return insights
    
    def _salary_insights(self, data: Dict[str, Any]) -> List[str]:
        """Generate insights for salary queries"""
        insights = []
        
        # Get data
        records = data.get('data', [])
        if not records:
            return insights
        
        df = pd.DataFrame(records)
        
        # Insight 1: Range analysis with trend
        if 'avg_salary' in df.columns:
            salaries = df['avg_salary'].dropna()
            if len(salaries) > 0:
                min_sal = salaries.min()
                max_sal = salaries.max()
                median_sal = salaries.median()
                range_pct = ((max_sal - min_sal) / min_sal * 100) if min_sal > 0 else 0
                
                # Determine if distribution is skewed
                skew_indicator = ""
                if median_sal < (min_sal + max_sal) / 2:
                    skew_indicator = " (skewed toward lower end)"
                elif median_sal > (min_sal + max_sal) / 2:
                    skew_indicator = " (skewed toward higher end)"
                
                insights.append(
                    f"Salary range spans ${min_sal:,.0f} to ${max_sal:,.0f}, "
                    f"a {range_pct:.0f}% difference across levels{skew_indicator}"
                )
        
        # Insight 2: Employee distribution with significance
        if 'employees' in df.columns:
            total_emp = df['employees'].sum()
            if total_emp > 0:
                # Find level with most employees
                max_emp_row = df.loc[df['employees'].idxmax()]
                level = max_emp_row.get('job_level', 'Unknown')
                emp_count = max_emp_row['employees']
                pct = (emp_count / total_emp * 100)
                
                # Check if this is significantly concentrated
                concentration_note = ""
                if pct > 40:
                    concentration_note = " - highly concentrated"
                elif pct > 25:
                    concentration_note = " - moderately concentrated"
                
                insights.append(
                    f"Largest concentration at {level} with {emp_count:,} employees "
                    f"({pct:.0f}% of total{concentration_note})"
                )
        
        # Insight 3: Salary-to-headcount correlation
        if 'avg_salary' in df.columns and 'employees' in df.columns and len(df) > 2:
            # Calculate correlation between salary and employee count
            correlation = df[['avg_salary', 'employees']].corr().iloc[0, 1]
            
            if abs(correlation) > 0.5:
                direction = "higher" if correlation > 0 else "lower"
                strength = "strong" if abs(correlation) > 0.7 else "moderate"
                insights.append(
                    f"Positions with {direction} salaries tend to have {direction} headcount "
                    f"({strength} correlation: {correlation:.2f})"
                )
            else:
                insights.append(
                    f"Salary levels show little correlation with headcount distribution "
                    f"(correlation: {correlation:.2f})"
                )
        
        # Insight 4: Identify outliers
        if 'avg_salary' in df.columns and len(df) > 3:
            outliers = self.identify_outliers(data)
            if outliers:
                outlier = outliers[0]  # Report first outlier
                outlier_type = "significantly higher" if outlier['type'] == 'high' else "significantly lower"
                insights.append(
                    f"{outlier['level']} shows {outlier_type} compensation "
                    f"(${outlier['salary']:,.0f}) compared to other levels"
                )
        
        return insights[:4]  # Top 4 insights

    def _comparison_insights(self, data: Dict[str, Any]) -> List[str]:
        """Generate insights for comparison queries"""
        insights = []
        
        records = data.get('data', [])
        if not records or len(records) < 2:
            return insights
        
        df = pd.DataFrame(records)
        
        # Group by function if comparing functions
        if 'job_function' in df.columns and len(df['job_function'].unique()) > 1:
            functions = df['job_function'].unique()
            
            # Compare average salaries with context
            if 'avg_salary' in df.columns:
                func_salaries = df.groupby('job_function')['avg_salary'].mean()
                
                if len(func_salaries) >= 2:
                    highest = func_salaries.idxmax()
                    lowest = func_salaries.idxmin()
                    diff = func_salaries[highest] - func_salaries[lowest]
                    pct_diff = (diff / func_salaries[lowest] * 100) if func_salaries[lowest] > 0 else 0
                    
                    # Add context about significance
                    significance = ""
                    if pct_diff > 50:
                        significance = " - substantial premium"
                    elif pct_diff > 25:
                        significance = " - notable difference"
                    elif pct_diff < 10:
                        significance = " - relatively similar"
                    
                    insights.append(
                        f"{highest} pays {pct_diff:.0f}% more than {lowest} on average "
                        f"(${func_salaries[highest]:,.0f} vs ${func_salaries[lowest]:,.0f}){significance}"
                    )
            
            # Compare employee counts with ratio
            if 'employees' in df.columns:
                func_employees = df.groupby('job_function')['employees'].sum()
                
                if len(func_employees) >= 2:
                    largest = func_employees.idxmax()
                    smallest = func_employees.idxmin()
                    ratio = func_employees[largest] / func_employees[smallest] if func_employees[smallest] > 0 else 0
                    
                    insights.append(
                        f"{largest} has {func_employees[largest]:,} employees vs "
                        f"{func_employees[smallest]:,} in {smallest} ({ratio:.1f}x larger workforce)"
                    )
            
            # Compare salary ranges
            if 'avg_salary' in df.columns and 'job_function' in df.columns:
                for func in functions[:2]:  # Compare first two functions
                    func_data = df[df['job_function'] == func]['avg_salary']
                    if len(func_data) > 1:
                        salary_range = func_data.max() - func_data.min()
                        range_pct = (salary_range / func_data.min() * 100) if func_data.min() > 0 else 0
                        
                        insights.append(
                            f"{func} shows {range_pct:.0f}% salary range across levels "
                            f"(${func_data.min():,.0f} to ${func_data.max():,.0f})"
                        )
            
            # Compare position diversity
            if 'positions' in df.columns and 'employees' in df.columns:
                func_stats = df.groupby('job_function').agg({
                    'positions': 'sum',
                    'employees': 'sum'
                })
                
                if len(func_stats) >= 2:
                    func_stats['emp_per_pos'] = func_stats['employees'] / func_stats['positions']
                    
                    most_diverse = func_stats['emp_per_pos'].idxmin()
                    least_diverse = func_stats['emp_per_pos'].idxmax()
                    
                    insights.append(
                        f"{most_diverse} has more position diversity "
                        f"({func_stats.loc[most_diverse, 'emp_per_pos']:.0f} emp/position) vs "
                        f"{least_diverse} ({func_stats.loc[least_diverse, 'emp_per_pos']:.0f} emp/position)"
                    )
        
        return insights[:4]
    
    def _progression_insights(self, data: Dict[str, Any]) -> List[str]:
        """Generate insights for career progression queries"""
        insights = []
        
        records = data.get('data', [])
        if not records:
            return insights
        
        df = pd.DataFrame(records)
        
        if 'avg_salary' in df.columns and len(df) > 1:
            # Calculate growth rates
            salaries = df['avg_salary'].values
            growth_rates = []
            absolute_increases = []
            
            for i in range(1, len(salaries)):
                if salaries[i-1] > 0:
                    growth = ((salaries[i] - salaries[i-1]) / salaries[i-1]) * 100
                    growth_rates.append(growth)
                    absolute_increases.append(salaries[i] - salaries[i-1])
            
            if growth_rates:
                avg_growth = np.mean(growth_rates)
                max_growth = max(growth_rates)
                min_growth = min(growth_rates)
                max_growth_idx = growth_rates.index(max_growth)
                
                # Overall progression insight
                total_growth = ((salaries[-1] - salaries[0]) / salaries[0] * 100) if salaries[0] > 0 else 0
                insights.append(
                    f"Career progression shows {total_growth:.0f}% total growth from entry to top level "
                    f"(avg {avg_growth:.1f}% per level)"
                )
                
                # Largest jump insight
                if 'job_level' in df.columns and max_growth_idx + 1 < len(df):
                    from_level = df.iloc[max_growth_idx]['job_level']
                    to_level = df.iloc[max_growth_idx + 1]['job_level']
                    abs_increase = absolute_increases[max_growth_idx]
                    
                    insights.append(
                        f"Largest jump ({max_growth:.0f}%, +${abs_increase:,.0f}) occurs from "
                        f"{from_level} to {to_level}"
                    )
                
                # Growth consistency insight
                growth_std = np.std(growth_rates)
                if growth_std < 5:
                    insights.append(
                        f"Progression is highly consistent with similar growth at each level "
                        f"(std dev: {growth_std:.1f}%)"
                    )
                elif growth_std > 15:
                    insights.append(
                        f"Progression varies significantly between levels "
                        f"(std dev: {growth_std:.1f}%, range: {min_growth:.0f}% to {max_growth:.0f}%)"
                    )
                
                # Acceleration/deceleration insight
                if len(growth_rates) >= 3:
                    early_growth = np.mean(growth_rates[:len(growth_rates)//2])
                    late_growth = np.mean(growth_rates[len(growth_rates)//2:])
                    
                    if late_growth > early_growth * 1.2:
                        insights.append(
                            f"Career progression accelerates at higher levels "
                            f"({late_growth:.1f}% vs {early_growth:.1f}% in early career)"
                        )
                    elif late_growth < early_growth * 0.8:
                        insights.append(
                            f"Career progression slows at higher levels "
                            f"({late_growth:.1f}% vs {early_growth:.1f}% in early career)"
                        )
        
        return insights[:4]
    
    def generate_summary(self, data: Dict[str, Any], insights: List[str], 
                        query_type: str) -> str:
        """
        Generate executive summary with context and interpretation.
        
        This provides the high-level answer users want with added context.
        """
        records = data.get('data', [])
        if not records:
            return "No data available for analysis."
        
        df = pd.DataFrame(records)
        
        # Build contextual summary based on query type
        if query_type == 'compare' or query_type == 'comparison':
            return self._generate_comparison_summary(df, insights)
        elif query_type == 'progression':
            return self._generate_progression_summary(df, insights)
        else:
            return self._generate_standard_summary(df, insights)
    
    def _generate_standard_summary(self, df: pd.DataFrame, insights: List[str]) -> str:
        """Generate summary for standard salary queries"""
        summary_parts = []
        
        # Key metric with context
        if 'avg_salary' in df.columns:
            avg_salary = df['avg_salary'].mean()
            min_salary = df['avg_salary'].min()
            max_salary = df['avg_salary'].max()
            
            summary_parts.append(
                f"Average compensation: ${avg_salary:,.0f} "
                f"(range: ${min_salary:,.0f} - ${max_salary:,.0f})"
            )
        
        # Workforce metrics
        if 'employees' in df.columns:
            total_emp = df['employees'].sum()
            summary_parts.append(f"Total workforce: {total_emp:,} employees")
        
        # Position diversity
        if 'positions' in df.columns:
            total_pos = df['positions'].sum()
            if 'employees' in df.columns:
                emp_per_pos = df['employees'].sum() / total_pos if total_pos > 0 else 0
                summary_parts.append(
                    f"{total_pos} distinct positions (avg {emp_per_pos:.0f} employees each)"
                )
            else:
                summary_parts.append(f"{total_pos} distinct positions")
        
        # Add function/level context if available
        if 'job_function' in df.columns:
            functions = df['job_function'].unique()
            if len(functions) == 1:
                summary_parts.insert(0, f"Function: {functions[0]}")
        
        return " | ".join(summary_parts)
    
    def _generate_comparison_summary(self, df: pd.DataFrame, insights: List[str]) -> str:
        """Generate summary for comparison queries"""
        summary_parts = []
        
        if 'job_function' in df.columns and len(df['job_function'].unique()) > 1:
            functions = df['job_function'].unique()
            summary_parts.append(f"Comparing: {' vs '.join(functions)}")
            
            # Salary comparison
            if 'avg_salary' in df.columns:
                func_salaries = df.groupby('job_function')['avg_salary'].mean()
                highest = func_salaries.idxmax()
                lowest = func_salaries.idxmin()
                diff_pct = ((func_salaries[highest] - func_salaries[lowest]) / func_salaries[lowest] * 100)
                
                summary_parts.append(
                    f"{highest} leads by {diff_pct:.0f}% "
                    f"(${func_salaries[highest]:,.0f} vs ${func_salaries[lowest]:,.0f})"
                )
            
            # Headcount comparison
            if 'employees' in df.columns:
                func_employees = df.groupby('job_function')['employees'].sum()
                total_emp = func_employees.sum()
                summary_parts.append(f"Total: {total_emp:,} employees across both functions")
        
        return " | ".join(summary_parts)
    
    def _generate_progression_summary(self, df: pd.DataFrame, insights: List[str]) -> str:
        """Generate summary for progression queries"""
        summary_parts = []
        
        if 'job_function' in df.columns:
            functions = df['job_function'].unique()
            if len(functions) == 1:
                summary_parts.append(f"Career Path: {functions[0]}")
        
        if 'avg_salary' in df.columns and len(df) > 1:
            entry_salary = df['avg_salary'].iloc[0]
            top_salary = df['avg_salary'].iloc[-1]
            total_growth = ((top_salary - entry_salary) / entry_salary * 100) if entry_salary > 0 else 0
            
            summary_parts.append(
                f"Entry to top: ${entry_salary:,.0f} → ${top_salary:,.0f} "
                f"({total_growth:.0f}% growth)"
            )
        
        if 'job_level' in df.columns:
            levels = len(df['job_level'].unique())
            summary_parts.append(f"{levels} career levels")
        
        return " | ".join(summary_parts)
    
    def _load_insight_templates(self) -> Dict[str, List[str]]:
        """Load templates for generating insights"""
        return {
            'salary_range': "Salary range spans ${min} to ${max}, a {pct}% difference",
            'concentration': "Largest concentration at {level} with {count} employees",
            'comparison': "{func1} pays {pct}% more than {func2}",
            'growth': "Average salary growth of {pct}% between levels",
        }
    
    def identify_outliers(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify statistical outliers in the data"""
        records = data.get('data', [])
        if not records:
            return []
        
        df = pd.DataFrame(records)
        outliers = []
        
        if 'avg_salary' in df.columns and len(df) > 3:
            salaries = df['avg_salary']
            q1 = salaries.quantile(0.25)
            q3 = salaries.quantile(0.75)
            iqr = q3 - q1
            
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            outlier_rows = df[(salaries < lower_bound) | (salaries > upper_bound)]
            
            for _, row in outlier_rows.iterrows():
                outliers.append({
                    'level': row.get('job_level', 'Unknown'),
                    'salary': row.get('avg_salary', 0),
                    'type': 'high' if row['avg_salary'] > upper_bound else 'low'
                })
        
        return outliers
    
    def calculate_significance(self, data1: Dict[str, Any], data2: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate statistical significance between two datasets.
        Uses t-test to determine if differences are statistically significant.
        """
        from scipy import stats
        
        records1 = data1.get('data', [])
        records2 = data2.get('data', [])
        
        if not records1 or not records2:
            return {'significant': False, 'reason': 'Insufficient data'}
        
        df1 = pd.DataFrame(records1)
        df2 = pd.DataFrame(records2)
        
        if 'avg_salary' not in df1.columns or 'avg_salary' not in df2.columns:
            return {'significant': False, 'reason': 'Missing salary data'}
        
        salaries1 = df1['avg_salary'].dropna()
        salaries2 = df2['avg_salary'].dropna()
        
        if len(salaries1) < 2 or len(salaries2) < 2:
            return {'significant': False, 'reason': 'Too few data points'}
        
        # Perform t-test
        t_stat, p_value = stats.ttest_ind(salaries1, salaries2)
        
        return {
            'significant': p_value < 0.05,
            'p_value': p_value,
            't_statistic': t_stat,
            'confidence': 'high' if p_value < 0.01 else 'moderate' if p_value < 0.05 else 'low'
        }
    
    def calculate_percentiles(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate salary percentiles (P10, P25, P50, P75, P90)"""
        records = data.get('data', [])
        if not records:
            return {}
        
        df = pd.DataFrame(records)
        
        if 'avg_salary' not in df.columns:
            return {}
        
        salaries = df['avg_salary'].dropna()
        
        if len(salaries) == 0:
            return {}
        
        return {
            'p10': salaries.quantile(0.10),
            'p25': salaries.quantile(0.25),
            'p50': salaries.quantile(0.50),
            'p75': salaries.quantile(0.75),
            'p90': salaries.quantile(0.90),
            'mean': salaries.mean(),
            'std': salaries.std()
        }
    
    def calculate_correlation(self, data: Dict[str, Any], var1: str, var2: str) -> Dict[str, Any]:
        """Calculate correlation between two variables"""
        records = data.get('data', [])
        if not records:
            return {'correlation': 0, 'strength': 'none'}
        
        df = pd.DataFrame(records)
        
        if var1 not in df.columns or var2 not in df.columns:
            return {'correlation': 0, 'strength': 'none'}
        
        # Drop NaN values
        clean_df = df[[var1, var2]].dropna()
        
        if len(clean_df) < 3:
            return {'correlation': 0, 'strength': 'insufficient data'}
        
        correlation = clean_df[var1].corr(clean_df[var2])
        
        # Determine strength
        abs_corr = abs(correlation)
        if abs_corr > 0.7:
            strength = 'strong'
        elif abs_corr > 0.4:
            strength = 'moderate'
        elif abs_corr > 0.2:
            strength = 'weak'
        else:
            strength = 'negligible'
        
        return {
            'correlation': correlation,
            'strength': strength,
            'direction': 'positive' if correlation > 0 else 'negative'
        }


if __name__ == "__main__":
    # Test the analysis engine
    print("="*70)
    print("ANALYSIS ENGINE TEST")
    print("="*70)
    
    engine = AnalysisEngine()
    
    # Test data
    test_data = {
        'status': 'success',
        'data': [
            {'job_level': 'Entry (P1)', 'avg_salary': 105000, 'employees': 3368, 'positions': 18},
            {'job_level': 'Manager (M3)', 'avg_salary': 219000, 'employees': 8133, 'positions': 26},
            {'job_level': 'Director (M5)', 'avg_salary': 271000, 'employees': 7468, 'positions': 26},
        ]
    }
    
    result = engine.analyze(test_data, 'salary')
    
    print("\n📊 Summary:")
    print(result['summary'])
    
    print("\n💡 Insights:")
    for i, insight in enumerate(result['insights'], 1):
        print(f"{i}. {insight}")
