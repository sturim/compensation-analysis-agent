#!/usr/bin/env python3
"""
Query Sales data and generate visualization
"""

from enhanced_agno_agent import EnhancedAgnoAgent

# Create agent
agent = EnhancedAgnoAgent(debug=False)

# Query Sales data
print("\n" + "="*70)
print("QUERYING SALES DATA")
print("="*70)

response = agent.ask("show me Sales salaries with visualization")

print(response)
