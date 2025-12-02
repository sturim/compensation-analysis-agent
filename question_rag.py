#!/usr/bin/env python3
"""
RAG System for Question Templates
Loads questions from Excel and provides retrieval for AGNT_HR_Reporter
"""

import pandas as pd
from typing import List, Dict, Optional, Tuple
import json
import os


class QuestionRAG:
    """RAG system for question templates and follow-ups."""
    
    def __init__(self, excel_path: str = "questions.xlsx", json_path: str = "questions_rag.json"):
        """
        Initialize the RAG system with questions from JSON or Excel.
        Prefers JSON if available (faster), falls back to Excel.
        
        Args:
            excel_path: Path to Excel file with questions
            json_path: Path to JSON file with pre-loaded questions
        """
        self.excel_path = excel_path
        self.json_path = json_path
        self.questions_db = []
        self.loaded = False
        
        # Try JSON first (faster)
        if os.path.exists(json_path):
            self.load_from_json()
        # Fall back to Excel
        elif os.path.exists(excel_path):
            self.load_questions()
    
    def load_questions(self) -> bool:
        """
        Load questions from Excel file.
        
        Expected Excel structure:
        - Column: 'initial_question' or 'question' - The main question
        - Column: 'follow_up_1', 'follow_up_2', etc. - Follow-up questions
        - Column: 'category' (optional) - Question category
        - Column: 'context' (optional) - Additional context
        
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            # Try to read Excel file
            df = pd.read_excel(self.excel_path)
            
            print(f"Loading questions from {self.excel_path}")
            print(f"Columns found: {list(df.columns)}")
            
            # Normalize column names to lowercase for easier matching
            df.columns = df.columns.str.lower().str.strip()
            
            # Parse each row
            for idx, row in df.iterrows():
                question_entry = {
                    'id': idx,
                    'initial_question': None,
                    'follow_ups': [],
                    'category': None,
                    'context': None
                }
                
                # Get initial question (try different column names)
                for col in ['initial_question', 'question', 'main_question', 'primary_question']:
                    if col in df.columns and pd.notna(row.get(col)):
                        question_entry['initial_question'] = str(row[col]).strip()
                        break
                
                # Get follow-up questions (handle both single and multiple columns)
                follow_up_cols = [col for col in df.columns if 'follow' in col.lower()]
                for col in follow_up_cols:
                    if pd.notna(row.get(col)):
                        follow_up_text = str(row[col]).strip()
                        # Split by newlines or semicolons if multiple follow-ups in one cell
                        if '\n' in follow_up_text:
                            question_entry['follow_ups'].extend([f.strip() for f in follow_up_text.split('\n') if f.strip()])
                        elif ';' in follow_up_text:
                            question_entry['follow_ups'].extend([f.strip() for f in follow_up_text.split(';') if f.strip()])
                        else:
                            question_entry['follow_ups'].append(follow_up_text)
                
                # Get category (try 'category' or 'group')
                for col in ['category', 'group', 'type']:
                    if col in df.columns and pd.notna(row.get(col)):
                        question_entry['category'] = str(row[col]).strip()
                        break
                
                # Get context
                if 'context' in df.columns and pd.notna(row.get('context')):
                    question_entry['context'] = str(row['context']).strip()
                
                # Only add if we have an initial question
                if question_entry['initial_question']:
                    self.questions_db.append(question_entry)
            
            self.loaded = True
            print(f"✓ Loaded {len(self.questions_db)} question templates")
            return True
            
        except FileNotFoundError:
            print(f"✗ Excel file not found: {self.excel_path}")
            return False
        except Exception as e:
            print(f"✗ Error loading questions: {str(e)}")
            return False
    
    def get_all_questions(self) -> List[Dict]:
        """Get all question templates."""
        return self.questions_db
    
    def get_question_by_id(self, question_id: int) -> Optional[Dict]:
        """Get a specific question by ID."""
        for q in self.questions_db:
            if q['id'] == question_id:
                return q
        return None
    
    def get_questions_by_category(self, category: str) -> List[Dict]:
        """Get all questions in a category."""
        return [q for q in self.questions_db if q.get('category') == category]
    
    def search_questions(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Keyword-based search for relevant questions.
        Supports multi-word queries by splitting into keywords.
        
        Args:
            query: Search query (can be multiple words)
            top_k: Number of results to return
        
        Returns:
            List of matching questions
        """
        query_lower = query.lower()
        # Split query into keywords for better matching
        keywords = [w.strip() for w in query_lower.split() if len(w.strip()) > 2]
        
        results = []
        
        for q in self.questions_db:
            score = 0
            question_text = q['initial_question'].lower()
            
            # Check for exact phrase match first (highest score)
            if query_lower in question_text:
                score += 20
            
            # Check for individual keyword matches
            for keyword in keywords:
                # Check initial question
                if keyword in question_text:
                    score += 5
                
                # Check follow-ups
                for follow_up in q['follow_ups']:
                    if keyword in follow_up.lower():
                        score += 3
                
                # Check category
                if q.get('category') and keyword in q['category'].lower():
                    score += 4
                
                # Check context
                if q.get('context') and keyword in q['context'].lower():
                    score += 2
            
            if score > 0:
                results.append((score, q))
        
        # Sort by score and return top_k
        results.sort(key=lambda x: x[0], reverse=True)
        return [q for score, q in results[:top_k]]
    
    def get_suggested_questions(self, context: Optional[str] = None) -> List[str]:
        """
        Get suggested questions based on context.
        
        Args:
            context: Optional context to filter suggestions
        
        Returns:
            List of suggested question strings
        """
        suggestions = []
        
        if context:
            # Get relevant questions based on context
            relevant = self.search_questions(context, top_k=3)
            for q in relevant:
                suggestions.append(q['initial_question'])
        else:
            # Return random sample of initial questions
            import random
            sample_size = min(5, len(self.questions_db))
            sample = random.sample(self.questions_db, sample_size)
            suggestions = [q['initial_question'] for q in sample]
        
        return suggestions
    
    def get_follow_ups(self, question_id: int) -> List[str]:
        """Get follow-up questions for a specific question."""
        q = self.get_question_by_id(question_id)
        return q['follow_ups'] if q else []
    
    def format_for_agent(self) -> str:
        """
        Format questions as context for the agent.
        
        Returns:
            Formatted string for agent instructions
        """
        if not self.questions_db:
            return ""
        
        output = ["QUESTION TEMPLATES AND EXAMPLES:\n"]
        
        for q in self.questions_db:
            output.append(f"\n{q['id'] + 1}. {q['initial_question']}")
            
            if q.get('category'):
                output.append(f"   Category: {q['category']}")
            
            if q['follow_ups']:
                output.append("   Follow-up questions:")
                for i, follow_up in enumerate(q['follow_ups'], 1):
                    output.append(f"   {i}) {follow_up}")
            
            if q.get('context'):
                output.append(f"   Context: {q['context']}")
        
        return "\n".join(output)
    
    def load_from_json(self) -> bool:
        """
        Load questions from JSON file (faster than Excel).
        
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            with open(self.json_path, 'r') as f:
                self.questions_db = json.load(f)
            
            self.loaded = True
            print(f"✓ Loaded {len(self.questions_db)} question templates from JSON")
            return True
            
        except FileNotFoundError:
            print(f"✗ JSON file not found: {self.json_path}")
            return False
        except Exception as e:
            print(f"✗ Error loading from JSON: {str(e)}")
            return False
    
    def export_to_json(self, output_path: str = "questions.json"):
        """Export questions to JSON file."""
        with open(output_path, 'w') as f:
            json.dump(self.questions_db, f, indent=2)
        print(f"✓ Exported questions to {output_path}")
    
    def get_stats(self) -> Dict:
        """Get statistics about loaded questions."""
        total_follow_ups = sum(len(q['follow_ups']) for q in self.questions_db)
        categories = set(q.get('category') for q in self.questions_db if q.get('category'))
        
        return {
            'total_questions': len(self.questions_db),
            'total_follow_ups': total_follow_ups,
            'categories': list(categories),
            'avg_follow_ups': total_follow_ups / len(self.questions_db) if self.questions_db else 0
        }


# Test function
def test_rag():
    """Test the RAG system."""
    rag = QuestionRAG("List of Questions.xlsx")
    
    if rag.loaded:
        print("\n" + "="*60)
        print("Question RAG System - Statistics")
        print("="*60)
        stats = rag.get_stats()
        print(f"Total Questions: {stats['total_questions']}")
        print(f"Total Follow-ups: {stats['total_follow_ups']}")
        print(f"Average Follow-ups per Question: {stats['avg_follow_ups']:.1f}")
        print(f"Categories: {', '.join(stats['categories']) if stats['categories'] else 'None'}")
        
        print("\n" + "="*60)
        print("Sample Questions")
        print("="*60)
        for q in rag.get_all_questions()[:3]:
            print(f"\n{q['id'] + 1}. {q['initial_question']}")
            if q['follow_ups']:
                print("   Follow-ups:")
                for fu in q['follow_ups']:
                    print(f"   - {fu}")


if __name__ == "__main__":
    test_rag()
