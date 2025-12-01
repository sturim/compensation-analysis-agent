# LLM Usage Design - Kiro-Aligned Architecture

## Summary of Changes

The design has been updated to align with how Kiro actually uses LLMs, following the principle: **"LLM for reasoning, tools for execution"**

## Key Changes Made

### 1. Renamed Component: NLU Engine → LLM Orchestrator

**Old Approach:**
- Used LLM (Claude) for simple entity extraction
- Treated LLM as a parser
- Expensive and slow for deterministic tasks

**New Approach:**
- LLM used for high-level reasoning and planning
- Fast entity extraction with regex/keywords
- LLM reserved for complex tasks

### 2. Two-Phase LLM Usage

**Phase 1: Planning (LLM)**
```
User Question → LLM Orchestrator → Execution Plan
```
- Understand intent in context
- Plan which tools to use
- Determine execution order

**Phase 2: Response Generation (LLM)**
```
Results → LLM Orchestrator → Natural Language Response
```
- Synthesize insights
- Generate conversational response
- Suggest next steps

**Between Phases: Deterministic Execution (No LLM)**
```
Execution Plan → Tools (SQL, Pandas, Matplotlib) → Results
```
- Fast, reliable, cheap
- Deterministic and testable

### 3. New Component: EntityParser

Fast, deterministic entity extraction:
- Job functions: regex matching
- Job levels: pattern matching
- Metrics: keyword matching
- No LLM needed - <1ms, $0 cost

### 4. Updated Architecture Flow

```
Question
   ↓
[LLM] Plan execution with context
   ↓
[Fast] Extract entities (regex)
   ↓
[Tools] Execute plan (SQL, pandas, matplotlib)
   ↓
[LLM] Generate insightful response
   ↓
Response
```

## Comparison: Old vs New Design

### Entity Extraction

**Old Design:**
```python
# Uses LLM for simple parsing
parsed = claude.parse_question(
    "What's the salary for Finance Managers?"
)
# Cost: $0.001-0.01, Time: 200-500ms
```

**New Design:**
```python
# Fast deterministic parsing
entities = EntityParser().extract(
    "What's the salary for Finance Managers?"
)
# Cost: $0, Time: <1ms
# Result: {function: "Finance", level: "Manager (M3)"}
```

### Planning and Execution

**Old Design:**
```python
# LLM does everything
result = claude.query_and_format(question)
```

**New Design:**
```python
# LLM plans, tools execute
plan = llm.create_plan(question, entities, context)
results = execute_tools(plan)  # No LLM
response = llm.generate_response(results)  # LLM for insights
```

## Benefits of New Design

### 1. Cost Efficiency
- **Old**: 2-3 LLM calls per question ($0.01-0.05)
- **New**: 2 LLM calls (planning + response), entity extraction free ($0.005-0.02)
- **Savings**: 40-60% cost reduction

### 2. Speed
- **Old**: 500-1500ms (multiple LLM calls)
- **New**: 400-800ms (parallel execution, fast entity extraction)
- **Improvement**: 30-50% faster

### 3. Reliability
- **Old**: LLM parsing can be inconsistent
- **New**: Deterministic entity extraction, LLM only for reasoning
- **Improvement**: More predictable behavior

### 4. Testability
- **Old**: Hard to test LLM parsing
- **New**: Entity extraction fully testable, LLM behavior isolated
- **Improvement**: Better test coverage

## Implementation Guidelines

### When to Call LLM

✅ **DO use LLM for:**
```python
# 1. Planning with context
plan = llm.plan_execution(
    question=question,
    history=conversation.history,
    available_tools=tools
)

# 2. Ambiguity detection
clarification = llm.detect_ambiguity(
    question=question,
    context=context
)

# 3. Reference resolution
resolved = llm.resolve_reference(
    question="compare them",
    history=conversation.history
)

# 4. Response generation
response = llm.generate_response(
    question=question,
    results=results,
    insights=insights
)
```

❌ **DON'T use LLM for:**
```python
# 1. Entity extraction - use regex
entities = EntityParser().extract(question)

# 2. Data queries - use SQL
data = database.query(entities)

# 3. Calculations - use pandas
stats = data.describe()

# 4. Visualization - use matplotlib
chart = create_chart(data)
```

### Prompt Engineering

**Planning Prompt:**
```python
prompt = f"""Given this question and context, create an execution plan.

Question: {question}
Context: {conversation.history[-3:]}
Available Tools: {tool_descriptions}

Return a JSON array of tool calls in execution order.
Each tool call should have: tool_name, parameters, dependencies.

Example:
[
  {{"tool": "query_database", "params": {{"function": "Engineering"}}}},
  {{"tool": "visualize", "params": {{"data": "step1", "type": "distribution"}}}}
]
"""
```

**Response Generation Prompt:**
```python
prompt = f"""Generate a conversational response with insights.

Question: {question}
Results: {json.dumps(results)}

Include:
1. Direct answer to the question
2. 2-3 key insights from the data
3. 2-3 suggested next steps

Be conversational and helpful. Use specific numbers.
"""
```

## Testing Strategy

### Unit Tests (No LLM)
```python
def test_entity_extraction():
    parser = EntityParser()
    result = parser.extract("Finance Manager salaries")
    assert result["function"] == "Finance"
    assert result["level"] == "Manager (M3)"
```

### Integration Tests (With LLM)
```python
def test_planning():
    llm = LLMOrchestrator(mock_claude)
    plan = llm.plan_execution("Compare engineering and sales")
    assert len(plan.steps) >= 2
    assert "query_database" in [s.tool for s in plan.steps]
```

### Property Tests
```python
@given(st.text())
def test_entity_extraction_never_crashes(question):
    parser = EntityParser()
    result = parser.extract(question)
    assert isinstance(result, dict)
```

## Migration Path

### Phase 1: Add EntityParser
- Implement fast entity extraction
- Test against current LLM parsing
- Ensure accuracy matches or exceeds

### Phase 2: Refactor LLM Usage
- Move LLM to planning role
- Keep execution deterministic
- Add response generation

### Phase 3: Optimize
- Cache common plans
- Batch LLM calls where possible
- Monitor costs and performance

## Success Metrics

- **Cost per query**: <$0.02 (vs current $0.03-0.05)
- **Response time**: <800ms (vs current 1000-1500ms)
- **Entity extraction accuracy**: >95% (vs current ~90%)
- **User satisfaction**: Comparable to Kiro

## Conclusion

The updated design follows Kiro's architecture:
- **LLM for reasoning**: Planning and response generation
- **Tools for execution**: Fast, reliable, deterministic
- **Best of both worlds**: Intelligence + reliability

This approach is:
- ✅ More cost-effective
- ✅ Faster
- ✅ More reliable
- ✅ Easier to test
- ✅ Aligned with Kiro's proven architecture
