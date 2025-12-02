#!/usr/bin/env python3
"""
Create data visualization comparing Engineering and Finance salaries
"""

from enhanced_agno_agent import EnhancedAgnoAgent

print("\n" + "="*70)
print("GENERATING VISUALIZATION: ENGINEERING VS FINANCE")
print("="*70)

# Create agent
agent = EnhancedAgnoAgent(debug=False)

# Request comparison with visualization
response = agent.ask("compare Engineering and Finance salaries with visualization")

print(response)

print("\n" + "="*70)
print("✅ Visualization complete!")
print("📊 Check the charts/ folder for the comparison chart")
print("="*70)
