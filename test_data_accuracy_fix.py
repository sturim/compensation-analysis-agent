#!/usr/bin/env python3
"""
Integration tests for data accuracy fix
Tests that the agent correctly returns all available data
"""

import sqlite3
from enhanced_agno_agent import EnhancedAgnoAgent


def test_creative_query_completeness():
    """Test that Creative query returns all records with salary data"""
    print("\n" + "="*70)
    print("TEST: Creative Query Completeness")
    print("="*70)
    
    # Get expected counts from database
    conn = sqlite3.connect('compensation_data.db')
    cursor = conn.cursor()
    
    # Count total Creative positions
    cursor.execute('SELECT COUNT(*) FROM job_positions WHERE job_function = "Creative"')
    total_positions = cursor.fetchone()[0]
    
    # Count Creative positions with salary data (what we should return)
    cursor.execute('''
        SELECT COUNT(*)
        FROM (
            SELECT jp.job_function, jp.job_level
            FROM job_positions jp
            JOIN compensation_metrics cm ON jp.id = cm.job_position_id
            WHERE jp.job_function = "Creative"
                AND cm.base_salary_lfy_p50 IS NOT NULL
                AND cm.base_salary_lfy_p50 > 0
            GROUP BY jp.job_function, jp.job_level
        )
    ''')
    expected_levels = cursor.fetchone()[0]
    
    conn.close()
    
    print(f"\n📊 Database Stats:")
    print(f"   Total Creative positions: {total_positions}")
    print(f"   Levels with salary data: {expected_levels}")
    
    # Query through agent
    agent = EnhancedAgnoAgent(debug=False)
    
    # Directly call _query_database to test
    entities = {'functions': ['Creative'], 'percentile': 'p50'}
    params = {}
    
    result = agent._query_database(entities, params)
    
    print(f"\n📊 Agent Results:")
    print(f"   Status: {result.get('status')}")
    print(f"   Rows returned: {result.get('row_count')}")
    print(f"   Total available: {result.get('total_available')}")
    print(f"   Is limited: {result.get('is_limited')}")
    
    # Verify
    assert result['status'] == 'success', f"Expected success, got {result['status']}"
    assert result['row_count'] == expected_levels, \
        f"Expected {expected_levels} rows, got {result['row_count']}"
    assert result['total_available'] == expected_levels, \
        f"Expected total_available={expected_levels}, got {result['total_available']}"
    
    print(f"\n✅ TEST PASSED: Agent returns all {expected_levels} Creative levels with salary data")
    print(f"   (Note: {total_positions - expected_levels*3} positions lack salary data)")


def test_case_insensitive_matching():
    """Test that case variations return same results through entity parser"""
    print("\n" + "="*70)
    print("TEST: Case-Insensitive Matching (via Entity Parser)")
    print("="*70)
    
    test_queries = [
        'show me salaries for Creative',
        'show me salaries for creative',
        'show me salaries for CREATIVE',
    ]
    
    results = []
    for query in test_queries:
        # Create new agent for each test to avoid connection issues
        agent = EnhancedAgnoAgent(debug=False)
        
        # Extract entities (this is where case-insensitive matching happens)
        entities = agent.entity_parser.extract(query)
        
        # Query database
        result = agent._query_database(entities, {})
        results.append(result)
        print(f"   Query '{query}': extracted={entities['functions']}, rows={result.get('row_count')}")
    
    # All should return same number of rows
    row_counts = [r.get('row_count') for r in results]
    assert len(set(row_counts)) == 1, \
        f"Case variations returned different results: {row_counts}"
    
    print(f"\n✅ TEST PASSED: All case variations return {row_counts[0]} rows")


def test_no_limit_by_default():
    """Test that queries don't have arbitrary limits by default"""
    print("\n" + "="*70)
    print("TEST: No Arbitrary Limits")
    print("="*70)
    
    agent = EnhancedAgnoAgent(debug=False)
    
    # Query Engineering (which has many levels)
    entities = {'functions': ['Engineering'], 'percentile': 'p50'}
    result = agent._query_database(entities, {})
    
    print(f"   Engineering query returned: {result.get('row_count')} rows")
    print(f"   Total available: {result.get('total_available')}")
    print(f"   Is limited: {result.get('is_limited')}")
    
    # Should not be limited
    assert not result.get('is_limited'), "Query should not be limited by default"
    assert result.get('row_count') == result.get('total_available'), \
        "Should return all available rows when no limit specified"
    
    print(f"\n✅ TEST PASSED: No arbitrary limit applied")


def test_validation_completeness():
    """Test that validation detects completeness correctly"""
    print("\n" + "="*70)
    print("TEST: Validation Completeness")
    print("="*70)
    
    agent = EnhancedAgnoAgent(debug=False)
    
    entities = {'functions': ['Creative'], 'percentile': 'p50'}
    result = agent._query_database(entities, {})
    
    validation = result.get('validation', {})
    
    print(f"   Validation complete: {validation.get('is_complete')}")
    print(f"   Discrepancies: {validation.get('discrepancies')}")
    print(f"   Warnings: {validation.get('warnings')}")
    
    # Should be complete (no discrepancies)
    assert validation.get('is_complete'), \
        f"Validation should be complete, but found discrepancies: {validation.get('discrepancies')}"
    
    print(f"\n✅ TEST PASSED: Validation confirms data completeness")


def test_transparency_with_limit():
    """Test that limited results show total available"""
    print("\n" + "="*70)
    print("TEST: Transparency with LIMIT")
    print("="*70)
    
    agent = EnhancedAgnoAgent(debug=False)
    
    # Query with explicit limit
    entities = {'functions': ['Engineering'], 'percentile': 'p50'}
    result = agent._query_database(entities, {}, limit=5)
    
    print(f"   Rows returned: {result.get('row_count')}")
    print(f"   Total available: {result.get('total_available')}")
    print(f"   Is limited: {result.get('is_limited')}")
    print(f"   Warning: {result.get('warning')}")
    
    # Should indicate limitation
    assert result.get('is_limited'), "Should be marked as limited"
    assert result.get('row_count') <= 5, "Should respect limit"
    assert result.get('total_available') > result.get('row_count'), \
        "Should show more records available"
    assert 'warning' in result, "Should include warning about limitation"
    
    print(f"\n✅ TEST PASSED: Limited results show transparency")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("DATA ACCURACY FIX - INTEGRATION TESTS")
    print("="*70)
    
    try:
        test_creative_query_completeness()
        test_case_insensitive_matching()
        test_no_limit_by_default()
        test_validation_completeness()
        test_transparency_with_limit()
        
        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED")
        print("="*70)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
