#!/usr/bin/env python3
"""
Finance Salary Analysis
Analyzes compensation data for Finance function
"""

import sqlite3
import pandas as pd

def analyze_finance_salaries():
    """Analyze finance salaries by level and specialization"""
    
    conn = sqlite3.connect('compensation_data.db')
    
    # Query 1: Salary by Level Overview
    query_by_level = """
    SELECT 
        jp.job_level,
        COUNT(DISTINCT jp.id) as positions,
        SUM(cm.base_salary_lfy_emp_count) as employees,
        ROUND(AVG(cm.base_salary_lfy_p10), 0) as p10,
        ROUND(AVG(cm.base_salary_lfy_p25), 0) as p25,
        ROUND(AVG(cm.base_salary_lfy_p50), 0) as p50,
        ROUND(AVG(cm.base_salary_lfy_p75), 0) as p75,
        ROUND(AVG(cm.base_salary_lfy_p90), 0) as p90
    FROM job_positions jp
    JOIN compensation_metrics cm ON jp.id = cm.job_position_id
    WHERE jp.job_function LIKE '%Finance%'
      AND cm.base_salary_lfy_p50 IS NOT NULL
    GROUP BY jp.job_level
    ORDER BY p50
    """
    
    df_levels = pd.read_sql_query(query_by_level, conn)
    
    # Query 2: Top Specializations
    query_specializations = """
    SELECT 
        jp.job_focus,
        COUNT(DISTINCT jp.id) as positions,
        SUM(cm.base_salary_lfy_emp_count) as employees,
        ROUND(AVG(cm.base_salary_lfy_p50), 0) as avg_salary
    FROM job_positions jp
    JOIN compensation_metrics cm ON jp.id = cm.job_position_id
    WHERE jp.job_function LIKE '%Finance%'
      AND jp.job_focus IS NOT NULL
      AND jp.job_focus != ''
      AND cm.base_salary_lfy_p50 IS NOT NULL
    GROUP BY jp.job_focus
    HAVING COUNT(DISTINCT jp.id) >= 3
    ORDER BY avg_salary DESC
    LIMIT 10
    """
    
    df_specializations = pd.read_sql_query(query_specializations, conn)
    
    # Query 3: Career Progression
    query_progression = """
    SELECT 
        jp.job_level,
        ROUND(AVG(cm.base_salary_lfy_p50), 0) as median_salary,
        SUM(cm.base_salary_lfy_emp_count) as employees
    FROM job_positions jp
    JOIN compensation_metrics cm ON jp.id = cm.job_position_id
    WHERE jp.job_function LIKE '%Finance%'
      AND cm.base_salary_lfy_p50 IS NOT NULL
      AND jp.job_level IN (
          'Entry (P1)', 'Developing (P2)', 'Career (P3)', 'Advanced (P4)',
          'Manager (M3)', 'Expert (P5)', 'Sr Manager (M4)', 'Director (M5)',
          'Principal (P6)', 'Senior Director (M6)'
      )
    GROUP BY jp.job_level
    ORDER BY median_salary
    """
    
    df_progression = pd.read_sql_query(query_progression, conn)
    
    conn.close()
    
    # Print Results
    print("=" * 120)
    print("FINANCE BASE SALARY ANALYSIS")
    print("=" * 120)
    
    print("\n" + "=" * 120)
    print("1. SALARY BY LEVEL OVERVIEW")
    print("=" * 120)
    print(f"{'Level':<25} | {'Positions':<10} | {'Employees':<10} | {'10th %':<12} | {'25th %':<12} | {'Median':<12} | {'75th %':<12} | {'90th %':<11}")
    print("-" * 120)
    
    for _, row in df_levels.iterrows():
        print(f"{row['job_level']:<25} | {row['positions']:<10} | {row['employees']:<10,} | "
              f"${row['p10']:>11,} | ${row['p25']:>11,} | ${row['p50']:>11,} | "
              f"${row['p75']:>11,} | ${row['p90']:>10,}")
    
    print("\n" + "=" * 100)
    print("2. CAREER PROGRESSION ANALYSIS")
    print("=" * 100)
    print(f"{'Level':<20} | {'Median Salary':<15} | {'Increase':<15} | {'% Increase':<12} | {'Employees'}")
    print("-" * 100)
    
    prev_salary = None
    for _, row in df_progression.iterrows():
        if prev_salary is None:
            print(f"{row['job_level']:<20} | ${row['median_salary']:>14,} | {'-':>15} | {'-':>12} | {row['employees']:>9,}")
        else:
            increase = row['median_salary'] - prev_salary
            pct_increase = (increase / prev_salary * 100) if prev_salary > 0 else 0
            print(f"{row['job_level']:<20} | ${row['median_salary']:>14,} | ${increase:>14,} | {pct_increase:>11.1f}% | {row['employees']:>9,}")
        prev_salary = row['median_salary']
    
    print("\n" + "=" * 100)
    print("3. TOP SPECIALIZATIONS")
    print("=" * 100)
    print(f"{'Focus Area':<50} | {'Avg Salary':<15} | {'Employees'}")
    print("-" * 100)
    
    for _, row in df_specializations.iterrows():
        print(f"{row['job_focus']:<50} | ${row['avg_salary']:>14,} | {row['employees']:>9}")
    
    print("=" * 100)
    print("\nAnalysis complete!")

if __name__ == "__main__":
    analyze_finance_salaries()
