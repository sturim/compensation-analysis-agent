#!/usr/bin/env python3
"""
Run the Enhanced Agno Agent with LLM-guided visualization
"""

from enhanced_agno_agent import EnhancedAgnoAgent

print("\n" + "="*70)
print("🤖 ENHANCED AGNO AGENT - LLM-Guided Visualization")
print("="*70)

# Create agent
agent = EnhancedAgnoAgent(debug=False)

print("\n" + "="*70)
print("Ready! The agent will use Claude AI to intelligently choose")
print("the best chart type for your data.")
print("="*70)

# Example query
print("\n📊 Querying: 'show me Engineering salaries'\n")
response = agent.ask("show me Engineering salaries")

print(response)

print("\n" + "="*70)
print("✅ Complete! Check the charts/ folder for the visualization.")
print("="*70)
