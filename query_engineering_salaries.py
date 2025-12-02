#!/usr/bin/env python3
"""
Query Engineering salaries and display graphs
"""

from enhanced_agno_agent import EnhancedAgnoAgent

# Create agent
agent = EnhancedAgnoAgent(debug=False)

# Query Engineering salaries
print("\n" + "="*70)
print("QUERYING ENGINEERING SALARIES")
print("="*70)

response = agent.ask("What are the salaries for Engineering?")

print(response)
