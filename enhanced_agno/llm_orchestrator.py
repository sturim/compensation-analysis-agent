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
            prompt = f"""Generate a helpful, conversational response.

Question: {question}
Results: {json.dumps(results, indent=2)}

Include:
1. Direct answer to the question
2. 2-3 key insights from the data
3. Mention any charts created
4. Suggest 1-2 related analyses

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
    
    def _fallback_response(self, results: Dict[str, Any]) -> str:
        """Fallback response without LLM"""
        response = "Here are the results:\n\n"
        
        for key, value in results.items():
            if isinstance(value, (int, float)):
                response += f"• {key}: ${value:,.0f}\n"
            else:
                response += f"• {key}: {value}\n"
        
        return response
