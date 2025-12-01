#!/usr/bin/env python3
"""
Finance vs Sales Quick Summary
"""

import sqlite3
import pandas as pd

def compare_finance_sales():
    conn = sqlite3.connect('compensation_data.db')
    
    query = """
    SELECT 
        jp.job_function,
        jp.job_level,
        COUNT(DISTINCT jp.id) as positions,
        SUM(cm.base_salary_lfy_emp_count) as employees,
        ROUND(AVG(cm.base_salary_lfy_p50), 0) as base_median,
        ROUND(AVG(cm.total_cash_p50), 0) as total_median
    FROM job_positions jp
    JOIN compensation_metrics cm ON jp.id = cm.job_position_id
    WHERE (jp.job_function LIKE '%Finance%' OR jp.job_function LIKE '%Sales%')
      AND cm.base_salary_lfy_p50 IS NOT NULL
      AND cm.total_cash_p50 IS NOT NULL
      AND jp.job_level IN (
          'Entry (P1)', 'Developing (P2)', 'Career (P3)', 'Advanced (P4)',
          'Manager (M3)', 'Expert (P5)', 'Sr Manager (M4)', 'Director (M5)',
          'Principal (P6)', 'Senior Director (M6)'
      )
    GROUP BY jp.job_function, jp.job_level
    ORDER BY jp.job_level, jp.job_function
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    print("\n" + "="*130)
    print("FINANCE VS SALES - SIDE-BY-SIDE COMPARISON")
    print("="*130)
    print(f"{'Level':<20} | {'Finance Base':<15} | {'Finance Total':<15} | {'Sales Base':<15} | {'Sales Total':<15} | {'Difference':<15}")
    print("-"*130)
    
    # Get unique levels
    levels = df['job_level'].unique()
    
    for level in levels:
        level_data = df[df['job_level'] == level]
        
        finance = level_data[level_data['job_function'].str.contains('Finance', case=False, na=False)]
        sales = level_data[level_data['job_function'].str.contains('Sales', case=False, na=False)]
        
        fin_base = finance['base_median'].values[0] if len(finance) > 0 else 0
        fin_total = finance['total_median'].values[0] if len(finance) > 0 else 0
        sales_base = sales['base_median'].values[0] if len(sales) > 0 else 0
        sales_total = sales['total_median'].values[0] if len(sales) > 0 else 0
        
        if fin_base > 0 and sales_base > 0:
            diff = fin_total - sales_total
            diff_pct = (diff / sales_total * 100) if sales_total > 0 else 0
            
            print(f"{level:<20} | ${fin_base:>13,} | ${fin_total:>13,} | ${sales_base:>13,} | ${sales_total:>13,} | ${diff:>13,} ({diff_pct:+.1f}%)")
    
    print("="*130)
    
    # Overall summary
    summary_query = """
    SELECT 
        jp.job_function,
        COUNT(DISTINCT jp.id) as positions,
        SUM(cm.base_salary_lfy_emp_count) as employees,
        ROUND(AVG(cm.base_salary_lfy_p50), 0) as avg_base,
        ROUND(AVG(cm.total_cash_p50), 0) as avg_total,
        ROUND(AVG(cm.total_cash_p50 - cm.base_salary_lfy_p50), 0) as avg_variable
    FROM job_positions jp
    JOIN compensation_metrics cm ON jp.id = cm.job_position_id
    WHERE (jp.job_function LIKE '%Finance%' OR jp.job_function LIKE '%Sales%')
      AND cm.base_salary_lfy_p50 IS NOT NULL
      AND cm.total_cash_p50 IS NOT NULL
    GROUP BY jp.job_function
    """
    
    summary_df = pd.read_sql_query(summary_query, conn)
    
    print("\nOVERALL SUMMARY:")
    print("="*130)
    print(f"{'Function':<15} | {'Positions':<10} | {'Employees':<12} | {'Avg Base':<15} | {'Avg Total':<15} | {'Variable Pay':<20}")
    print("-"*130)
    
    for _, row in summary_df.iterrows():
        var_pct = (row['avg_variable'] / row['avg_base'] * 100) if row['avg_base'] > 0 else 0
        print(f"{row['job_function']:<15} | {row['positions']:<10} | {row['employees']:<12,} | "
              f"${row['avg_base']:>13,} | ${row['avg_total']:>13,} | ${row['avg_variable']:>13,} ({var_pct:.1f}%)")
    
    print("="*130)

if __name__ == "__main__":
    compare_finance_sales()
