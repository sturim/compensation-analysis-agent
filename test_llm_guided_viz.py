#!/usr/bin/env python3
"""
Test LLM-guided visualization - demonstrates intelligent chart selection
"""

from enhanced_agno_agent import EnhancedAgnoAgent

print("\n" + "="*70)
print("TESTING LLM-GUIDED VISUALIZATION")
print("="*70)
print("\nThe agent will now use Claude to intelligently choose the best")
print("chart type based on your data and query!")
print("="*70)

# Create agent
agent = EnhancedAgnoAgent(debug=False)

# Test 1: Simple query - LLM should recommend appropriate viz
print("\n\n1️⃣  TEST: Simple Engineering query")
print("-" * 70)
response1 = agent.ask("show me Engineering salaries")

# Test 2: Comparison - LLM should detect and recommend comparison chart
print("\n\n2️⃣  TEST: Comparison query")
print("-" * 70)
response2 = agent.ask("compare Sales and Finance")

# Test 3: Complex query - LLM should analyze and recommend best approach
print("\n\n3️⃣  TEST: Complex query")
print("-" * 70)
response3 = agent.ask("visualize Marketing compensation across all levels")

print("\n" + "="*70)
print("✅ LLM-GUIDED VISUALIZATION TEST COMPLETE")
print("="*70)
print("\n📊 Check the charts/ folder to see the intelligently generated visualizations!")
print("\nThe LLM analyzed your data and query to choose the optimal chart type")
print("for clear, insightful, and visually pleasing representation.")
