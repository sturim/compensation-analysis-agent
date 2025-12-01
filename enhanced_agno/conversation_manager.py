#!/usr/bin/env python3
"""
Conversation Manager - Tracks context and history
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import json


@dataclass
class Interaction:
    """Represents a single Q&A interaction"""
    timestamp: str
    question: str
    entities: Dict[str, Any]
    results: Dict[str, Any]
    response: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ConversationManager:
    """Manages conversation history and context"""
    
    def __init__(self):
        self.history: List[Interaction] = []
        self.context: Dict[str, Any] = {}
    
    def add_interaction(self, question: str, entities: Dict[str, Any], 
                       results: Dict[str, Any], response: str):
        """Add a Q&A interaction to history"""
        interaction = Interaction(
            timestamp=datetime.now().isoformat(),
            question=question,
            entities=entities,
            results=results,
            response=response
        )
        self.history.append(interaction)
        self._update_context(interaction)
    
    def _update_context(self, interaction: Interaction):
        """Update context based on latest interaction"""
        # Track last mentioned entities
        if interaction.entities.get('functions'):
            self.context['last_functions'] = interaction.entities['functions']
        if interaction.entities.get('levels'):
            self.context['last_levels'] = interaction.entities['levels']
        
        # Track last query type
        self.context['last_intent'] = interaction.entities.get('intent')
    
    def get_recent_history(self, n: int = 3) -> List[Dict[str, Any]]:
        """Get n most recent interactions"""
        return [i.to_dict() for i in self.history[-n:]]
    
    def resolve_reference(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Resolve references like 'them', 'that', 'those'
        Returns context that the reference likely refers to
        """
        text_lower = text.lower()
        
        # Check for reference words
        reference_words = ['them', 'that', 'those', 'it', 'these']
        has_reference = any(word in text_lower for word in reference_words)
        
        if not has_reference:
            return None
        
        # Return last mentioned entities
        return {
            'functions': self.context.get('last_functions', []),
            'levels': self.context.get('last_levels', []),
            'intent': self.context.get('last_intent')
        }
    
    def get_context_summary(self) -> str:
        """Get a summary of current context for LLM"""
        if not self.history:
            return "No previous conversation."
        
        recent = self.history[-3:]
        summary = "Recent conversation:\n"
        for i, interaction in enumerate(recent, 1):
            summary += f"{i}. Q: {interaction.question}\n"
            if interaction.entities.get('functions'):
                summary += f"   Functions: {', '.join(interaction.entities['functions'])}\n"
        
        return summary
    
    def clear(self):
        """Clear history and context"""
        self.history.clear()
        self.context.clear()


if __name__ == "__main__":
    # Test conversation manager
    manager = ConversationManager()
    
    # Simulate conversation
    manager.add_interaction(
        question="What's the salary for engineering managers?",
        entities={'functions': ['Engineering'], 'levels': ['Manager (M3)']},
        results={'avg_salary': 219109},
        response="Engineering managers earn $219,109 on average."
    )
    
    manager.add_interaction(
        question="Compare them to sales",
        entities={'functions': ['Sales'], 'intent': 'compare'},
        results={'comparison': 'data'},
        response="Comparison complete."
    )
    
    # Test reference resolution
    ref = manager.resolve_reference("compare them to finance")
    print("Reference resolution:", ref)
    
    # Test context summary
    print("\n" + manager.get_context_summary())
