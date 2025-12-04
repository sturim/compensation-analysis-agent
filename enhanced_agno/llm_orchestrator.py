#!/usr/bin/env python3
"""
LLM Orchestrator - Uses Claude for planning and response generation
"""

from typing import Dict, List, Any, Optional
import json


class LLMOrchestrator:
    """Uses LLM for high-level reasoning, not data processing"""
    
    def __init__(self, claude_client, conversation_manager):
        self.claude = claude_client
        self.conversation = conversation_manager
    
    def plan_execution(self, question: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use LLM to create execution plan.
        Returns structured plan with tool calls.
        """
        if not self.claude:
            return self._fallback_plan(entities)
        
        try:
            context = self.conversation.get_context_summary()
            
            prompt = f"""You are a compensation analysis assistant. Create an execution plan.

Question: {question}
Extracted Entities: {json.dumps(entities, indent=2)}
Context: {context}

Available Tools:
- query_database: Query compensation data
- create_comparison: Compare two datasets
- visualize: Create charts
- calculate_stats: Calculate statistics

IMPORTANT: Return ONLY a valid JSON array. No explanation, no markdown, just the JSON array.

Format:
[
  {{"tool": "query_database", "params": {{"function": "Engineering"}}}},
  {{"tool": "visualize", "params": {{"type": "distribution"}}}}
]

Return 2-4 steps as a JSON array:"""
            
            message = self.claude.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text.strip()
            
            # Debug: print what Claude returned
            if not response_text:
                print(f"⚠️  Claude returned empty response")
                return self._fallback_plan(entities)
            
            # Extract JSON - try multiple methods
            json_text = response_text
            
            # Method 1: Look for ```json blocks
            if '```json' in response_text:
                json_text = response_text.split('```json')[1].split('```')[0].strip()
            # Method 2: Look for any ``` blocks
            elif '```' in response_text:
                json_text = response_text.split('```')[1].split('```')[0].strip()
            # Method 3: Look for [ or { at start
            elif '[' in response_text:
                start = response_text.index('[')
                # Find matching ]
                json_text = response_text[start:]
                if ']' in json_text:
                    end = json_text.rindex(']') + 1
                    json_text = json_text[:end]
            
            # Try to parse
            if not json_text or json_text == response_text and not json_text.startswith('['):
                print(f"⚠️  Could not extract JSON from Claude response")
                print(f"     Response preview: {response_text[:100]}...")
                return self._fallback_plan(entities)
            
            plan = json.loads(json_text)
            return {'status': 'success', 'plan': plan, 'source': 'llm'}
            
        except Exception as e:
            print(f"⚠️  LLM planning failed: {e}, using fallback")
            return self._fallback_plan(entities)

    def _fallback_plan(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback planning without LLM"""
        intent = entities.get('intent', 'query')
        functions = entities.get('functions', [])
        
        plan = []
        
        if intent == 'compare' and len(functions) >= 2:
            plan = [
                {"tool": "query_database", "params": {"function": functions[0]}},
                {"tool": "query_database", "params": {"function": functions[1]}},
                {"tool": "create_comparison", "params": {}},
                {"tool": "visualize", "params": {"type": "comparison"}}
            ]
        elif intent == 'visualize' or intent == 'analyze':
            plan = [
                {"tool": "query_database", "params": {"function": functions[0] if functions else "All"}},
                {"tool": "calculate_stats", "params": {}},
                {"tool": "visualize", "params": {"type": "distribution"}}
            ]
        else:
            plan = [
                {"tool": "query_database", "params": {"function": functions[0] if functions else "All"}},
                {"tool": "calculate_stats", "params": {}}
            ]
        
        return {'status': 'success', 'plan': plan, 'source': 'fallback'}
    
    def generate_response(self, question: str, results: Dict[str, Any]) -> str:
        """
        Use LLM to generate insightful response.
        This is where LLM adds value - synthesizing insights.
        """
        if not self.claude:
            return self._fallback_response(results)
        
        try:
            # Convert numpy types to native Python types for JSON serialization
            serializable_results = self._make_json_serializable(results)
            
            # Get database schema context
            schema_context = self._get_schema_context()
            
            prompt = f"""Generate a helpful, conversational response.

Question: {question}
Results: {json.dumps(serializable_results, indent=2)}

{schema_context}

RESPONSE GUIDELINES:
1. Direct answer to the question with specific numbers
2. 2-3 key insights from the data
3. Mention any charts created
4. Suggest 1-2 related analyses

CLARIFICATION PROTOCOL:
- If the query was ambiguous, explain what you searched for
- If multiple interpretations exist, mention alternatives
- If data is missing, suggest what might be available

Be conversational and use specific numbers. Keep it concise.
"""
            
            message = self.claude.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return message.content[0].text.strip()
            
        except Exception as e:
            print(f"⚠️  LLM response generation failed: {e}")
            return self._fallback_response(results)
    
    def _make_json_serializable(self, obj: Any) -> Any:
        """
        Convert numpy types and other non-serializable objects to JSON-serializable types.
        
        Args:
            obj: Object to convert
            
        Returns:
            JSON-serializable version of the object
        """
        import numpy as np
        
        if isinstance(obj, dict):
            return {key: self._make_json_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_serializable(item) for item in obj]
        elif isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return obj
    
    def _get_schema_context(self) -> str:
        """Get database schema context for LLM"""
        return """
DATABASE SCHEMA REFERENCE:
- job_function: Broad category (Finance, Engineering, Sales, Marketing, HR, Operations, etc.)
- job_level: Seniority levels
  * P1-P6: Professional levels (Entry, Developing, Career, Advanced, Expert, Principal)
  * M1-M6: Management levels (Supervisor, Sr Supervisor, Manager, Sr Manager, Director, Sr Director)
  * E1-E4: Executive levels
  * S1-S5: Support levels
  * F1-F7: Specialized levels
- Compensation metrics: base_salary_lfy (Last Fiscal Year), total_comp (Total Compensation)
- Percentiles: p10, p25, p50 (median), p75, p90
"""
    
    def check_for_ambiguity(self, question: str, entities: Dict[str, Any]) -> Optional[str]:
        """
        Check if query is ambiguous and needs clarification.
        
        Returns:
            Clarification question if ambiguous, None otherwise
        """
        if not self.claude:
            return None
        
        try:
            prompt = f"""Analyze if this query is ambiguous and needs clarification.

Question: "{question}"
Extracted: {json.dumps(entities)}

Common ambiguities:
- "Engineering" → All engineering roles or specific area (Software, Infrastructure)?
- "Manager" → Which level (M1-M6)?
- "Finance" → All finance roles or specific function?
- "Senior" → Sr Supervisor (M2), Sr Manager (M4), or Sr Director (M6)?

If ambiguous, return a clarification question.
If clear, return "CLEAR".

Response:"""
            
            message = self.claude.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response = message.content[0].text.strip()
            
            if response == "CLEAR" or "clear" in response.lower()[:20]:
                return None
            
            return response
            
        except Exception as e:
            print(f"⚠️  Ambiguity check failed: {e}")
            return None
    
    def generate_confirmation(self, question: str, entities: Dict[str, Any], query_plan: str) -> str:
        """
        Generate confirmation message before executing query.
        
        Args:
            question: User's question
            entities: Extracted entities
            query_plan: Description of what will be queried
            
        Returns:
            Confirmation message
        """
        if not self.claude:
            return self._fallback_confirmation(entities, query_plan)
        
        try:
            prompt = f"""Generate a brief confirmation message before executing a database query.

Question: "{question}"
Will search for: {json.dumps(entities)}
Query plan: {query_plan}

Format:
"I'll search for [specific criteria]. This will query:
- [detail 1]
- [detail 2]

Does this match what you're looking for?"

Keep it concise (2-3 lines max).
"""
            
            message = self.claude.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return message.content[0].text.strip()
            
        except Exception as e:
            print(f"⚠️  Confirmation generation failed: {e}")
            return self._fallback_confirmation(entities, query_plan)
    
    def _fallback_confirmation(self, entities: Dict[str, Any], query_plan: str) -> str:
        """Fallback confirmation without LLM"""
        functions = entities.get('functions', [])
        levels = entities.get('levels', [])
        
        msg = "I'll search for:\n"
        if functions:
            msg += f"- Functions: {', '.join(functions)}\n"
        if levels:
            msg += f"- Levels: {', '.join(levels)}\n"
        msg += f"\n{query_plan}\n\nDoes this match what you're looking for?"
        
        return msg
    
    def _fallback_response(self, results: Dict[str, Any]) -> str:
        """Fallback response without LLM"""
        response = "Here are the results:\n\n"
        
        for key, value in results.items():
            if isinstance(value, (int, float)):
                response += f"• {key}: ${value:,.0f}\n"
            else:
                response += f"• {key}: {value}\n"
        
        return response
