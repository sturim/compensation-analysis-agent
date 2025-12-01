#!/usr/bin/env python3
"""
Demo script showing Enhanced Agno Agent capabilities
"""

from enhanced_agno_agent import EnhancedAgnoAgent
import time


def demo():
    """Run a demo showing key features"""
    print("="*70)
    print("ENHANCED AGNO AGENT - DEMO")
    print("="*70)
    print("\nThis demo shows the key improvements:")
    print("  1. Fast entity extraction")
    print("  2. Intelligent LLM planning")
    print("  3. Auto-visualization")
    print("  4. Conversation memory")
    print("\n" + "="*70)
    
    agent = EnhancedAgnoAgent()
    
    # Demo 1: Simple query with visualization
    print("\n\n📊 DEMO 1: Simple Query with Auto-Visualization")
    print("-"*70)
    response = agent.ask("What's the salary for Engineering Managers?")
    print("\n" + response)
    time.sleep(2)
    
    # Demo 2: Comparison
    print("\n\n📊 DEMO 2: Comparison")
    print("-"*70)
    response = agent.ask("Compare engineering and sales salaries")
    print("\n" + response)
    time.sleep(2)
    
    # Demo 3: Context awareness
    print("\n\n📊 DEMO 3: Context Awareness (Reference Resolution)")
    print("-"*70)
    print("Previous question mentioned Engineering and Sales...")
    print("Now asking: 'Compare them to finance'")
    response = agent.ask("Compare them to finance")
    print("\n" + response)
    time.sleep(2)
    
    # Demo 4: Show conversation history
    print("\n\n📊 DEMO 4: Conversation History")
    print("-"*70)
    history = agent.conversation.get_recent_history(3)
    for i, interaction in enumerate(history, 1):
        print(f"\n{i}. Q: {interaction['question']}")
        print(f"   Functions: {interaction['entities'].get('functions', [])}")
        print(f"   Intent: {interaction['entities'].get('intent')}")
    
    print("\n\n" + "="*70)
    print("DEMO COMPLETE!")
    print("="*70)
    print("\nKey Takeaways:")
    print("  ✅ Fast entity extraction (<1ms)")
    print("  ✅ LLM used only for planning and insights")
    print("  ✅ Charts created automatically")
    print("  ✅ Conversation context maintained")
    print("\nTry it yourself:")
    print("  python3 enhanced_agno_agent.py -i")
    print("="*70)


if __name__ == "__main__":
    demo()
