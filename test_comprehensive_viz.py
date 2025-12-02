#!/usr/bin/env python3
"""
Test comprehensive visualization system
"""

from enhanced_agno_agent import EnhancedAgnoAgent
import os

print("\n" + "="*70)
print("TESTING COMPREHENSIVE VISUALIZATION SYSTEM")
print("="*70)

# Initialize agent
agent = EnhancedAgnoAgent(debug=False)

# Test 1: Engineering Overview
print("\n📊 Test 1: Engineering Salary Overview")
print("-" * 70)
response = agent.ask("show me Engineering salaries with visualization")
print(response)

# Test 2: Finance Overview
print("\n📊 Test 2: Finance Salary Overview")
print("-" * 70)
response = agent.ask("visualize Finance salaries")
print(response)

# Test 3: Comparison
print("\n📊 Test 3: Engineering vs Finance Comparison")
print("-" * 70)
response = agent.ask("compare Engineering vs Finance salaries")
print(response)

# Check generated files
print("\n" + "="*70)
print("GENERATED FILES")
print("="*70)

charts_dir = "charts"
expected_files = [
    "engineering_salary_overview.png",
    "finance_salary_overview.png",
    "comparison_engineering_finance.png"
]

for filename in expected_files:
    filepath = os.path.join(charts_dir, filename)
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
        print(f"✅ {filename} ({size:,} bytes)")
    else:
        print(f"❌ {filename} (not found)")

print("\n" + "="*70)
print("✅ TESTING COMPLETE")
print("="*70)
print("\nOpen the charts/ directory to view the generated visualizations!")
