#!/usr/bin/env python3
"""
Finance vs Sales Salary Comparison
Creates side-by-side comparison charts
"""

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Set style for professional charts
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

class FinanceVsSalesCharts:
    """Create finance vs sales comparison visualizations"""
    
    def __init__(self, db_path: str = "compensation_data.db"):
        self.db_path = db_path
        self.output_dir = Path("charts")
        self.output_dir.mkdir(exist_ok=True)
        
        # Set up matplotlib for better charts
        plt.rcParams['figure.figsize'] = (16, 10)
        plt.rcParams['font.size'] = 10
        plt.rcParams['axes.titlesize'] = 14
        plt.rcParams['axes.labelsize'] = 12
        
    def load_data(self, query: str) -> pd.DataFrame:
        """Load data from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        except Exception as e:
            print(f"Error loading data: {e}")
            return pd.DataFrame()
    
    def create_comparison_chart(self):
        """Create comprehensive comparison between Finance and Sales"""
        
        # Query for both functions
        query = """
        SELECT 
            jp.job_function,
            jp.job_level,
            COUNT(DISTINCT jp.id) as positions,
            SUM(cm.base_salary_lfy_emp_count) as employees,
            ROUND(AVG(cm.base_salary_lfy_p50), 0) as base_salary_median,
            ROUND(AVG(cm.total_cash_p50), 0) as total_cash_median,
            ROUND(AVG(cm.total_cash_p50 - cm.base_salary_lfy_p50), 0) as variable_pay
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
        ORDER BY jp.job_function, base_salary_median
        """
        
        df = self.load_data(query)
        if df.empty:
            print("No data found!")
            return
        
        # Separate Finance and Sales data
        finance_df = df[df['job_function'].str.contains('Finance', case=False, na=False)]
        sales_df = df[df['job_function'].str.contains('Sales', case=False, na=False)]
        
        # Create figure with subplots
        fig = plt.figure(figsize=(20, 12))
        gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
        
        # Chart 1: Base Salary Comparison by Level
        ax1 = fig.add_subplot(gs[0, :])
        
        # Get common levels
        common_levels = sorted(set(finance_df['job_level']) & set(sales_df['job_level']), 
                              key=lambda x: finance_df[finance_df['job_level']==x]['base_salary_median'].values[0] if len(finance_df[finance_df['job_level']==x]) > 0 else 0)
        
        x = range(len(common_levels))
        width = 0.35
        
        finance_salaries = [finance_df[finance_df['job_level']==level]['base_salary_median'].values[0] 
                           if len(finance_df[finance_df['job_level']==level]) > 0 else 0 
                           for level in common_levels]
        sales_salaries = [sales_df[sales_df['job_level']==level]['base_salary_median'].values[0] 
                         if len(sales_df[sales_df['job_level']==level]) > 0 else 0 
                         for level in common_levels]
        
        bars1 = ax1.bar([i - width/2 for i in x], finance_salaries, width, 
                       label='Finance', color='#2E86AB', alpha=0.8, edgecolor='black')
        bars2 = ax1.bar([i + width/2 for i in x], sales_salaries, width, 
                       label='Sales', color='#F18F01', alpha=0.8, edgecolor='black')
        
        ax1.set_xlabel('Job Level', fontsize=12)
        ax1.set_ylabel('Median Base Salary ($)', fontsize=12)
        ax1.set_title('Finance vs Sales: Base Salary Comparison by Level', 
                     fontsize=16, fontweight='bold')
        ax1.set_xticks(x)
        ax1.set_xticklabels(common_levels, rotation=45, ha='right')
        ax1.legend(fontsize=12)
        ax1.grid(True, alpha=0.3, axis='y')
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
        
        # Add value labels
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    ax1.text(bar.get_x() + bar.get_width()/2., height + 3000,
                           f'${height/1000:.0f}K', ha='center', va='bottom', fontsize=8)
        
        # Chart 2: Total Cash Comparison (Base + Variable)
        ax2 = fig.add_subplot(gs[1, 0])
        
        finance_total = [finance_df[finance_df['job_level']==level]['total_cash_median'].values[0] 
                        if len(finance_df[finance_df['job_level']==level]) > 0 else 0 
                        for level in common_levels]
        sales_total = [sales_df[sales_df['job_level']==level]['total_cash_median'].values[0] 
                      if len(sales_df[sales_df['job_level']==level]) > 0 else 0 
                      for level in common_levels]
        
        bars3 = ax2.bar([i - width/2 for i in x], finance_total, width, 
                       label='Finance', color='#2E86AB', alpha=0.8, edgecolor='black')
        bars4 = ax2.bar([i + width/2 for i in x], sales_total, width, 
                       label='Sales', color='#F18F01', alpha=0.8, edgecolor='black')
        
        ax2.set_xlabel('Job Level', fontsize=12)
        ax2.set_ylabel('Median Total Cash ($)', fontsize=12)
        ax2.set_title('Total Cash Compensation (Base + Variable)', 
                     fontsize=14, fontweight='bold')
        ax2.set_xticks(x)
        ax2.set_xticklabels(common_levels, rotation=45, ha='right')
        ax2.legend(fontsize=11)
        ax2.grid(True, alpha=0.3, axis='y')
        ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
        
        # Chart 3: Variable Pay Percentage
        ax3 = fig.add_subplot(gs[1, 1])
        
        finance_var_pct = [(finance_df[finance_df['job_level']==level]['variable_pay'].values[0] / 
                           finance_df[finance_df['job_level']==level]['base_salary_median'].values[0] * 100)
                          if len(finance_df[finance_df['job_level']==level]) > 0 and 
                          finance_df[finance_df['job_level']==level]['base_salary_median'].values[0] > 0 
                          else 0 for level in common_levels]
        
        sales_var_pct = [(sales_df[sales_df['job_level']==level]['variable_pay'].values[0] / 
                         sales_df[sales_df['job_level']==level]['base_salary_median'].values[0] * 100)
                        if len(sales_df[sales_df['job_level']==level]) > 0 and 
                        sales_df[sales_df['job_level']==level]['base_salary_median'].values[0] > 0 
                        else 0 for level in common_levels]
        
        bars5 = ax3.bar([i - width/2 for i in x], finance_var_pct, width, 
                       label='Finance', color='#2E86AB', alpha=0.8, edgecolor='black')
        bars6 = ax3.bar([i + width/2 for i in x], sales_var_pct, width, 
                       label='Sales', color='#F18F01', alpha=0.8, edgecolor='black')
        
        ax3.set_xlabel('Job Level', fontsize=12)
        ax3.set_ylabel('Variable Pay (% of Base)', fontsize=12)
        ax3.set_title('Variable Pay as Percentage of Base Salary', 
                     fontsize=14, fontweight='bold')
        ax3.set_xticks(x)
        ax3.set_xticklabels(common_levels, rotation=45, ha='right')
        ax3.legend(fontsize=11)
        ax3.grid(True, alpha=0.3, axis='y')
        
        # Add percentage labels
        for bars in [bars5, bars6]:
            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    ax3.text(bar.get_x() + bar.get_width()/2., height + 1,
                           f'{height:.1f}%', ha='center', va='bottom', fontsize=8)
        
        plt.suptitle('Finance vs Sales Compensation Analysis', 
                    fontsize=18, fontweight='bold', y=0.995)
        
        output_file = self.output_dir / 'finance_vs_sales_comparison.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"\n✅ Chart saved to: {output_file}")
        plt.show()
        
        return str(output_file)
    
    def create_summary_table(self):
        """Create a summary comparison table"""
        query = """
        SELECT 
            jp.job_function,
            COUNT(DISTINCT jp.id) as total_positions,
            SUM(cm.base_salary_lfy_emp_count) as total_employees,
            ROUND(AVG(cm.base_salary_lfy_p50), 0) as avg_base_salary,
            ROUND(AVG(cm.total_cash_p50), 0) as avg_total_cash,
            ROUND(AVG(cm.total_cash_p50 - cm.base_salary_lfy_p50), 0) as avg_variable_pay
        FROM job_positions jp
        JOIN compensation_metrics cm ON jp.id = cm.job_position_id
        WHERE (jp.job_function LIKE '%Finance%' OR jp.job_function LIKE '%Sales%')
          AND cm.base_salary_lfy_p50 IS NOT NULL
          AND cm.total_cash_p50 IS NOT NULL
        GROUP BY jp.job_function
        """
        
        df = self.load_data(query)
        if df.empty:
            print("No summary data found!")
            return
        
        print("\n" + "="*100)
        print("FINANCE VS SALES - OVERALL SUMMARY")
        print("="*100)
        print(f"{'Function':<20} | {'Positions':<10} | {'Employees':<12} | {'Avg Base':<15} | {'Avg Total Cash':<15} | {'Avg Variable':<15}")
        print("-"*100)
        
        for _, row in df.iterrows():
            var_pct = (row['avg_variable_pay'] / row['avg_base_salary'] * 100) if row['avg_base_salary'] > 0 else 0
            print(f"{row['job_function']:<20} | {row['total_positions']:<10} | {row['total_employees']:<12,} | "
                  f"${row['avg_base_salary']:>13,.0f} | ${row['avg_total_cash']:>13,.0f} | "
                  f"${row['avg_variable_pay']:>13,.0f} ({var_pct:.1f}%)")
        
        print("="*100)
        
        # Calculate differences
        if len(df) == 2:
            finance_row = df[df['job_function'].str.contains('Finance', case=False)].iloc[0]
            sales_row = df[df['job_function'].str.contains('Sales', case=False)].iloc[0]
            
            base_diff = finance_row['avg_base_salary'] - sales_row['avg_base_salary']
            total_diff = finance_row['avg_total_cash'] - sales_row['avg_total_cash']
            var_diff = finance_row['avg_variable_pay'] - sales_row['avg_variable_pay']
            
            print("\nKEY DIFFERENCES (Finance - Sales):")
            print(f"  Base Salary:    ${base_diff:>13,.0f} ({base_diff/sales_row['avg_base_salary']*100:+.1f}%)")
            print(f"  Total Cash:     ${total_diff:>13,.0f} ({total_diff/sales_row['avg_total_cash']*100:+.1f}%)")
            print(f"  Variable Pay:   ${var_diff:>13,.0f} ({var_diff/sales_row['avg_variable_pay']*100:+.1f}%)")
            print("="*100)

def main():
    """Create finance vs sales comparison charts"""
    print("📊 Creating Finance vs Sales Comparison Charts...")
    
    charts = FinanceVsSalesCharts()
    
    print("\n1. Creating comparison chart...")
    charts.create_comparison_chart()
    
    print("\n2. Creating summary table...")
    charts.create_summary_table()
    
    print("\n✅ All comparisons created successfully!")

if __name__ == "__main__":
    main()
