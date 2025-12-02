#!/usr/bin/env python3
"""
Visualization Engine - Auto-generates professional charts
"""

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, List, Dict, Any
import warnings
warnings.filterwarnings('ignore')

# Try to import comprehensive visualization
try:
    from enhanced_agno.salary_viz_generator import SalaryVizGenerator
    SALARY_VIZ_AVAILABLE = True
except ImportError:
    SALARY_VIZ_AVAILABLE = False

# Try to import visualization advisor
try:
    from enhanced_agno.visualization_advisor import VisualizationAdvisor
    ADVISOR_AVAILABLE = True
except ImportError:
    ADVISOR_AVAILABLE = False


class VisualizationEngine:
    """Creates professional visualizations automatically with LLM guidance"""
    
    def __init__(self, output_dir: str = "charts", db_path: str = "compensation_data.db", claude_client=None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.db_path = db_path
        self.claude_client = claude_client
        
        # Initialize visualization advisor if available
        if ADVISOR_AVAILABLE and claude_client:
            self.advisor = VisualizationAdvisor(claude_client)
            print("   📊 LLM-Guided Visualization: ✅")
        else:
            self.advisor = None
        
        # Initialize comprehensive viz if available
        if SALARY_VIZ_AVAILABLE:
            self.salary_viz = SalaryVizGenerator(db_path, str(self.output_dir))
        else:
            self.salary_viz = None
        
        # Set professional style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        plt.rcParams['figure.figsize'] = (12, 8)
        plt.rcParams['font.size'] = 10
    
    def create_salary_overview(self, job_function: str) -> Optional[str]:
        """
        Create comprehensive 3-panel salary overview.
        
        Args:
            job_function: Job function to visualize
            
        Returns:
            Path to saved chart or None
        """
        if self.salary_viz:
            return self.salary_viz.generate_salary_overview(job_function)
        else:
            print("⚠️  Comprehensive visualization not available, using basic chart")
            return None
    
    def create_comparison_chart(self, function1: str, function2: str) -> Optional[str]:
        """
        Create comparison chart between two functions.
        
        Args:
            function1: First job function
            function2: Second job function
            
        Returns:
            Path to saved chart or None
        """
        if self.salary_viz:
            return self.salary_viz.generate_comparison_chart(function1, function2)
        else:
            print("⚠️  Comparison visualization not available")
            return None
    
    def auto_visualize(self, data: pd.DataFrame, analysis_type: str, 
                      title: str, query: str = "", entities: Dict[str, Any] = None) -> Optional[str]:
        """
        Automatically create appropriate visualization using LLM guidance.
        
        Args:
            data: DataFrame with results
            analysis_type: Type of analysis (comparison, distribution, progression)
            title: Chart title
            query: Original user query (for LLM context)
            entities: Extracted entities (for LLM context)
            
        Returns:
            Path to saved chart or None
        """
        try:
            # Use LLM advisor if available
            if self.advisor and len(data) > 0:
                recommendation = self.advisor.recommend_visualization(
                    data, query, entities or {}
                )
                
                print(f"   🤖 LLM Recommendation: {recommendation['chart_type']}")
                print(f"   💡 Reasoning: {recommendation['reasoning']}")
                
                # Use recommended chart type
                chart_type = recommendation['chart_type']
                title = recommendation.get('title', title)
                
                # Map recommendation to chart method
                if chart_type == 'comprehensive_overview':
                    # Try to create comprehensive overview if available
                    return self._create_comprehensive_chart(data, title, recommendation)
                elif chart_type == 'comparison':
                    return self._create_comparison_chart(data, title)
                elif chart_type == 'distribution':
                    return self._create_distribution_chart(data, title)
                elif chart_type == 'progression':
                    return self._create_progression_chart(data, title)
                else:  # simple_bar or fallback
                    return self._create_bar_chart(data, title)
            
            # Fallback to rule-based if no advisor
            if analysis_type == 'comparison':
                return self._create_comparison_chart(data, title)
            elif analysis_type == 'distribution':
                return self._create_distribution_chart(data, title)
            elif analysis_type == 'progression':
                return self._create_progression_chart(data, title)
            else:
                return self._create_bar_chart(data, title)
                
        except Exception as e:
            print(f"⚠️  Visualization failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _create_comprehensive_chart(self, data: pd.DataFrame, title: str, 
                                    recommendation: Dict[str, Any]) -> Optional[str]:
        """Create comprehensive multi-panel chart based on LLM recommendation"""
        # Check if we have the required data
        has_percentiles = all(col in data.columns for col in ['p10', 'p25', 'p50', 'p75', 'p90'])
        has_employees = 'employees' in data.columns
        
        if not (has_percentiles and has_employees):
            print("   ⚠️  Insufficient data for comprehensive chart, using distribution instead")
            return self._create_distribution_chart(data, title)
        
        # Create 3-panel layout
        fig = plt.figure(figsize=(18, 12))
        gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.3, wspace=0.3)
        
        # Panel 1: Distribution with percentile bands (top, full width)
        ax1 = fig.add_subplot(gs[0, :])
        self._plot_percentile_distribution(ax1, data, title)
        
        # Panel 2: Career progression (bottom left)
        ax2 = fig.add_subplot(gs[1, 0])
        self._plot_career_progression(ax2, data)
        
        # Panel 3: Employee distribution (bottom right)
        ax3 = fig.add_subplot(gs[1, 1])
        self._plot_employee_distribution(ax3, data)
        
        # Save
        filename = f"comprehensive_{title.replace(' ', '_').lower()}.png"
        filepath = self.output_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return str(filepath)
    
    def _plot_percentile_distribution(self, ax, data: pd.DataFrame, title: str):
        """Plot distribution panel with percentile bands"""
        x_pos = range(len(data))
        
        # Plot percentile bands
        ax.fill_between(x_pos, data['p25'], data['p75'], 
                        alpha=0.3, color='#2E86AB', label='25th-75th Percentile')
        ax.plot(x_pos, data['p10'], '--', linewidth=1.5, 
               color='#A23B72', label='10th Percentile', alpha=0.7)
        ax.plot(x_pos, data['p90'], '--', linewidth=1.5, 
               color='#F18F01', label='90th Percentile', alpha=0.7)
        
        # Plot median line
        ax.plot(x_pos, data['p50'], 'o-', linewidth=2, markersize=10,
               color='#2E86AB', label='Median (P50)', zorder=3)
        
        # Add labels
        for i, row in data.iterrows():
            salary = row['p50']
            emp_count = row.get('employees', 0)
            ax.text(i, salary + (data['p90'].max() - data['p10'].min()) * 0.03,
                   f"${salary:,.0f}\n({emp_count:,} emp)",
                   ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        # Styling
        ax.set_xticks(x_pos)
        ax.set_xticklabels(data['job_level'] if 'job_level' in data.columns else data.iloc[:, 0],
                          rotation=45, ha='right')
        ax.set_ylabel('Base Salary ($)', fontsize=12, fontweight='bold')
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        ax.legend(loc='upper left', framealpha=0.9)
        ax.grid(True, alpha=0.3)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
    
    def _plot_career_progression(self, ax, data: pd.DataFrame):
        """Plot career progression panel"""
        x_pos = range(len(data))
        salary_col = 'p50' if 'p50' in data.columns else 'avg_salary'
        
        bars = ax.bar(x_pos, data[salary_col], alpha=0.8)
        
        # Apply gradient colors
        colors = plt.cm.viridis(data[salary_col] / data[salary_col].max())
        for bar, color in zip(bars, colors):
            bar.set_color(color)
        
        # Add value labels
        for i, val in enumerate(data[salary_col]):
            ax.text(i, val, f'${val:,.0f}',
                   ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        # Styling
        ax.set_xticks(x_pos)
        ax.set_xticklabels(data['job_level'] if 'job_level' in data.columns else data.iloc[:, 0],
                          rotation=45, ha='right')
        ax.set_ylabel('Median Salary ($)', fontsize=11, fontweight='bold')
        ax.set_title('Career Progression', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
    
    def _plot_employee_distribution(self, ax, data: pd.DataFrame):
        """Plot employee distribution panel"""
        y_pos = range(len(data))
        
        ax.barh(y_pos, data['employees'], color='#F18F01', alpha=0.8)
        
        # Add value labels
        for i, val in enumerate(data['employees']):
            ax.text(val, i, f' {val:,}',
                   ha='left', va='center', fontsize=9, fontweight='bold')
        
        # Styling
        ax.set_yticks(y_pos)
        ax.set_yticklabels(data['job_level'] if 'job_level' in data.columns else data.iloc[:, 0])
        ax.set_xlabel('Number of Employees', fontsize=11, fontweight='bold')
        ax.set_title('Employee Distribution', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='x')
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x):,}'))
    
    def _create_comparison_chart(self, data: pd.DataFrame, title: str) -> str:
        """Create side-by-side comparison chart"""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        x = range(len(data))
        width = 0.35
        
        # Assume data has columns for two groups
        cols = data.columns.tolist()
        if len(cols) >= 3:  # index + 2 value columns
            ax.bar([i - width/2 for i in x], data[cols[1]], width, 
                  label=cols[1], alpha=0.8)
            ax.bar([i + width/2 for i in x], data[cols[2]], width, 
                  label=cols[2], alpha=0.8)
        
        ax.set_xlabel('Category')
        ax.set_ylabel('Value ($)')
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(data[cols[0]], rotation=45, ha='right')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        filename = f"comparison_{title.replace(' ', '_').lower()}.png"
        filepath = self.output_dir / filename
        plt.tight_layout()
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(filepath)

    def _create_distribution_chart(self, data: pd.DataFrame, title: str) -> str:
        """Create distribution chart with percentiles"""
        fig, ax = plt.subplots(figsize=(14, 8))
        
        x_pos = range(len(data))
        
        # Plot median line
        if 'median' in data.columns or 'p50' in data.columns:
            median_col = 'median' if 'median' in data.columns else 'p50'
            ax.plot(x_pos, data[median_col], 'o-', linewidth=2, 
                   markersize=10, color='#2E86AB', label='Median')
            
            # Add value labels
            for i, val in enumerate(data[median_col]):
                ax.text(i, val + 5000, f'${val:,.0f}', 
                       ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        ax.set_xticks(x_pos)
        ax.set_xticklabels(data.iloc[:, 0], rotation=45, ha='right')
        ax.set_ylabel('Salary ($)')
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
        
        filename = f"distribution_{title.replace(' ', '_').lower()}.png"
        filepath = self.output_dir / filename
        plt.tight_layout()
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(filepath)
    
    def _create_progression_chart(self, data: pd.DataFrame, title: str) -> str:
        """Create career progression chart"""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        x_pos = range(len(data))
        bars = ax.bar(x_pos, data.iloc[:, 1], color='#2E86AB', alpha=0.7)
        
        # Color gradient
        colors = plt.cm.viridis(data.iloc[:, 1] / data.iloc[:, 1].max())
        for bar, color in zip(bars, colors):
            bar.set_color(color)
        
        ax.set_xticks(x_pos)
        ax.set_xticklabels(data.iloc[:, 0], rotation=45, ha='right')
        ax.set_ylabel('Salary ($)')
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')
        
        filename = f"progression_{title.replace(' ', '_').lower()}.png"
        filepath = self.output_dir / filename
        plt.tight_layout()
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(filepath)
    
    def _create_bar_chart(self, data: pd.DataFrame, title: str) -> str:
        """Create simple bar chart"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        ax.bar(range(len(data)), data.iloc[:, 1], color='#2E86AB', alpha=0.7)
        ax.set_xticks(range(len(data)))
        ax.set_xticklabels(data.iloc[:, 0], rotation=45, ha='right')
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')
        
        filename = f"chart_{title.replace(' ', '_').lower()}.png"
        filepath = self.output_dir / filename
        plt.tight_layout()
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(filepath)
