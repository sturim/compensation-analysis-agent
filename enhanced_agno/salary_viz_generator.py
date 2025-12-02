#!/usr/bin/env python3
"""
Salary Visualization Generator - Comprehensive 3-panel salary charts
"""

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from pathlib import Path
from typing import Optional
import warnings
warnings.filterwarnings('ignore')


class SalaryVizGenerator:
    """Generates comprehensive salary visualizations with 3-panel layouts"""
    
    def __init__(self, db_path: str = "compensation_data.db", output_dir: str = "charts"):
        """
        Initialize salary visualization generator.
        
        Args:
            db_path: Path to SQLite database
            output_dir: Directory to save charts
        """
        self.db_path = db_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Professional styling
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        plt.rcParams['figure.figsize'] = (18, 12)
        plt.rcParams['font.size'] = 10
    
    def generate_salary_overview(self, job_function: str) -> Optional[str]:
        """
        Generate comprehensive 3-panel salary overview.
        
        Args:
            job_function: Job function to visualize (e.g., 'Engineering')
            
        Returns:
            Path to saved chart or None if failed
        """
        try:
            # Fetch data with percentiles
            df = self._fetch_salary_data(job_function)
            
            if df.empty:
                print(f"⚠️  No data found for {job_function}")
                return None
            
            # Create 3-panel layout
            fig = plt.figure(figsize=(18, 12))
            gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.3, wspace=0.3)
            
            # Panel 1: Distribution (top, full width)
            ax1 = fig.add_subplot(gs[0, :])
            self._create_distribution_panel(ax1, df, job_function)
            
            # Panel 2: Progression (bottom left)
            ax2 = fig.add_subplot(gs[1, 0])
            self._create_progression_panel(ax2, df)
            
            # Panel 3: Employee Distribution (bottom right)
            ax3 = fig.add_subplot(gs[1, 1])
            self._create_employee_panel(ax3, df)
            
            # Save
            filename = f"{job_function.lower().replace(' ', '_')}_salary_overview.png"
            filepath = self.output_dir / filename
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"✅ Chart saved to: {filepath}")
            return str(filepath)
            
        except Exception as e:
            print(f"❌ Visualization failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def generate_comparison_chart(self, function1: str, function2: str) -> Optional[str]:
        """
        Generate side-by-side comparison between two functions.
        
        Args:
            function1: First job function
            function2: Second job function
            
        Returns:
            Path to saved chart or None if failed
        """
        try:
            # Fetch data for both functions
            df1 = self._fetch_salary_data(function1)
            df2 = self._fetch_salary_data(function2)
            
            if df1.empty or df2.empty:
                print(f"⚠️  Insufficient data for comparison")
                return None
            
            # Create comparison chart
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))
            
            # Left: Function 1
            x_pos1 = range(len(df1))
            ax1.bar(x_pos1, df1['p50'], color='#2E86AB', alpha=0.7)
            ax1.set_xticks(x_pos1)
            ax1.set_xticklabels(df1['job_level'], rotation=45, ha='right')
            ax1.set_ylabel('Median Base Salary ($)')
            ax1.set_title(f'{function1} Salary by Level', fontsize=14, fontweight='bold')
            ax1.grid(True, alpha=0.3, axis='y')
            ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
            
            # Right: Function 2
            x_pos2 = range(len(df2))
            ax2.bar(x_pos2, df2['p50'], color='#F18F01', alpha=0.7)
            ax2.set_xticks(x_pos2)
            ax2.set_xticklabels(df2['job_level'], rotation=45, ha='right')
            ax2.set_ylabel('Median Base Salary ($)')
            ax2.set_title(f'{function2} Salary by Level', fontsize=14, fontweight='bold')
            ax2.grid(True, alpha=0.3, axis='y')
            ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
            
            # Save
            filename = f"comparison_{function1.lower().replace(' ', '_')}_{function2.lower().replace(' ', '_')}.png"
            filepath = self.output_dir / filename
            plt.tight_layout()
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"✅ Comparison chart saved to: {filepath}")
            return str(filepath)
            
        except Exception as e:
            print(f"❌ Comparison visualization failed: {e}")
            return None
    
    def _fetch_salary_data(self, job_function: str) -> pd.DataFrame:
        """
        Fetch salary data with all percentiles from database.
        
        Args:
            job_function: Job function to query
            
        Returns:
            DataFrame with percentile data
        """
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
        WHERE jp.job_function LIKE ?
          AND cm.base_salary_lfy_p50 IS NOT NULL
          AND jp.job_level IN (
              'Entry (P1)', 'Developing (P2)', 'Career (P3)', 'Advanced (P4)',
              'Manager (M3)', 'Expert (P5)', 'Sr Manager (M4)', 'Director (M5)',
              'Principal (P6)', 'Senior Director (M6)'
          )
        GROUP BY jp.job_level
        ORDER BY p50
        """
        
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            df = pd.read_sql_query(query, conn, params=[f'%{job_function}%'])
            conn.close()
            return df
        except Exception as e:
            print(f"❌ Database query failed: {e}")
            return pd.DataFrame()
    
    def _create_distribution_panel(self, ax, df: pd.DataFrame, job_function: str):
        """
        Create top panel: Salary distribution with percentile bands.
        
        Args:
            ax: Matplotlib axes object
            df: DataFrame with salary data
            job_function: Job function name for title
        """
        x_pos = range(len(df))
        
        # Plot percentile bands
        ax.fill_between(x_pos, df['p25'], df['p75'], 
                        alpha=0.3, color='#2E86AB', label='25th-75th Percentile')
        
        # Plot P10 and P90 lines
        ax.plot(x_pos, df['p10'], '--', linewidth=1.5, 
               color='#A23B72', label='10th Percentile', alpha=0.7)
        ax.plot(x_pos, df['p90'], '--', linewidth=1.5, 
               color='#F18F01', label='90th Percentile', alpha=0.7)
        
        # Plot median line
        ax.plot(x_pos, df['p50'], 'o-', linewidth=2, markersize=10,
               color='#2E86AB', label='Median (P50)', zorder=3)
        
        # Add labels with salary and employee count
        for i, (idx, row) in enumerate(df.iterrows()):
            ax.text(i, row['p50'] + (df['p90'].max() - df['p10'].min()) * 0.02, 
                   f"${row['p50']:,.0f}\n({row['employees']:,} emp)",
                   ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        # Styling
        ax.set_xticks(x_pos)
        ax.set_xticklabels(df['job_level'], rotation=45, ha='right')
        ax.set_ylabel('Base Salary ($)', fontsize=12, fontweight='bold')
        ax.set_title(f'{job_function} Base Salary Distribution by Level',
                    fontsize=16, fontweight='bold', pad=20)
        ax.legend(loc='upper left', fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
    
    def _create_progression_panel(self, ax, df: pd.DataFrame):
        """
        Create bottom left panel: Career progression with gradient colors.
        
        Args:
            ax: Matplotlib axes object
            df: DataFrame with salary data
        """
        x_pos = range(len(df))
        bars = ax.bar(x_pos, df['p50'], alpha=0.7)
        
        # Apply gradient colors
        colors = plt.cm.viridis(df['p50'] / df['p50'].max())
        for bar, color in zip(bars, colors):
            bar.set_color(color)
        
        # Add value labels
        for i, (idx, row) in enumerate(df.iterrows()):
            ax.text(i, row['p50'], f"${row['p50']:,.0f}",
                   ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        # Styling
        ax.set_xticks(x_pos)
        ax.set_xticklabels(df['job_level'], rotation=45, ha='right')
        ax.set_ylabel('Median Base Salary ($)', fontsize=11, fontweight='bold')
        ax.set_title('Career Progression - Median Salary by Level',
                    fontsize=14, fontweight='bold', pad=15)
        ax.grid(True, alpha=0.3, axis='y')
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
    
    def _create_employee_panel(self, ax, df: pd.DataFrame):
        """
        Create bottom right panel: Employee distribution by level.
        
        Args:
            ax: Matplotlib axes object
            df: DataFrame with salary data
        """
        y_pos = range(len(df))
        
        # Horizontal bars
        ax.barh(y_pos, df['employees'], color='#F18F01', alpha=0.7)
        
        # Add value labels
        for i, (idx, row) in enumerate(df.iterrows()):
            ax.text(row['employees'], i, f" {row['employees']:,}",
                   ha='left', va='center', fontsize=9, fontweight='bold')
        
        # Styling
        ax.set_yticks(y_pos)
        ax.set_yticklabels(df['job_level'])
        ax.set_xlabel('Number of Employees', fontsize=11, fontweight='bold')
        ax.set_title('Employee Distribution by Level',
                    fontsize=14, fontweight='bold', pad=15)
        ax.grid(True, alpha=0.3, axis='x')
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x):,}'))
