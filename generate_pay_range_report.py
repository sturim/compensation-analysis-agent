#!/usr/bin/env python3
"""
Generate Pay Range Report with Market Data Comparison
Shows Radford/Pave data points and watershed pay range (Min, Midpoint, Max)
"""

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from matplotlib.patches import FancyBboxPatch, Circle, FancyArrowPatch

def generate_pay_range_report(job_function='Engineering', job_level='Manager (M3)'):
    """
    Generate a pay range report showing market data and pay range structure
    
    Args:
        job_function: Job function to analyze
        job_level: Job level to analyze
    """
    
    # Connect to database
    conn = sqlite3.connect('compensation_data.db')
    
    # Query salary data for the specific job
    query = """
    SELECT 
        jp.job_function,
        jp.job_level,
        cm.base_salary_lfy_p10,
        cm.base_salary_lfy_p25,
        cm.base_salary_lfy_p50,
        cm.base_salary_lfy_p75,
        cm.base_salary_lfy_p90,
        cm.base_salary_lfy_emp_count
    FROM job_positions jp
    JOIN compensation_metrics cm ON jp.id = cm.job_position_id
    WHERE jp.job_function = ?
        AND jp.job_level = ?
        AND cm.base_salary_lfy_p50 IS NOT NULL
    """
    
    df = pd.read_sql_query(query, conn, params=[job_function, job_level])
    conn.close()
    
    if df.empty:
        print(f"⚠️  No data found for {job_function} - {job_level}")
        return
    
    # Get percentile data
    p10 = df['base_salary_lfy_p10'].iloc[0]
    p25 = df['base_salary_lfy_p25'].iloc[0]
    p50 = df['base_salary_lfy_p50'].iloc[0]
    p75 = df['base_salary_lfy_p75'].iloc[0]
    p90 = df['base_salary_lfy_p90'].iloc[0]
    
    # Calculate pay range (typical structure: 80% to 120% of midpoint)
    midpoint = p50
    min_range = midpoint * 0.80
    max_range = midpoint * 1.20
    
    # Create figure with two subplots
    fig = plt.figure(figsize=(16, 6))
    
    # Left subplot: Radford/Pave Data (Market Data Points)
    ax1 = plt.subplot(1, 2, 1)
    
    # Create box plot style visualization
    positions = [1]
    
    # Plot percentile ranges
    ax1.plot([1, 1], [p10, p90], 'o-', color='#D2691E', linewidth=2, markersize=8, label='P10-P90 Range')
    ax1.plot([1, 1], [p25, p75], 'o-', color='#FFA500', linewidth=4, markersize=10, label='P25-P75 Range')
    
    # Highlight P50 (median)
    ax1.plot(1, p50, 'o', color='#FF6347', markersize=15, label='P50 (Median)', zorder=5)
    ax1.add_patch(Circle((1, p50), 0.08, color='#FF6347', fill=False, linewidth=2, zorder=6))
    
    # Add percentile labels
    offset = 0.15
    ax1.text(1 + offset, p10, f'P10: ${p10:,.0f}', va='center', fontsize=9)
    ax1.text(1 + offset, p25, f'P25: ${p25:,.0f}', va='center', fontsize=9)
    ax1.text(1 + offset, p50, f'P50: ${p50:,.0f}', va='center', fontsize=10, fontweight='bold')
    ax1.text(1 + offset, p75, f'P75: ${p75:,.0f}', va='center', fontsize=9)
    ax1.text(1 + offset, p90, f'P90: ${p90:,.0f}', va='center', fontsize=9)
    
    # Add legend bar at bottom
    legend_colors = ['#8B4513', '#A0522D', '#CD853F', '#DEB887', '#F5DEB3', '#FFE4B5']
    legend_labels = ['P10', '20th', '30th', '40th', '50th', 'Average']
    
    legend_y = p10 - (p90 - p10) * 0.15
    bar_width = 0.4
    bar_height = (p90 - p10) * 0.05
    
    for i, (color, label) in enumerate(zip(legend_colors, legend_labels)):
        x_pos = 0.7 + (i * bar_width / len(legend_colors))
        rect = FancyBboxPatch((x_pos, legend_y), bar_width / len(legend_colors), bar_height,
                              boxstyle="round,pad=0.01", facecolor=color, edgecolor='black', linewidth=0.5)
        ax1.add_patch(rect)
        ax1.text(x_pos + bar_width / (2 * len(legend_colors)), legend_y - bar_height * 1.5, 
                label, ha='center', fontsize=7)
    
    ax1.set_xlim(0.5, 1.8)
    ax1.set_ylim(p10 - (p90 - p10) * 0.25, p90 + (p90 - p10) * 0.1)
    ax1.set_xticks([])
    ax1.set_ylabel('Salary ($)', fontsize=12, fontweight='bold')
    ax1.set_title('Radford/Pave Data\n', fontsize=14, fontweight='bold')
    ax1.grid(axis='y', alpha=0.3, linestyle='--')
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.spines['bottom'].set_visible(False)
    
    # Right subplot: Watershed Pay Range
    ax2 = plt.subplot(1, 2, 2)
    
    # Draw the curve connecting min-midpoint-max
    x_curve = np.linspace(0, 2, 100)
    y_curve = -0.5 * (x_curve - 1)**2 + 1  # Parabola centered at x=1
    
    # Scale to salary range
    y_scaled = min_range + (y_curve - y_curve.min()) / (y_curve.max() - y_curve.min()) * (max_range - min_range) * 0.3
    y_scaled = y_scaled + (midpoint - y_scaled[50])  # Center on midpoint
    
    ax2.plot(x_curve, y_scaled, '-', color='#DC143C', linewidth=3, zorder=1)
    
    # Draw the pay range bar
    bar_y = midpoint - (max_range - min_range) * 0.15
    
    # Main range line
    ax2.plot([0.5, 2.5], [bar_y, bar_y], '-', color='#333', linewidth=3, zorder=2)
    
    # Min marker
    ax2.plot(0.5, bar_y, '|', color='#FFA500', markersize=30, markeredgewidth=4, zorder=3)
    ax2.text(0.5, bar_y - (max_range - min_range) * 0.08, 'Min', ha='center', fontsize=11, fontweight='bold')
    ax2.text(0.5, bar_y - (max_range - min_range) * 0.13, f'${min_range:,.0f}', ha='center', fontsize=9)
    
    # Midpoint marker (circle)
    ax2.add_patch(Circle((1.5, bar_y), (max_range - min_range) * 0.08, 
                         color='#FFA500', fill=True, zorder=4))
    ax2.add_patch(Circle((1.5, bar_y), (max_range - min_range) * 0.08, 
                         color='#DC143C', fill=False, linewidth=2, zorder=5))
    ax2.text(1.5, bar_y - (max_range - min_range) * 0.08, 'Midpoint', ha='center', fontsize=11, fontweight='bold')
    ax2.text(1.5, bar_y - (max_range - min_range) * 0.13, f'${midpoint:,.0f}', ha='center', fontsize=9)
    
    # Max marker
    ax2.plot(2.5, bar_y, '|', color='#FFA500', markersize=30, markeredgewidth=4, zorder=3)
    ax2.text(2.5, bar_y - (max_range - min_range) * 0.08, 'Max', ha='center', fontsize=11, fontweight='bold')
    ax2.text(2.5, bar_y - (max_range - min_range) * 0.13, f'${max_range:,.0f}', ha='center', fontsize=9)
    
    ax2.set_xlim(0, 3)
    ax2.set_ylim(min_range - (max_range - min_range) * 0.3, max_range + (max_range - min_range) * 0.2)
    ax2.set_xticks([])
    ax2.set_yticks([])
    ax2.set_title('Watershed Pay\nRange', fontsize=14, fontweight='bold')
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.spines['bottom'].set_visible(False)
    ax2.spines['left'].set_visible(False)
    
    # Overall title
    fig.suptitle(f'Pay Range Analysis: {job_function} - {job_level}', 
                 fontsize=16, fontweight='bold', y=0.98)
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    
    # Save
    filename = f'charts/pay_range_{job_function.lower().replace(" ", "_")}_{job_level.replace(" ", "_").replace("(", "").replace(")", "")}.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✅ Pay range report saved to: {filename}")
    
    plt.close()

if __name__ == "__main__":
    print("="*70)
    print("GENERATING PAY RANGE REPORT")
    print("="*70)
    
    # Generate reports for different roles
    roles = [
        ('Engineering', 'Manager (M3)'),
        ('Finance', 'Manager (M3)'),
        ('Engineering', 'Director (M5)'),
    ]
    
    for job_function, job_level in roles:
        print(f"\nGenerating report for {job_function} - {job_level}...")
        generate_pay_range_report(job_function, job_level)
    
    print("\n" + "="*70)
    print("✅ All reports generated!")
    print("="*70)
