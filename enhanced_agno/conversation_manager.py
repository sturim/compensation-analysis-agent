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
    """Manages conversation history and context with session support"""
    
    def __init__(self):
        # Session-based storage: {session_id: {history: [], context: {}}}
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.current_session_id: Optional[str] = None
        
        # Legacy support - default session
        self.history: List[Interaction] = []
        self.context: Dict[str, Any] = {}
    
    def create_session(self, session_id: str = None) -> str:
        """Create a new session and return its ID"""
        if session_id is None:
            from datetime import datetime
            import random
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            random_suffix = random.randint(10000, 99999)
            session_id = f"hr_session_{timestamp}_{random_suffix}"
        
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                'history': [],
                'context': {},
                'created_at': datetime.now().isoformat()
            }
        
        self.current_session_id = session_id
        return session_id
    
    def set_session(self, session_id: str) -> bool:
        """Set the active session"""
        if session_id not in self.sessions:
            # Create session if it doesn't exist
            self.create_session(session_id)
        
        self.current_session_id = session_id
        return True
    
    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get history for a specific session"""
        if session_id in self.sessions:
            return [i.to_dict() for i in self.sessions[session_id]['history']]
        return []
    
    def get_session_context(self, session_id: str) -> Dict[str, Any]:
        """Get context for a specific session"""
        if session_id in self.sessions:
            return self.sessions[session_id]['context']
        return {}
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all sessions with metadata"""
        sessions = []
        for session_id, data in self.sessions.items():
            sessions.append({
                'session_id': session_id,
                'created_at': data.get('created_at'),
                'message_count': len(data['history'])
            })
        return sessions
    
    def add_interaction(self, question: str, entities: Dict[str, Any], 
                       results: Dict[str, Any], response: str, session_id: str = None):
        """Add a Q&A interaction to history"""
        interaction = Interaction(
            timestamp=datetime.now().isoformat(),
            question=question,
            entities=entities,
            results=results,
            response=response
        )
        
        # Add to session-specific history if session is active
        if session_id or self.current_session_id:
            sid = session_id or self.current_session_id
            if sid not in self.sessions:
                self.create_session(sid)
            self.sessions[sid]['history'].append(interaction)
            self._update_context(interaction, sid)
        
        # Also add to legacy history for backward compatibility
        self.history.append(interaction)
        self._update_context(interaction)
    
    def _update_context(self, interaction: Interaction, session_id: str = None):
        """Update context based on latest interaction"""
        # Determine which context to update
        if session_id and session_id in self.sessions:
            context = self.sessions[session_id]['context']
        else:
            context = self.context
        
        # Track last mentioned entities
        if interaction.entities.get('functions'):
            context['last_functions'] = interaction.entities['functions']
        if interaction.entities.get('levels'):
            context['last_levels'] = interaction.entities['levels']
        
        # Track last query type
        context['last_intent'] = interaction.entities.get('intent')
    
    def get_recent_history(self, n: int = 3) -> List[Dict[str, Any]]:
        """Get n most recent interactions"""
        return [i.to_dict() for i in self.history[-n:]]
    
    def resolve_reference(self, text: str, session_id: str = None) -> Optional[Dict[str, Any]]:
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
        
        # Get context from session or default
        if session_id and session_id in self.sessions:
            context = self.sessions[session_id]['context']
        else:
            context = self.context
        
        # Return last mentioned entities
        return {
            'functions': context.get('last_functions', []),
            'levels': context.get('last_levels', []),
            'intent': context.get('last_intent')
        }
    
    def get_context_summary(self, session_id: str = None) -> str:
        """Get a summary of current context for LLM"""
        # Get history from session or default
        if session_id and session_id in self.sessions:
            history = self.sessions[session_id]['history']
        else:
            history = self.history
        
        if not history:
            return "No previous conversation."
        
        recent = history[-3:]
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
