#!/usr/bin/env python3
"""
Test script to verify all enhanced agent components
"""

import sys
import os
sys.path.insert(0, 'enhanced_agno')

from analysis_engine import AnalysisEngine
from result_formatter import ResultFormatter
from suggestion_engine import SuggestionEngine

# Test data
test_results = {
    'status': 'success',
    'row_count': 3,
    'data': [
        {'job_function': 'Engineering', 'job_level': 'Entry (P1)', 'avg_salary': 105000, 'employees': 3368, 'positions': 18},
        {'job_function': 'Engineering', 'job_level': 'Manager (M3)', 'avg_salary': 219000, 'employees': 8133, 'positions': 26},
        {'job_function': 'Engineering', 'job_level': 'Director (M5)', 'avg_salary': 271000, 'employees': 7468, 'positions': 26},
    ],
    'chart_path': 'charts/test.png'
}

print("="*70)
print("TESTING ENHANCED COMPONENTS")
print("="*70)

# Test 1: Analysis Engine
print("\n1. Testing Analysis Engine...")
engine = AnalysisEngine()
analyzed = engine.analyze(test_results.copy(), 'query')

print(f"   ✅ Summary: {analyzed.get('summary', 'MISSING')[:80]}...")
print(f"   ✅ Insights: {len(analyzed.get('insights', []))} insights generated")
if analyzed.get('insights'):
    for i, insight in enumerate(analyzed['insights'][:2], 1):
        print(f"      {i}. {insight[:60]}...")

# Test 2: Suggestion Engine
print("\n2. Testing Suggestion Engine...")
suggestion_engine = SuggestionEngine()
suggestions = suggestion_engine.generate_suggestions(
    "What's the salary for Engineering?",
    analyzed,
    'query'
)
print(f"   ✅ Generated {len(suggestions)} suggestions")
for i, suggestion in enumerate(suggestions, 1):
    print(f"      {i}. {suggestion}")

# Test 3: Result Formatter
print("\n3. Testing Result Formatter...")
formatter = ResultFormatter()
formatted = formatter.format_response(
    "What's the salary for Engineering?",
    analyzed,
    "Engineering salaries range from $105K to $271K across different levels."
)

print("   ✅ Formatted output:")
print(formatted)

print("\n" + "="*70)
print("ALL TESTS COMPLETE")
print("="*70)
