#!/usr/bin/env python3
"""
Entity Parser - Fast, deterministic entity extraction
No LLM needed for simple parsing
"""

import re
import sqlite3
from typing import Dict, Optional, List, Any
from difflib import get_close_matches


class EntityParser:
    """Fast entity extraction using regex and keyword matching"""
    
    def __init__(self, db_path: str = 'compensation_data.db'):
        """
        Initialize entity parser.
        
        Args:
            db_path: Path to database for validation
        """
        self.db_path = db_path
        self._db_job_functions = None  # Cache for database job functions
        self._db_job_modules = None  # Cache for database job modules
        
        # Job function patterns (fallback for when DB not available)
        self.functions = {
            'engineering': ['engineering', 'engineer', 'software', 'technical'],
            'finance': ['finance', 'financial', 'accounting', 'treasury'],
            'sales': ['sales', 'selling', 'revenue'],
            'marketing': ['marketing', 'brand', 'advertising'],
            'human resources': ['hr', 'human resources', 'people', 'talent'],
            'legal': ['legal', 'counsel', 'compliance'],
            'operations': ['operations', 'ops'],
            'creative': ['creative', 'design', 'designer'],
            'infrastructure': ['infrastructure', 'infra'],
        }
        
        # Job module patterns
        self.modules = {
            'infrastructure': ['infrastructure', 'infra'],
            'technology': ['technology', 'tech'],
        }
        
        # Job level patterns
        self.levels = {
            'Entry (P1)': ['entry', 'p1', 'junior'],
            'Developing (P2)': ['developing', 'p2'],
            'Career (P3)': ['career', 'p3', 'mid-level'],
            'Advanced (P4)': ['advanced', 'p4'],
            'Expert (P5)': ['expert', 'p5', 'principal'],
            'Supervisor (M1)': ['supervisor', 'm1'],
            'Sr Supervisor (M2)': ['sr supervisor', 'senior supervisor', 'm2'],
            'Manager (M3)': ['manager', 'm3', 'mgr'],
            'Sr Manager (M4)': ['sr manager', 'senior manager', 'm4'],
            'Director (M5)': ['director', 'm5'],
            'Senior Director (M6)': ['senior director', 'sr director', 'm6'],
            'Principal (P6)': ['principal', 'p6'],
        }
        
        # Intent patterns
        self.intents = {
            'create_ranges': ['create salary range', 'create range', 'build range', 'salary structure', 'pay structure', 'range structure'],
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
        
        entities = {
            'functions': self._extract_functions(question_lower),
            'modules': self._extract_modules(question_lower),
            'levels': self._extract_levels(question_lower),
            'intent': self._extract_intent(question_lower),
            'metrics': self._extract_metrics(question_lower),
            'percentile': self._extract_percentile(question_lower),
            'spread': self._extract_spread(question_lower),
            'original_question': question
        }
        
        # Validate against database
        entities = self.validate_against_db(entities)
        
        return entities
    
    def _extract_functions(self, text: str) -> List[str]:
        """Extract job functions from text"""
        found = []
        
        # First, check for common multi-word phrases that should be matched as aliases
        # This prevents "Business Operations" from matching just "Operations"
        phrase_aliases = {
            'business operations': 'Corporate & Business Services',
            'business services': 'Corporate & Business Services',
            'corporate services': 'Corporate & Business Services',
        }
        
        for phrase, alias in phrase_aliases.items():
            if phrase in text:
                found.append(alias)
                # Remove the phrase from text to prevent partial matches
                text = text.replace(phrase, '')
        
        # Then, try to match against actual database values
        # Sort by length (longest first) to match longer names before shorter ones
        db_functions = self._load_db_job_functions()
        if db_functions:
            # Sort by length descending to match longer names first
            sorted_functions = sorted(db_functions, key=len, reverse=True)
            for db_func in sorted_functions:
                # Check if the database function name appears in the text
                if db_func.lower() in text and db_func not in found:
                    found.append(db_func)
                    # Remove matched function to prevent overlapping matches
                    text = text.replace(db_func.lower(), '')
        
        # If no DB matches, fall back to keyword matching
        if not found:
            for function, keywords in self.functions.items():
                for keyword in keywords:
                    # Use word boundaries to avoid false matches
                    # e.g., "people" in "engineering people" shouldn't match HR
                    if keyword in ['hr', 'ops']:
                        # Short keywords need exact match or word boundary
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
    
    def _extract_spread(self, text: str) -> Optional[float]:
        """Extract spread percentage from text (e.g., '20%' -> 0.20)"""
        import re
        
        # Look for patterns like "20%", "spread 20", "20 percent"
        patterns = [
            r'spread[:\s]+(\d+)%?',
            r'(\d+)%\s+spread',
            r'(\d+)\s*percent\s+spread',
            r'spread[:\s]+(\d+)\s*percent',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return float(match.group(1)) / 100.0
        
        return None  # No spread specified
    
    def _load_db_job_functions(self) -> List[str]:
        """Load distinct job functions from database"""
        if self._db_job_functions is not None:
            return self._db_job_functions
        
        try:
            conn = sqlite3.connect(self.db_path, timeout=5)
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT job_function FROM job_positions ORDER BY job_function")
            self._db_job_functions = [row[0] for row in cursor.fetchall()]
            conn.close()
            return self._db_job_functions
        except Exception as e:
            print(f"⚠️  Could not load job functions from database: {e}")
            return []
    
    def _load_db_job_modules(self) -> List[str]:
        """Load distinct job modules from database"""
        if self._db_job_modules is not None:
            return self._db_job_modules
        
        try:
            conn = sqlite3.connect(self.db_path, timeout=5)
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT job_module FROM job_positions WHERE job_module IS NOT NULL ORDER BY job_module")
            self._db_job_modules = [row[0] for row in cursor.fetchall()]
            conn.close()
            return self._db_job_modules
        except Exception as e:
            print(f"⚠️  Could not load job modules from database: {e}")
            return []
    
    def _extract_modules(self, text: str) -> List[str]:
        """Extract job modules from text"""
        found = []
        
        # First, try to match against actual database values
        db_modules = self._load_db_job_modules()
        if db_modules:
            for db_module in db_modules:
                # Check if the database module name appears in the text
                if db_module.lower() in text:
                    found.append(db_module)
        
        # If no DB matches, fall back to keyword matching
        if not found:
            for module, keywords in self.modules.items():
                for keyword in keywords:
                    if keyword in text:
                        found.append(module.title())
                        break
        
        return found
    
    def get_exact_match(self, term: str, db_values: List[str]) -> Optional[str]:
        """
        Find exact case-insensitive match in database values.
        
        Args:
            term: Term to match
            db_values: List of valid database values
            
        Returns:
            Exact match or None
        """
        term_lower = term.lower().strip()
        
        for value in db_values:
            if value.lower() == term_lower:
                return value
        
        return None
    
    def suggest_alternatives(
        self, 
        term: str, 
        db_values: List[str], 
        max_suggestions: int = 3
    ) -> List[str]:
        """
        Suggest similar values when exact match not found.
        
        Args:
            term: Term to match
            db_values: List of valid database values
            max_suggestions: Maximum number of suggestions
            
        Returns:
            List of suggested alternatives
        """
        # Use difflib for fuzzy matching
        matches = get_close_matches(term, db_values, n=max_suggestions, cutoff=0.6)
        return matches
    
    def requires_user_confirmation(self, extracted: str, matched: str) -> bool:
        """
        Determine if user confirmation needed before using approximation.
        
        Args:
            extracted: Originally extracted term
            matched: Matched database value
            
        Returns:
            True if confirmation needed
        """
        # Always require confirmation if not exact match
        return extracted.lower() != matched.lower()
    
    def validate_against_db(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate extracted entities exist in database.
        
        Args:
            entities: Extracted entities
            
        Returns:
            Updated entities with validation info
        """
        db_functions = self._load_db_job_functions()
        db_modules = self._load_db_job_modules()
        
        if not db_functions and not db_modules:
            # Database not available, return as-is
            return entities
        
        validated_functions = []
        validated_modules = []
        suggestions = []
        
        # Validate functions
        for func in entities.get('functions', []):
            # Try exact match
            exact_match = self.get_exact_match(func, db_functions)
            
            if exact_match:
                validated_functions.append(exact_match)
            else:
                # No exact match, suggest alternatives
                alternatives = self.suggest_alternatives(func, db_functions)
                if alternatives:
                    suggestions.append({
                        'type': 'function',
                        'original': func,
                        'alternatives': alternatives,
                        'requires_confirmation': True
                    })
        
        # Validate modules
        for module in entities.get('modules', []):
            # Try exact match
            exact_match = self.get_exact_match(module, db_modules)
            
            if exact_match:
                validated_modules.append(exact_match)
            else:
                # No exact match, suggest alternatives
                alternatives = self.suggest_alternatives(module, db_modules)
                if alternatives:
                    suggestions.append({
                        'type': 'module',
                        'original': module,
                        'alternatives': alternatives,
                        'requires_confirmation': True
                    })
        
        # Update entities
        entities['functions'] = validated_functions
        entities['modules'] = validated_modules
        entities['validation'] = {
            'has_suggestions': len(suggestions) > 0,
            'suggestions': suggestions
        }
        
        return entities


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
