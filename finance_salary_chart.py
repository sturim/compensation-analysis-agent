#!/usr/bin/env python3
"""
Finance Salary Visualization
Creates charts specifically for finance compensation data
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

class FinanceSalaryCharts:
    """Create finance salary visualizations"""
    
    def __init__(self, db_path: str = "compensation_data.db"):
        self.db_path = db_path
        self.output_dir = Path("charts")
        self.output_dir.mkdir(exist_ok=True)
        
        # Set up matplotlib for better charts
        plt.rcParams['figure.figsize'] = (14, 10)
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
    
    def create_finance_salary_overview(self):
        """Create comprehensive finance salary overview chart"""
        query = """
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
          AND jp.job_level IN (
              'Entry (P1)', 'Developing (P2)', 'Career (P3)', 'Advanced (P4)',
              'Manager (M3)', 'Expert (P5)', 'Sr Manager (M4)', 'Director (M5)',
              'Principal (P6)', 'Senior Director (M6)'
          )
        GROUP BY jp.job_level
        ORDER BY p50
        """
        
        df = self.load_data(query)
        if df.empty:
            print("No data found!")
            return
        
        # Create figure with subplots
        fig = plt.figure(figsize=(18, 12))
        gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
        
        # Chart 1: Salary Range by Level (Box Plot Style)
        ax1 = fig.add_subplot(gs[0, :])
        x_pos = range(len(df))
        
        # Plot median line
        ax1.plot(x_pos, df['p50'], 'o-', linewidth=2, markersize=10, 
                color='#2E86AB', label='Median (P50)', zorder=3)
        
        # Fill between P25 and P75
        ax1.fill_between(x_pos, df['p25'], df['p75'], alpha=0.3, 
                        color='#2E86AB', label='25th-75th Percentile')
        
        # Add P10 and P90 lines
        ax1.plot(x_pos, df['p10'], '--', linewidth=1.5, color='#A23B72', 
                label='10th Percentile', alpha=0.7)
        ax1.plot(x_pos, df['p90'], '--', linewidth=1.5, color='#F18F01', 
                label='90th Percentile', alpha=0.7)
        
        ax1.set_xticks(x_pos)
        ax1.set_xticklabels(df['job_level'], rotation=45, ha='right')
        ax1.set_ylabel('Base Salary ($)')
        ax1.set_title('Finance Base Salary Distribution by Level', fontsize=16, fontweight='bold')
        ax1.legend(loc='upper left')
        ax1.grid(True, alpha=0.3)
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
        
        # Add median value labels
        for i, (level, median, employees) in enumerate(zip(df['job_level'], df['p50'], df['employees'])):
            ax1.text(i, median + 10000, f'${median:,.0f}\n({employees:,} emp)', 
                    ha='center', va='bottom', fontsize=8, fontweight='bold')
        
        # Chart 2: Career Progression (Median Salary Growth)
        ax2 = fig.add_subplot(gs[1, 0])
        bars = ax2.bar(x_pos, df['p50'], color='#2E86AB', alpha=0.7, edgecolor='black')
        
        # Color code bars by salary range
        colors = plt.cm.viridis(df['p50'] / df['p50'].max())
        for bar, color in zip(bars, colors):
            bar.set_color(color)
        
        ax2.set_xticks(x_pos)
        ax2.set_xticklabels(df['job_level'], rotation=45, ha='right')
        ax2.set_ylabel('Median Base Salary ($)')
        ax2.set_title('Career Progression - Median Salary by Level', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3, axis='y')
        ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
        
        # Add value labels on bars
        for i, (bar, val) in enumerate(zip(bars, df['p50'])):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 5000,
                    f'${val/1000:.0f}K', ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        # Chart 3: Employee Distribution
        ax3 = fig.add_subplot(gs[1, 1])
        bars3 = ax3.barh(range(len(df)), df['employees'], color='#F18F01', alpha=0.7, edgecolor='black')
        
        ax3.set_yticks(range(len(df)))
        ax3.set_yticklabels(df['job_level'])
        ax3.set_xlabel('Number of Employees')
        ax3.set_title('Employee Distribution by Level', fontsize=14, fontweight='bold')
        ax3.grid(True, alpha=0.3, axis='x')
        
        # Add value labels
        for i, (bar, val) in enumerate(zip(bars3, df['employees'])):
            width = bar.get_width()
            ax3.text(width + 50, bar.get_y() + bar.get_height()/2.,
                    f'{val:,}', ha='left', va='center', fontsize=9, fontweight='bold')
        
        plt.suptitle('Finance Compensation Analysis', fontsize=18, fontweight='bold', y=0.995)
        
        output_file = self.output_dir / 'finance_salary_overview.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"\n✅ Chart saved to: {output_file}")
        plt.show()
        
        return str(output_file)
    
    def create_specialization_chart(self):
        """Create chart for top finance specializations"""
        query = """
        SELECT 
            jp.job_focus,
            COUNT(DISTINCT jp.id) as positions,
            SUM(cm.base_salary_lfy_emp_count) as employees,
            ROUND(AVG(cm.base_salary_lfy_p50), 0) as avg_salary
        FROM job_positions jp
        JOIN compensation_metrics cm ON jp.id = cm.job_position_id
        WHERE jp.job_function LIKE '%Finance%'
          AND jp.job_level LIKE '%Manager%'
          AND jp.job_focus IS NOT NULL
          AND jp.job_focus != ''
          AND cm.base_salary_lfy_p50 IS NOT NULL
        GROUP BY jp.job_focus
        HAVING COUNT(DISTINCT jp.id) >= 3
        ORDER BY avg_salary DESC
        LIMIT 15
        """
        
        df = self.load_data(query)
        if df.empty:
            print("No specialization data found!")
            return
        
        # Create horizontal bar chart
        fig, ax = plt.subplots(figsize=(14, 10))
        
        y_pos = range(len(df))
        bars = ax.barh(y_pos, df['avg_salary'], color='#2E86AB', alpha=0.7, edgecolor='black')
        
        # Color gradient based on salary
        colors = plt.cm.RdYlGn(df['avg_salary'] / df['avg_salary'].max())
        for bar, color in zip(bars, colors):
            bar.set_color(color)
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(df['job_focus'])
        ax.set_xlabel('Average Base Salary ($)', fontsize=12)
        ax.set_title('Top Finance Specializations by Salary (Manager Level)', 
                    fontsize=16, fontweight='bold', pad=20)
        ax.grid(True, alpha=0.3, axis='x')
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
        
        # Add value labels
        for i, (bar, salary, employees) in enumerate(zip(bars, df['avg_salary'], df['employees'])):
            width = bar.get_width()
            ax.text(width + 3000, bar.get_y() + bar.get_height()/2.,
                   f'${salary:,.0f}  ({employees} emp)', 
                   ha='left', va='center', fontsize=9, fontweight='bold')
        
        output_file = self.output_dir / 'finance_specializations.png'
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✅ Chart saved to: {output_file}")
        plt.show()
        
        return str(output_file)

def main():
    """Create all finance salary charts"""
    print("📊 Creating Finance Salary Charts...")
    
    charts = FinanceSalaryCharts()
    
    print("\n1. Creating salary overview chart...")
    charts.create_finance_salary_overview()
    
    print("\n2. Creating specialization chart...")
    charts.create_specialization_chart()
    
    print("\n✅ All charts created successfully!")

if __name__ == "__main__":
    main()
