#!/usr/bin/env python3
"""
Generate Job Architecture Report
Creates a visual job leveling matrix showing career progression across tracks
"""

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.table import Table
import numpy as np

def extract_level_number(level_str):
    """Extract numeric level from job level string"""
    # Map common patterns to numeric levels
    level_map = {
        'Entry': 1,
        'Developing': 2,
        'Career': 3,
        'Advanced': 4,
        'Expert': 5,
        'Manager': 6,
        'Sr Manager': 7,
        'Director': 8,
        'Senior Director': 9,
        'Principal': 6,
        'Executive 1': 11,
        'Executive 2': 12,
        'Executive 3': 13,
        'Executive 4': 14,
    }
    
    for key, value in level_map.items():
        if key in level_str:
            return value
    
    # Try to extract P/M/E numbers
    if 'P1' in level_str or 'F1' in level_str or 'S1' in level_str:
        return 1
    elif 'P2' in level_str or 'F2' in level_str or 'S2' in level_str:
        return 2
    elif 'P3' in level_str or 'F3' in level_str or 'S3' in level_str:
        return 3
    elif 'P4' in level_str or 'F4' in level_str or 'S4' in level_str:
        return 4
    elif 'P5' in level_str or 'F5' in level_str or 'S5' in level_str:
        return 5
    elif 'P6' in level_str or 'F6' in level_str:
        return 6
    elif 'P7' in level_str or 'F7' in level_str:
        return 7
    elif 'M1' in level_str:
        return 5
    elif 'M2' in level_str:
        return 6
    elif 'M3' in level_str:
        return 7
    elif 'M4' in level_str:
        return 8
    elif 'M5' in level_str:
        return 9
    elif 'M6' in level_str:
        return 10
    elif 'E1' in level_str:
        return 11
    elif 'E2' in level_str:
        return 12
    elif 'E3' in level_str:
        return 13
    elif 'E4' in level_str:
        return 14
    
    return 0

def categorize_track(level_str):
    """Categorize job level into track (Executive, Management, Professional, Support)"""
    level_lower = level_str.lower()
    
    if 'executive' in level_lower or 'c-suite' in level_lower or 'svp' in level_lower or 'vp' in level_lower:
        return 'Executive'
    elif 'manager' in level_lower or 'director' in level_lower or level_str.startswith('M'):
        return 'Management'
    elif 'support' in level_lower or level_str.startswith('S'):
        return 'Support'
    else:
        return 'Professional'

def generate_job_architecture_report():
    """Generate job architecture matrix report"""
    
    # Connect to database
    conn = sqlite3.connect('compensation_data.db')
    
    # Query all job levels
    query = """
    SELECT DISTINCT 
        jp.job_level,
        jp.job_function
    FROM job_positions jp
    WHERE jp.job_level NOT LIKE '%Roll-Up%'
    ORDER BY jp.job_level
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Add level number and track
    df['level_num'] = df['job_level'].apply(extract_level_number)
    df['track'] = df['job_level'].apply(categorize_track)
    
    # Filter out invalid levels
    df = df[df['level_num'] > 0]
    
    # Create matrix structure
    max_level = 14
    tracks = ['Executive', 'Management', 'Professional', 'Support']
    
    # Create figure
    fig, ax = plt.subplots(figsize=(16, 10))
    ax.axis('tight')
    ax.axis('off')
    
    # Create table data
    table_data = []
    
    # Header row
    header = ['Level']
    for track in tracks:
        header.extend([track, 'Code'])
    table_data.append(header)
    
    # Data rows
    for level in range(max_level, 0, -1):
        row = [str(level)]
        
        for track in tracks:
            # Find matching job levels
            matches = df[(df['level_num'] == level) & (df['track'] == track)]
            
            if len(matches) > 0:
                # Get the most common job level name
                job_level = matches['job_level'].iloc[0]
                
                # Simplify the name
                if 'Executive' in job_level:
                    if '4' in job_level:
                        company_name = 'C-Suite'
                        code = 'E4'
                    elif '3' in job_level:
                        company_name = 'SVP'
                        code = 'E3'
                    elif '2' in job_level:
                        company_name = 'VP'
                        code = 'E2'
                    else:
                        company_name = 'VP'
                        code = 'E1'
                elif 'Director' in job_level:
                    if 'Senior' in job_level or 'Sr' in job_level:
                        company_name = f'{track} - {level}'
                        code = f'M{level-4}'
                    else:
                        company_name = f'{track} - {level}'
                        code = f'M{level-3}'
                elif 'Manager' in job_level:
                    if 'Sr' in job_level:
                        company_name = f'{track} - {level}'
                        code = f'M{level-3}'
                    else:
                        company_name = f'{track} - {level}'
                        code = f'M{level-2}'
                elif 'Professional' in job_level or 'P' in job_level:
                    company_name = f'{track} - {level}'
                    code = f'P{level}'
                elif 'Support' in job_level or 'S' in job_level:
                    company_name = f'{track} - {level}'
                    code = f'S{level}'
                else:
                    company_name = f'{track} - {level}'
                    code = f'L{level}'
                
                row.extend([company_name, code])
            else:
                row.extend(['', ''])
        
        table_data.append(row)
    
    # Create table
    table = ax.table(cellText=table_data, cellLoc='center', loc='center',
                     colWidths=[0.08] + [0.115, 0.08] * 4)
    
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 2)
    
    # Style the table
    # Header row - orange background
    for i in range(len(header)):
        cell = table[(0, i)]
        cell.set_facecolor('#FFA500')
        cell.set_text_props(weight='bold', color='white')
    
    # Track headers - lighter orange
    for i in [1, 3, 5, 7]:
        cell = table[(0, i)]
        cell.set_facecolor('#FFB84D')
    
    # Data cells
    for i in range(1, len(table_data)):
        for j in range(len(header)):
            cell = table[(i, j)]
            if j == 0:  # Level column
                cell.set_facecolor('#F0F0F0')
            elif j % 2 == 1:  # Company name columns
                if table_data[i][j]:  # If not empty
                    cell.set_facecolor('#FFFACD')
            else:  # Code columns
                if table_data[i][j]:  # If not empty
                    cell.set_facecolor('#F5F5DC')
    
    plt.title('Job Architecture Matrix\nCareer Progression Across Tracks', 
              fontsize=16, fontweight='bold', pad=20)
    
    # Save
    plt.tight_layout()
    plt.savefig('charts/job_architecture_matrix.png', dpi=300, bbox_inches='tight')
    print("✅ Job architecture matrix saved to: charts/job_architecture_matrix.png")
    
    plt.close()

if __name__ == "__main__":
    print("="*70)
    print("GENERATING JOB ARCHITECTURE REPORT")
    print("="*70)
    generate_job_architecture_report()
    print("="*70)
