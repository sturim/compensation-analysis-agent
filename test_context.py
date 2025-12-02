#!/usr/bin/env python3
"""
Test script to demonstrate context awareness
"""

from enhanced_agno_agent import EnhancedAgnoAgent

# Create agent once
agent = EnhancedAgnoAgent(debug=False)

print("\n" + "="*70)
print("TESTING CONTEXT AWARENESS")
print("="*70)

# First question
print("\n1️⃣ First question: What are the engineering salaries?")
response1 = agent.ask("What are the engineering salaries?")
print(response1)

# Second question with reference
print("\n" + "="*70)
print("\n2️⃣ Second question: Compare them with finance")
response2 = agent.ask("compare them with finance")
print(response2)

# Third question with reference
print("\n" + "="*70)
print("\n3️⃣ Third question: Show them visually")
response3 = agent.ask("show them visually")
print(response3)

print("\n" + "="*70)
print("✅ Context test complete!")
print("="*70)
