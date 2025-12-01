#!/usr/bin/env python3
"""
Visualization Engine - Auto-generates professional charts
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from pathlib import Path
from typing import Optional, List
import warnings
warnings.filterwarnings('ignore')


class VisualizationEngine:
    """Creates professional visualizations automatically"""
    
    def __init__(self, output_dir: str = "charts"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Set professional style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        plt.rcParams['figure.figsize'] = (12, 8)
        plt.rcParams['font.size'] = 10
    
    def auto_visualize(self, data: pd.DataFrame, analysis_type: str, 
                      title: str) -> Optional[str]:
        """
        Automatically create appropriate visualization.
        
        Args:
            data: DataFrame with results
            analysis_type: Type of analysis (comparison, distribution, progression)
            title: Chart title
            
        Returns:
            Path to saved chart or None
        """
        try:
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
            return None
    
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
