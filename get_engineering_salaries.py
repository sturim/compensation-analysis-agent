#!/usr/bin/env python3
"""
Get Engineering salaries using enhanced_agno_agent
"""

from enhanced_agno_agent import EnhancedAgnoAgent

# Create agent
agent = EnhancedAgnoAgent(debug=False)

# Get Engineering salaries
response = agent.ask("show me Engineering salaries")

print(response)
