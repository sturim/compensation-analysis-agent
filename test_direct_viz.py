#!/usr/bin/env python3
"""
Direct test of visualization generator
"""

from enhanced_agno.salary_viz_generator import SalaryVizGenerator
import os

print("\n" + "="*70)
print("DIRECT VISUALIZATION TEST")
print("="*70)

# Initialize generator
viz = SalaryVizGenerator()

# Test 1: Engineering Overview
print("\n📊 Generating Engineering Salary Overview...")
chart_path = viz.generate_salary_overview("Engineering")

if chart_path and os.path.exists(chart_path):
    size = os.path.getsize(chart_path)
    print(f"   File: {chart_path}")
    print(f"   Size: {size:,} bytes ({size/1024/1024:.2f} MB)")
else:
    print("   ❌ Failed to generate chart")

# Test 2: Finance Overview
print("\n📊 Generating Finance Salary Overview...")
chart_path = viz.generate_salary_overview("Finance")

if chart_path and os.path.exists(chart_path):
    size = os.path.getsize(chart_path)
    print(f"   File: {chart_path}")
    print(f"   Size: {size:,} bytes ({size/1024/1024:.2f} MB)")
else:
    print("   ❌ Failed to generate chart")

# Test 3: Comparison
print("\n📊 Generating Engineering vs Finance Comparison...")
chart_path = viz.generate_comparison_chart("Engineering", "Finance")

if chart_path and os.path.exists(chart_path):
    size = os.path.getsize(chart_path)
    print(f"   File: {chart_path}")
    print(f"   Size: {size:,} bytes ({size/1024/1024:.2f} MB)")
else:
    print("   ❌ Failed to generate chart")

print("\n" + "="*70)
print("✅ DIRECT TEST COMPLETE")
print("="*70)
