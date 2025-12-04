#!/usr/bin/env python3
"""
Generate Pay Transparency Range & Range Width Report
Creates a stacked visualization showing pay ranges across multiple job levels.
Shows Min, Midpoint, Max markers for each level with range width percentages.
This is specifically for pay transparency and range width analysis, NOT salary overviews.
"""

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def generate_pay_transparency_report(job_function='Engineering'):
    """
    Generate pay transparency report showing range width across levels
    
    Args:
        job_function: Job function to analyze
    """
    
    # Connect to database
    conn = sqlite3.connect('compensation_data.db')
    
    # Query salary data for standard career levels (no roll-ups)
    query = """
    SELECT 
        jp.job_level,
        cm.base_salary_lfy_p50 as midpoint
    FROM job_positions jp
    JOIN compensation_metrics cm ON jp.id = cm.job_position_id
    WHERE jp.job_function = ?
        AND jp.job_level NOT LIKE '%Roll-Up%'
        AND jp.job_level NOT LIKE '%Executive%'
        AND cm.base_salary_lfy_p50 IS NOT NULL
    ORDER BY cm.base_salary_lfy_p50 ASC
    LIMIT 10
    """
    
    df = pd.read_sql_query(query, conn, params=[job_function])
    conn.close()
    
    if df.empty:
        print(f"⚠️  No data found for {job_function}")
        return
    
    # Calculate pay ranges (80% to 120% of midpoint)
    df['min'] = df['midpoint'] * 0.80
    df['max'] = df['midpoint'] * 1.20
    df['range_width'] = ((df['max'] - df['min']) / df['midpoint'] * 100).round(0)
    
    # Create figure
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # Plot each level's pay range
    num_levels = len(df)
    
    for idx, row in df.iterrows():
        level_num = idx + 1
        min_sal = row['min']
        mid_sal = row['midpoint']
        max_sal = row['max']
        
        # Draw the range bar
        ax.plot([min_sal, max_sal], [level_num, level_num], 
                color='#8B4513', linewidth=3, solid_capstyle='butt')
        
        # Min marker
        ax.plot(min_sal, level_num, '|', color='#FFA500', 
                markersize=20, markeredgewidth=4)
        
        # Midpoint marker
        ax.plot(mid_sal, level_num, 'o', color='#FFA500', 
                markersize=12, markeredgewidth=2, markerfacecolor='#FFA500')
        
        # Max marker
        ax.plot(max_sal, level_num, '|', color='#FFA500', 
                markersize=20, markeredgewidth=4)
        
        # Add range width annotation for some levels
        if idx == 0 or idx == num_levels - 1 or idx == num_levels // 2:
            range_pct = row['range_width']
            ax.text(max_sal + (max_sal - min_sal) * 0.05, level_num, 
                   f'+{range_pct/2:.0f}%', va='center', fontsize=9, color='#666')
            ax.text(min_sal - (max_sal - min_sal) * 0.05, level_num, 
                   f'-{range_pct/2:.0f}%', va='center', ha='right', fontsize=9, color='#666')
    
    # Add labels at top
    top_level = num_levels + 0.5
    sample_min = df['min'].iloc[-1]
    sample_mid = df['midpoint'].iloc[-1]
    sample_max = df['max'].iloc[-1]
    
    ax.text(sample_min, top_level, 'Min', ha='center', fontsize=12, fontweight='bold')
    ax.text(sample_mid, top_level, 'Midpoint', ha='center', fontsize=12, fontweight='bold')
    ax.text(sample_max, top_level, 'Max', ha='center', fontsize=12, fontweight='bold')
    
    # Add compa ratio annotations
    if num_levels >= 4:
        mid_level = num_levels // 2
        mid_row = df.iloc[mid_level]
        ax.text(mid_row['min'] + (mid_row['midpoint'] - mid_row['min']) / 2, 
               mid_level - 0.3, '-10%', ha='center', fontsize=8, color='#666')
        ax.text(mid_row['midpoint'] + (mid_row['max'] - mid_row['midpoint']) / 2, 
               mid_level - 0.3, '+10%', ha='center', fontsize=8, color='#666')
    
    # Formatting
    ax.set_ylim(0.5, num_levels + 1)
    ax.set_xlim(df['min'].min() * 0.95, df['max'].max() * 1.08)
    
    ax.set_yticks(range(1, num_levels + 1))
    ax.set_yticklabels(range(1, num_levels + 1))
    ax.set_ylabel('Level', fontsize=12, fontweight='bold')
    ax.set_xlabel('Salary ($)', fontsize=12, fontweight='bold')
    
    # Format x-axis as currency
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
    
    ax.grid(axis='x', alpha=0.3, linestyle='--')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Title and description
    title_text = 'Pay transparency range & Range width'
    ax.text(0.02, 0.98, title_text, transform=ax.transAxes, 
           fontsize=16, fontweight='bold', va='top')
    
    desc_text = (
        '• Range of probable pay for every job. Should be where most newly hired/promoted EEs should be positioned at\n'
        '• Example: minimum of band to 5% above mid (80/90% - 105% compa ratio)\n'
        '• Reserve the higher end of range for internal progression'
    )
    ax.text(0.02, 0.92, desc_text, transform=ax.transAxes, 
           fontsize=10, va='top', linespacing=1.5)
    
    # Sample range at bottom
    sample_text = f'sample range: Min= {df["min"].iloc[0]/1000:.0f}K  Midpt= {df["midpoint"].iloc[0]/1000:.0f}K  Max= {df["max"].iloc[0]/1000:.0f}K'
    ax.text(0.5, -0.08, sample_text, transform=ax.transAxes, 
           fontsize=10, ha='center', color='#DC143C', style='italic')
    
    plt.tight_layout()
    
    # Save
    filename = f'charts/pay_transparency_{job_function.lower().replace(" ", "_")}.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✅ Pay transparency report saved to: {filename}")
    
    plt.close()

if __name__ == "__main__":
    print("="*70)
    print("GENERATING PAY TRANSPARENCY REPORT")
    print("="*70)
    
    # Generate reports for different functions
    functions = ['Engineering', 'Finance', 'Sales']
    
    for function in functions:
        print(f"\nGenerating report for {function}...")
        generate_pay_transparency_report(function)
    
    print("\n" + "="*70)
    print("✅ All reports generated!")
    print("="*70)
