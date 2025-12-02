#!/usr/bin/env python3
from enhanced_agno_agent import EnhancedAgnoAgent

agent = EnhancedAgnoAgent(debug=False)
print("\n" + "="*70)
print("Testing LLM-Guided Visualization")
print("="*70)
response = agent.ask("show me Engineering salaries")
print(response)
