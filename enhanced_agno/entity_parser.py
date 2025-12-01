#!/usr/bin/env python3
"""
Entity Parser - Fast, deterministic entity extraction
No LLM needed for simple parsing
"""

import re
from typing import Dict, Optional, List, Any


class EntityParser:
    """Fast entity extraction using regex and keyword matching"""
    
    def __init__(self):
        # Job function patterns
        self.functions = {
            'engineering': ['engineering', 'engineer', 'software', 'technical'],
            'finance': ['finance', 'financial', 'accounting', 'treasury'],
            'sales': ['sales', 'selling', 'revenue'],
            'marketing': ['marketing', 'brand', 'advertising'],
            'human resources': ['hr', 'human resources', 'people', 'talent'],
            'legal': ['legal', 'counsel', 'compliance'],
            'operations': ['operations', 'ops'],
        }
        
        # Job level patterns
        self.levels = {
            'Entry (P1)': ['entry', 'p1', 'junior'],
            'Developing (P2)': ['developing', 'p2'],
            'Career (P3)': ['career', 'p3', 'mid-level'],
            'Advanced (P4)': ['advanced', 'p4', 'senior'],
            'Expert (P5)': ['expert', 'p5', 'principal'],
            'Manager (M3)': ['manager', 'm3', 'mgr'],
            'Sr Manager (M4)': ['sr manager', 'senior manager', 'm4'],
            'Director (M5)': ['director', 'm5'],
            'Senior Director (M6)': ['senior director', 'sr director', 'm6'],
            'Principal (P6)': ['principal', 'p6'],
        }
        
        # Intent patterns
        self.intents = {
            'compare': ['compare', 'versus', 'vs', 'difference between'],
            'visualize': ['show', 'display', 'chart', 'graph', 'plot', 'visualize'],
            'analyze': ['analyze', 'analysis', 'breakdown', 'examine'],
            'progression': ['progression', 'career path', 'growth', 'advancement'],
            'query': ['what', 'how much', 'salary', 'compensation'],
        }
    
    def extract(self, question: str) -> Dict[str, Any]:
        """
        Extract entities from question using fast pattern matching.
        
        Args:
            question: User's question
            
        Returns:
            Dictionary with extracted entities
        """
        question_lower = question.lower()
        
        return {
            'functions': self._extract_functions(question_lower),
            'levels': self._extract_levels(question_lower),
            'intent': self._extract_intent(question_lower),
            'metrics': self._extract_metrics(question_lower),
            'percentile': self._extract_percentile(question_lower),
            'original_question': question
        }
    
    def _extract_functions(self, text: str) -> List[str]:
        """Extract job functions from text"""
        found = []
        for function, keywords in self.functions.items():
            for keyword in keywords:
                # Use word boundaries to avoid false matches
                # e.g., "people" in "engineering people" shouldn't match HR
                if keyword in ['hr', 'ops']:
                    # Short keywords need exact match or word boundary
                    import re
                    if re.search(r'\b' + keyword + r'\b', text):
                        found.append(function.title())
                        break
                elif keyword == 'people':
                    # Only match "people" if it's part of "people operations" or "people team"
                    if 'people operations' in text or 'people team' in text or 'people department' in text:
                        found.append(function.title())
                        break
                elif keyword in text:
                    found.append(function.title())
                    break
        return found
    
    def _extract_levels(self, text: str) -> List[str]:
        """Extract job levels from text"""
        found = []
        for level, keywords in self.levels.items():
            if any(keyword in text for keyword in keywords):
                found.append(level)
        return found
    
    def _extract_intent(self, text: str) -> str:
        """Extract primary intent from text"""
        for intent, keywords in self.intents.items():
            if any(keyword in text for keyword in keywords):
                return intent
        return 'query'  # default
    
    def _extract_metrics(self, text: str) -> List[str]:
        """Extract metrics of interest"""
        metrics = []
        if any(word in text for word in ['salary', 'base', 'compensation']):
            metrics.append('base_salary')
        if any(word in text for word in ['total', 'total comp', 'total cash']):
            metrics.append('total_comp')
        if any(word in text for word in ['variable', 'bonus', 'incentive']):
            metrics.append('variable_pay')
        if any(word in text for word in ['employee', 'count', 'how many']):
            metrics.append('employee_count')
        
        return metrics if metrics else ['base_salary']  # default
    
    def _extract_percentile(self, text: str) -> Optional[str]:
        """Extract percentile from text"""
        percentile_map = {
            '10th': 'p10',
            '25th': 'p25',
            '50th': 'p50',
            'median': 'p50',
            '75th': 'p75',
            '90th': 'p90',
        }
        
        for keyword, percentile in percentile_map.items():
            if keyword in text:
                return percentile
        
        return 'p50'  # default to median


if __name__ == "__main__":
    # Test the parser
    parser = EntityParser()
    
    test_questions = [
        "What's the salary for Finance Managers?",
        "Compare engineering and sales at director level",
        "Show me career progression in HR",
        "What's the 90th percentile for senior engineers?",
    ]
    
    print("Entity Parser Test\n" + "="*60)
    for q in test_questions:
        result = parser.extract(q)
        print(f"\nQ: {q}")
        print(f"Functions: {result['functions']}")
        print(f"Levels: {result['levels']}")
        print(f"Intent: {result['intent']}")
        print(f"Metrics: {result['metrics']}")
