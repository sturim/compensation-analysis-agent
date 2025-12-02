#!/usr/bin/env python3
"""
Test script to demonstrate session context retention
"""

from enhanced_agno_agent import EnhancedAgnoAgent

def test_session_context():
    """Test that sessions maintain separate contexts"""
    
    agent = EnhancedAgnoAgent()
    
    print("="*70)
    print("SESSION CONTEXT RETENTION TEST")
    print("="*70)
    
    # Create two separate sessions
    session1 = agent.create_session()
    session2 = agent.create_session()
    
    print(f"\n✅ Created Session 1: {session1}")
    print(f"✅ Created Session 2: {session2}")
    
    # Session 1: Ask about Engineering
    print("\n" + "="*70)
    print("SESSION 1: Asking about Engineering")
    print("="*70)
    response1 = agent.ask("give me engineering people salaries", session_id=session1)
    print(response1[:300] + "...")
    
    # Session 2: Ask about Sales
    print("\n" + "="*70)
    print("SESSION 2: Asking about Sales")
    print("="*70)
    response2 = agent.ask("give me sales people salaries", session_id=session2)
    print(response2[:300] + "...")
    
    # Session 1: Follow-up (should remember Engineering context)
    print("\n" + "="*70)
    print("SESSION 1: Follow-up question (should use Engineering context)")
    print("="*70)
    response3 = agent.ask("what about managers?", session_id=session1)
    print(response3[:300] + "...")
    
    # Session 2: Follow-up (should remember Sales context)
    print("\n" + "="*70)
    print("SESSION 2: Follow-up question (should use Sales context)")
    print("="*70)
    response4 = agent.ask("what about directors?", session_id=session2)
    print(response4[:300] + "...")
    
    # Show session histories
    print("\n" + "="*70)
    print("SESSION HISTORIES")
    print("="*70)
    
    history1 = agent.get_session_history(session1)
    print(f"\nSession 1 ({session1}):")
    for i, interaction in enumerate(history1, 1):
        print(f"  {i}. {interaction['question']}")
        print(f"     Functions: {interaction['entities'].get('functions', [])}")
    
    history2 = agent.get_session_history(session2)
    print(f"\nSession 2 ({session2}):")
    for i, interaction in enumerate(history2, 1):
        print(f"  {i}. {interaction['question']}")
        print(f"     Functions: {interaction['entities'].get('functions', [])}")
    
    # List all sessions
    print("\n" + "="*70)
    print("ALL SESSIONS")
    print("="*70)
    sessions = agent.list_sessions()
    for session in sessions:
        print(f"\n  Session: {session['session_id']}")
        print(f"  Created: {session['created_at']}")
        print(f"  Messages: {session['message_count']}")
    
    print("\n" + "="*70)
    print("✅ SESSION CONTEXT RETENTION TEST COMPLETE")
    print("="*70)
    print("\nKey Points:")
    print("  • Each session maintains its own conversation history")
    print("  • Context (functions, levels, intent) is session-specific")
    print("  • Follow-up questions use the correct session context")
    print("  • Sessions can be retrieved and listed")


if __name__ == "__main__":
    test_session_context()
