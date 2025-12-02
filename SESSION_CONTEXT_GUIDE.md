# Session Context Retention Guide

## Overview

The Enhanced Agno Agent now supports **session-based context retention**, allowing multiple independent conversations to run simultaneously while maintaining separate context for each session.

## Key Features

### ✅ Session Management
- **Unique Session IDs**: Each conversation gets a unique ID like `hr_session_20241201_143022_12345`
- **Session Persistence**: Sessions maintain their own conversation history and context
- **Context Preservation**: Follow-up questions use the correct session context
- **Multiple Sessions**: Support for unlimited concurrent sessions

### ✅ Context Tracking Per Session
Each session independently tracks:
- **Conversation History**: All questions and responses
- **Entity Context**: Last mentioned functions, levels, intents
- **Reference Resolution**: "that", "them", "those" resolve to session-specific context

## Usage

### Python API

```python
from enhanced_agno_agent import EnhancedAgnoAgent

agent = EnhancedAgnoAgent()

# Create a new session
session_id = agent.create_session()
# Returns: 'hr_session_20241201_143022_12345'

# Ask questions with session context
response1 = agent.ask("give me engineering salaries", session_id=session_id)
response2 = agent.ask("what about managers?", session_id=session_id)
# "managers" will be understood in the context of Engineering

# Get session history
history = agent.get_session_history(session_id)
for interaction in history:
    print(f"Q: {interaction['question']}")
    print(f"Functions: {interaction['entities']['functions']}")

# List all sessions
sessions = agent.list_sessions()
for session in sessions:
    print(f"Session: {session['session_id']}")
    print(f"Messages: {session['message_count']}")
```

### Multiple Sessions Example

```python
agent = EnhancedAgnoAgent()

# Session 1: Engineering analysis
session1 = agent.create_session()
agent.ask("give me engineering salaries", session_id=session1)
agent.ask("what about senior levels?", session_id=session1)  # Uses Engineering context

# Session 2: Sales analysis (independent context)
session2 = agent.create_session()
agent.ask("give me sales salaries", session_id=session2)
agent.ask("what about senior levels?", session_id=session2)  # Uses Sales context

# Each session maintains its own context!
```

## Session ID Format

Session IDs follow the pattern: `hr_session_YYYYMMDD_HHMMSS_RANDOM`

Example: `hr_session_20241201_143022_12345`

- **Prefix**: `hr_session_`
- **Date**: `YYYYMMDD` (e.g., 20241201)
- **Time**: `HHMMSS` (e.g., 143022)
- **Random**: 5-digit random number (e.g., 12345)

## API Methods

### `create_session(session_id: str = None) -> str`
Creates a new session and returns its ID.
- If `session_id` is provided, uses that ID
- If not provided, generates a unique ID automatically

### `ask(question: str, session_id: str = None) -> str`
Processes a question with optional session context.
- If `session_id` is provided, uses that session's context
- If not provided, uses default (legacy) context

### `get_session_history(session_id: str) -> List[Dict]`
Returns the conversation history for a specific session.

### `list_sessions() -> List[Dict]`
Returns metadata for all active sessions.

## Web Integration Ready

This implementation is designed to integrate seamlessly with web applications:

### Backend (Flask/FastAPI)
```python
from flask import Flask, request, jsonify
from enhanced_agno_agent import EnhancedAgnoAgent

app = Flask(__name__)
agent = EnhancedAgnoAgent()

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    message = data['message']
    session_id = data.get('session_id')
    
    # Create session if not provided
    if not session_id:
        session_id = agent.create_session()
    
    # Process with session context
    response = agent.ask(message, session_id=session_id)
    
    return jsonify({
        'response': response,
        'session_id': session_id
    })

@app.route('/api/session/<session_id>/history', methods=['GET'])
def get_history(session_id):
    history = agent.get_session_history(session_id)
    return jsonify({'history': history})

@app.route('/api/session/new', methods=['POST'])
def new_session():
    session_id = agent.create_session()
    return jsonify({'session_id': session_id})
```

### Frontend (React/TypeScript)
```typescript
// Store session ID in localStorage
const sessionId = localStorage.getItem('hr_session_id') || null;

// Send message with session context
const response = await fetch('/api/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: userQuestion,
    session_id: sessionId
  })
});

const data = await response.json();

// Store session ID for future requests
localStorage.setItem('hr_session_id', data.session_id);
```

## Benefits

### 🎯 Context Preservation
- Follow-up questions work correctly
- "that", "them", "those" resolve to the right context
- No confusion between different conversations

### 🔄 Multiple Conversations
- Support multiple users simultaneously
- Each user has independent context
- No cross-contamination between sessions

### 💾 Session Persistence
- Sessions can be retrieved later
- Full conversation history available
- Context can be restored

### 🌐 Web-Ready
- Designed for web application integration
- Session IDs work with browser localStorage
- RESTful API pattern

## Testing

Run the test script to see session context in action:

```bash
python3 test_session_context.py
```

This demonstrates:
- Creating multiple sessions
- Independent context per session
- Follow-up questions using correct context
- Session history retrieval

## Backward Compatibility

The implementation maintains backward compatibility:
- Calling `ask()` without `session_id` works as before
- Legacy `conversation.history` still available
- No breaking changes to existing code

## Next Steps

This session context implementation is ready for:
1. **Web Interface Integration** - Flask/FastAPI backend
2. **Frontend Development** - React/Vue/Angular with localStorage
3. **Session Persistence** - Database storage for long-term sessions
4. **Session Management UI** - View/delete/export sessions

The foundation is complete and production-ready! 🚀
