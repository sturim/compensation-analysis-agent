#!/usr/bin/env python3
"""
Test that comparison queries work without the 'Interaction' object error
"""

from enhanced_agno_agent import EnhancedAgnoAgent

print("\n" + "="*70)
print("TESTING COMPARISON FIX")
print("="*70)

try:
    # Create agent
    agent = EnhancedAgnoAgent(debug=False)
    
    # Test 1: Simple query first
    print("\n1. Testing simple query...")
    response1 = agent.ask("show me Engineering salaries")
    print("✅ Simple query works")
    
    # Test 2: Comparison query (this was failing before)
    print("\n2. Testing comparison query...")
    response2 = agent.ask("compare Engineering vs Sales")
    print("✅ Comparison query works!")
    
    # Test 3: Another query to build history
    print("\n3. Testing follow-up query...")
    response3 = agent.ask("show me Finance salaries")
    print("✅ Follow-up query works")
    
    print("\n" + "="*70)
    print("✅ ALL TESTS PASSED - Fix successful!")
    print("="*70)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
