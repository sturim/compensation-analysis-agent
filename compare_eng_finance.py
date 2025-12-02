#!/usr/bin/env python3
"""
Compare Engineering salaries with Finance
"""

from enhanced_agno_agent import EnhancedAgnoAgent

print("\n" + "="*70)
print("COMPARING ENGINEERING VS FINANCE SALARIES")
print("="*70)

# Create agent
agent = EnhancedAgnoAgent(debug=False)

# Compare Engineering and Finance
response = agent.ask("compare Engineering salaries with Finance")

print(response)

print("\n" + "="*70)
print("✅ Comparison complete!")
print("📊 Check charts/ folder for the visualization")
print("="*70)
