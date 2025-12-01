#!/usr/bin/env python3
import sqlite3
import pandas as pd

conn = sqlite3.connect('compensation_data.db')

query = """
SELECT 
    jp.job_level,
    COUNT(DISTINCT jp.id) as positions,
    SUM(cm.base_salary_lfy_emp_count) as employees,
    ROUND(AVG(cm.base_salary_lfy_p50), 0) as median_salary
FROM job_positions jp
JOIN compensation_metrics cm ON jp.id = cm.job_position_id
WHERE jp.job_function LIKE '%Engineering%'
  AND cm.base_salary_lfy_p50 IS NOT NULL
  AND jp.job_level IN (
      'Entry (P1)', 'Developing (P2)', 'Career (P3)', 'Advanced (P4)',
      'Manager (M3)', 'Expert (P5)', 'Sr Manager (M4)', 'Director (M5)',
      'Principal (P6)', 'Senior Director (M6)'
  )
GROUP BY jp.job_level
ORDER BY median_salary
"""

df = pd.read_sql_query(query, conn)
conn.close()

print("\n" + "="*80)
print("ENGINEERING SALARIES")
print("="*80)
print(f"{'Level':<25} | {'Positions':<10} | {'Employees':<12} | {'Median Salary':<15}")
print("-"*80)

for _, row in df.iterrows():
    print(f"{row['job_level']:<25} | {row['positions']:<10} | {row['employees']:<12,} | ${row['median_salary']:>13,}")

print("="*80)
print(f"Total: {len(df)} levels, {df['employees'].sum():,} employees")
print("="*80)
