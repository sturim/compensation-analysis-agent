# Design Document: Enhanced Agno Agent

## Overview

The Enhanced Agno Agent is a sophisticated AI-powered compensation analysis system that combines natural language understanding, intelligent data analysis, and rich visualization capabilities. It aims to match the sophistication of Kiro's AI assistant while maintaining the domain-specific focus on HR compensation data.

## LLM Usage Philosophy

### When to Use LLM (Claude)

**✅ Use LLM for:**
1. **High-Level Planning**: Deciding which tools to call and in what order
2. **Context Understanding**: Interpreting questions in light of conversation history
3. **Ambiguity Resolution**: Detecting unclear requests and asking clarifying questions
4. **Natural Language Generation**: Creating conversational, insightful responses
5. **Reference Resolution**: Understanding "them", "that", "compare those"
6. **Insight Generation**: Synthesizing patterns and trends from data into natural language

**❌ Don't Use LLM for:**
1. **Simple Entity Extraction**: Use regex/keyword matching (faster, cheaper, deterministic)
2. **Data Processing**: Use pandas/SQL (more reliable, faster)
3. **Calculations**: Use Python (deterministic, accurate)
4. **Visualization**: Use matplotlib/seaborn (consistent, controllable)
5. **Structured Parsing**: Use JSON schemas and validation (reliable)

### LLM Integration Pattern (Kiro-Style)

```python
# GOOD: LLM for planning, tools for execution
def process_question(question: str):
    # 1. Fast entity extraction (no LLM)
    entities = entity_parser.extract(question)
    
    # 2. LLM for planning with context
    plan = llm.create_plan(
        question=question,
        entities=entities,
        history=conversation.history,
        available_tools=tools
    )
    
    # 3. Execute plan with tools (no LLM)
    results = execute_plan(plan)
    
    # 4. LLM for response generation
    response = llm.generate_response(
        question=question,
        results=results,
        insights=analyze_results(results)
    )
    
    return response

# BAD: Using LLM for simple parsing
def process_question_bad(question: str):
    # Expensive, slow, non-deterministic
    parsed = llm.parse_to_json(question)
    results = query_database(parsed)
    return format_results(results)
```

### Cost and Performance Considerations

- **Entity Extraction**: Regex/keywords = <1ms, $0 | LLM = 200-500ms, $0.001-0.01
- **Planning**: LLM necessary, but cache plans for similar questions
- **Response Generation**: LLM necessary for quality, but keep prompts concise
- **Data Processing**: Never use LLM - use pandas/SQL

### Concrete Example: "Compare engineering and sales salaries"

```python
# Step 1: Fast entity extraction (no LLM)
entities = EntityParser().extract("Compare engineering and sales salaries")
# Result: {functions: ["Engineering", "Sales"], intent: "compare"}

# Step 2: LLM creates execution plan
plan = llm_orchestrator.plan(
    question="Compare engineering and sales salaries",
    entities=entities,
    available_tools=["query_database", "create_comparison", "visualize"]
)
# LLM Output:
# [
#   {tool: "query_database", params: {function: "Engineering"}},
#   {tool: "query_database", params: {function: "Sales"}},
#   {tool: "create_comparison", params: {data1: "step1", data2: "step2"}},
#   {tool: "visualize", params: {type: "comparison", data: "step3"}}
# ]

# Step 3: Execute plan (no LLM - pure Python/SQL)
eng_data = query_database(function="Engineering")
sales_data = query_database(function="Sales")
comparison = create_comparison(eng_data, sales_data)
chart = visualize(comparison, type="comparison")

# Step 4: LLM generates response
response = llm_orchestrator.generate_response(
    question="Compare engineering and sales salaries",
    results={
        "engineering_avg": 231299,
        "sales_avg": 178807,
        "difference": 52492,
        "chart_path": "charts/eng_vs_sales.png"
    }
)
# LLM Output:
# "I've compared Engineering and Sales salaries. Key findings:
#  
#  Engineering has higher base salaries ($231K vs $179K, +29%)
#  However, Sales has more variable pay (52% vs 24% of base)
#  Total compensation is similar ($287K vs $272K)
#  
#  Chart saved to charts/eng_vs_sales.png
#  
#  💡 You might also want to:
#  • Compare at specific levels (Manager, Director)
#  • See career progression in each function
#  • Analyze top specializations"
```

This pattern ensures:
- Fast, cheap entity extraction
- Intelligent planning with context
- Reliable data processing
- Natural, insightful responses

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Interface                        │
│                  (CLI / Interactive Mode)                    │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                   LLM Orchestrator (Claude)                  │
│  • Understand question in context                            │
│  • Plan tool usage (like Kiro)                              │
│  • Generate natural language responses                       │
│  • Detect ambiguity and ask clarifications                   │
└──────────────────────────┬──────────────────────────────────┘
                           │
                    ┌──────┴──────┐
                    │ Check Tool  │
                    │ Inventory   │ ← NEW: Check existing tools first!
                    └──────┬──────┘
                           │
                ┌──────────┴──────────┐
                │                     │
         ┌──────▼──────┐      ┌──────▼──────┐
         │ Existing    │      │ Create New  │
         │ Tool Found? │      │ Execution   │
         │             │      │ Plan        │
         └──────┬──────┘      └──────┬──────┘
                │                     │
         ┌──────▼──────┐             │
         │ Execute     │             │
         │ Existing    │             │
         │ Script      │             │
         └──────┬──────┘             │
                │                     │
                └──────────┬──────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
┌───────▼────────┐ ┌──────▼──────┐ ┌────────▼────────┐
│ Entity Parser  │ │  Analysis   │ │  Visualization  │
│ (Regex/Fast)   │ │  Engine     │ │  Engine         │
│                │ │ (Pandas/SQL)│ │ (Matplotlib)    │
└───────┬────────┘ └──────┬──────┘ └────────┬────────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                    ┌──────▼──────┐
                    │   Results   │
                    └──────┬──────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│              LLM Response Generator (Claude)                 │
│  • Synthesize results into insights                          │
│  • Generate conversational response                          │
│  • Suggest next steps                                        │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                  Formatted Response                          │
│  • Rich text formatting                                      │
│  • Charts and visualizations                                 │
│  • Suggestions and next steps                                │
└──────────────────────────────────────────────────────────────┘

Note: NEW - Tool Inventory checks for existing scripts first!
      LLM used only for planning and response generation.
      All data processing uses deterministic tools.
```

### Component Breakdown

#### 1. Tool Discovery & Inventory (NEW - Critical Missing Component)
- **Purpose**: Know what tools exist and when to use them
- **Responsibilities**:
  - Scan workspace for existing analysis scripts
  - Build inventory of available tools with descriptions
  - Match user queries to existing tools
  - Prefer existing tools over creating new code
  - Only generate new code when no suitable tool exists
- **Why Critical**: Prevents reinventing the wheel, uses proven tools, faster execution

#### 2. Conversation Manager
- **Purpose**: Maintain context across multiple interactions
- **Responsibilities**:
  - Track conversation history
  - Store previous queries and results
  - Resolve references ("compare them", "show more")
  - Manage session state

#### 2. Query Orchestrator
- **Purpose**: Coordinate complex multi-step analyses
- **Responsibilities**:
  - Break down complex questions into steps
  - Determine execution order
  - Aggregate results from multiple tools
  - Handle dependencies between steps

#### 3. LLM Orchestrator (Enhanced)
- **Purpose**: High-level reasoning and conversation management using LLM
- **Responsibilities**:
  - Understand user intent in context of conversation history
  - Plan multi-step analyses and tool usage
  - Generate natural language explanations and insights
  - Detect ambiguity and formulate clarifying questions
  - Synthesize results into conversational responses
  
**Note**: Simple entity extraction uses regex/keyword matching. LLM is reserved for complex reasoning.

#### 4. Analysis Engine
- **Purpose**: Perform sophisticated data analysis
- **Responsibilities**:
  - Execute database queries
  - Calculate statistics and aggregations
  - Identify trends and patterns
  - Generate insights and recommendations

#### 5. Visualization Engine
- **Purpose**: Create professional charts and graphs
- **Responsibilities**:
  - Select appropriate chart types
  - Generate matplotlib/seaborn visualizations
  - Apply consistent styling
  - Save and manage output files

#### 6. Script Generator (Enhanced)
- **Purpose**: Create production-ready analysis scripts
- **Responsibilities**:
  - Generate well-structured Python code
  - Include error handling and validation
  - Add comprehensive documentation
  - Follow best practices and style guidelines

## Components and Interfaces

### ToolInventory Class (NEW)

```python
class ToolInventory:
    """Discovers and manages available workspace tools"""
    
    def __init__(self, workspace_path: str = "."):
        self.workspace_path = Path(workspace_path)
        self.tools: Dict[str, ToolInfo] = {}
        self.scan_workspace()
    
    def scan_workspace(self):
        """Scan workspace for existing analysis scripts"""
        # Find Python scripts that look like analysis tools
        for script in self.workspace_path.glob("*_analysis.py"):
            self._register_tool(script)
        
        for script in self.workspace_path.glob("*_chart.py"):
            self._register_tool(script)
    
    def _register_tool(self, script_path: Path):
        """Register a tool with metadata"""
        # Extract docstring and infer capabilities
        tool_info = self._extract_tool_info(script_path)
        self.tools[script_path.stem] = tool_info
    
    def match_query_to_tool(self, question: str, entities: Dict[str, Any]) -> Optional[str]:
        """
        Match user query to existing tool.
        Returns tool name if match found, None otherwise.
        
        Example:
        - "engineering salaries" → "engineering_analysis"
        - "finance charts" → "finance_salary_chart"
        """
        functions = entities.get('functions', [])
        intent = entities.get('intent', 'query')
        
        # Try to match function + intent to existing tools
        for tool_name, tool_info in self.tools.items():
            if self._is_match(tool_name, tool_info, functions, intent):
                return tool_name
        
        return None
    
    def _is_match(self, tool_name: str, tool_info: ToolInfo, 
                  functions: List[str], intent: str) -> bool:
        """Check if tool matches the query"""
        # Match function name
        for func in functions:
            if func.lower() in tool_name.lower():
                # Match intent
                if intent in ['query', 'analyze'] and 'analysis' in tool_name:
                    return True
                if intent in ['visualize', 'show'] and 'chart' in tool_name:
                    return True
        
        return False
    
    def execute_tool(self, tool_name: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute an existing tool"""
        tool_path = self.workspace_path / f"{tool_name}.py"
        
        try:
            result = subprocess.run(
                ['python3', str(tool_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                'status': 'success',
                'output': result.stdout,
                'tool_used': tool_name,
                'execution_time': '...'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'tool_used': tool_name
            }
    
    def get_tool_description(self, tool_name: str) -> str:
        """Get human-readable description of tool"""
        tool_info = self.tools.get(tool_name)
        if tool_info:
            return tool_info.description
        return "Unknown tool"

@dataclass
class ToolInfo:
    """Information about a workspace tool"""
    name: str
    path: Path
    description: str
    capabilities: List[str]
    last_modified: datetime
```

### ConversationManager Class

```python
class ConversationManager:
    """Manages conversation context and history"""
    
    def __init__(self):
        self.history: List[Dict[str, Any]] = []
        self.context: Dict[str, Any] = {}
        self.workspace_info: Dict[str, Any] = {}
    
    def add_interaction(self, question: str, result: Dict[str, Any]):
        """Add a Q&A pair to history"""
        
    def get_context(self) -> Dict[str, Any]:
        """Get current conversation context"""
        
    def resolve_reference(self, text: str) -> Optional[Dict[str, Any]]:
        """Resolve references like 'them', 'that', 'previous'"""
        
    def scan_workspace(self):
        """Scan workspace for available resources"""
```

### QueryOrchestrator Class

```python
class QueryOrchestrator:
    """Orchestrates complex multi-step queries"""
    
    def __init__(self, conversation_manager, tools):
        self.conversation_manager = conversation_manager
        self.tools = tools
        self.execution_plan: List[Dict[str, Any]] = []
    
    def create_execution_plan(self, parsed_query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create a multi-step execution plan"""
        
    def execute_plan(self, plan: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute the plan and aggregate results"""
        
    def should_visualize(self, result: Dict[str, Any]) -> bool:
        """Determine if results should be visualized"""
```

### LLMOrchestrator Class

```python
class LLMOrchestrator:
    """Uses LLM for high-level reasoning and conversation management"""
    
    def __init__(self, claude_client, conversation_manager, available_tools):
        self.claude_client = claude_client
        self.conversation_manager = conversation_manager
        self.available_tools = available_tools
        self.entity_parser = EntityParser()  # Fast, deterministic parsing
    
    def plan_execution(self, question: str) -> ExecutionPlan:
        """
        Use LLM to create execution plan with tool calls.
        Similar to how Kiro plans tool usage.
        """
        
    def generate_response(self, results: Dict[str, Any]) -> str:
        """
        Use LLM to synthesize results into natural language response.
        Include insights, explanations, and suggestions.
        """
        
    def detect_ambiguity(self, question: str, context: Dict[str, Any]) -> Optional[str]:
        """Use LLM to detect ambiguity and generate clarifying questions"""
        
    def understand_reference(self, question: str, history: List[Dict]) -> Dict[str, Any]:
        """Use LLM to resolve references like 'them', 'that', 'compare those'"""

class EntityParser:
    """Fast, deterministic entity extraction (no LLM needed)"""
    
    def extract_entities(self, question: str) -> Dict[str, Any]:
        """Use regex and keyword matching for entity extraction"""
        
    def extract_job_function(self, text: str) -> Optional[str]:
        """Extract job function using keyword matching"""
        
    def extract_job_level(self, text: str) -> Optional[str]:
        """Extract job level using pattern matching"""
```

### VisualizationEngine Class

```python
class VisualizationEngine:
    """Creates professional visualizations"""
    
    def __init__(self, output_dir: str = "charts"):
        self.output_dir = Path(output_dir)
        self.style_config = self._load_style_config()
    
    def auto_visualize(self, data: pd.DataFrame, analysis_type: str) -> List[str]:
        """Automatically create appropriate visualizations"""
        
    def create_salary_distribution(self, data: pd.DataFrame, title: str) -> str:
        """Create salary distribution chart"""
        
    def create_comparison_chart(self, data: pd.DataFrame, func1: str, func2: str) -> str:
        """Create side-by-side comparison chart"""
        
    def create_progression_chart(self, data: pd.DataFrame, function: str) -> str:
        """Create career progression chart"""
        
    def create_multi_panel_overview(self, data: pd.DataFrame, function: str) -> str:
        """Create comprehensive multi-panel visualization"""
```

### AnalysisEngine Class

```python
class AnalysisEngine:
    """Performs sophisticated data analysis"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def analyze_salary_distribution(self, filters: Dict[str, Any]) -> pd.DataFrame:
        """Analyze salary distribution with percentiles"""
        
    def compare_functions(self, func1: str, func2: str, level: Optional[str] = None) -> Dict[str, Any]:
        """Compare two job functions with detailed metrics"""
        
    def analyze_progression(self, function: str) -> pd.DataFrame:
        """Analyze career progression within a function"""
        
    def identify_insights(self, data: pd.DataFrame, analysis_type: str) -> List[str]:
        """Identify key insights from data"""
        
    def generate_summary(self, data: pd.DataFrame, analysis_type: str) -> str:
        """Generate executive summary"""
```

### ResultFormatter Class

```python
class ResultFormatter:
    """Formats results for display"""
    
    def format_table(self, data: pd.DataFrame, title: str) -> str:
        """Format data as a professional table"""
        
    def format_summary(self, summary: Dict[str, Any]) -> str:
        """Format executive summary"""
        
    def format_comparison(self, comparison: Dict[str, Any]) -> str:
        """Format comparison results"""
        
    def format_insights(self, insights: List[str]) -> str:
        """Format insights with visual hierarchy"""
```

## Data Models

### ConversationHistory

```python
@dataclass
class ConversationHistory:
    timestamp: datetime
    question: str
    parsed_query: Dict[str, Any]
    execution_plan: List[Dict[str, Any]]
    results: Dict[str, Any]
    visualizations: List[str]
    insights: List[str]
```

### ExecutionStep

```python
@dataclass
class ExecutionStep:
    step_id: int
    tool_name: str
    parameters: Dict[str, Any]
    dependencies: List[int]
    status: str  # pending, running, completed, failed
    result: Optional[Dict[str, Any]]
```

### AnalysisResult

```python
@dataclass
class AnalysisResult:
    query_type: str
    data: pd.DataFrame
    summary: Dict[str, Any]
    insights: List[str]
    visualizations: List[str]
    suggestions: List[str]
    metadata: Dict[str, Any]
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Context Preservation
*For any* sequence of questions, when a user references a previous query, the system should correctly resolve the reference and maintain consistent context throughout the conversation
**Validates: Requirements 1.3, 5.4**

### Property 2: Visualization Appropriateness
*For any* dataset returned from a query, the automatically selected visualization type should be appropriate for the data structure and analysis type
**Validates: Requirements 2.1**

### Property 3: Query Decomposition Correctness
*For any* complex multi-step question, the execution plan should contain all necessary steps in the correct dependency order
**Validates: Requirements 1.4**

### Property 4: Insight Relevance
*For any* analysis result, all generated insights should be directly supported by the data and relevant to the user's question
**Validates: Requirements 3.5**

### Property 5: Graceful Degradation
*For any* failure scenario, the system should provide a helpful error message and suggest alternative approaches without crashing
**Validates: Requirements 7.1, 7.2, 7.3**

### Property 6: Format Consistency
*For any* numerical output, formatting should be consistent (thousands separators, decimal places, currency symbols) across all displays
**Validates: Requirements 6.2**

### Property 7: Script Quality
*For any* generated script, it should be syntactically valid Python, follow PEP 8 guidelines, and execute without errors on valid inputs
**Validates: Requirements 4.1, 4.2, 4.5**

### Property 8: Comparison Completeness
*For any* comparison between two entities, the result should include both absolute differences and percentage changes
**Validates: Requirements 8.1**

### Property 9: Suggestion Relevance
*For any* completed query, suggested next steps should be logically related to the current analysis
**Validates: Requirements 9.1**

### Property 10: Export Integrity
*For any* exported data or report, the content should exactly match what was displayed to the user
**Validates: Requirements 10.1, 10.2, 10.3**

### Property 11: Tool Reuse Preference (NEW)
*For any* user query, if an existing workspace tool can satisfy the request, the system should use that tool rather than creating new code
**Validates: Requirements 11.1 (NEW)**

## Error Handling

### Error Categories

1. **User Input Errors**
   - Ambiguous questions → Ask clarifying questions
   - Invalid entities → Suggest corrections
   - Unsupported operations → Explain limitations

2. **Data Errors**
   - Missing data → Suggest alternative queries
   - Empty results → Recommend broadening criteria
   - Data quality issues → Warn and proceed with caveats

3. **System Errors**
   - Database connection failures → Retry with exponential backoff
   - Claude API failures → Fall back to keyword matching
   - Visualization errors → Provide tabular output instead

4. **Script Generation Errors**
   - Syntax errors → Fix and regenerate
   - Runtime errors → Add error handling
   - Dependency errors → Check and install requirements

### Error Handling Strategy

```python
class ErrorHandler:
    """Centralized error handling"""
    
    def handle_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle errors with appropriate recovery strategies"""
        
        if isinstance(error, DatabaseError):
            return self._handle_database_error(error, context)
        elif isinstance(error, ClaudeAPIError):
            return self._handle_api_error(error, context)
        elif isinstance(error, VisualizationError):
            return self._handle_visualization_error(error, context)
        else:
            return self._handle_generic_error(error, context)
    
    def _handle_database_error(self, error, context):
        """Handle database errors with retry logic"""
        
    def _handle_api_error(self, error, context):
        """Handle API errors with fallback"""
        
    def _handle_visualization_error(self, error, context):
        """Handle visualization errors with alternatives"""
```

## Testing Strategy

### Unit Testing
- Test each component in isolation
- Mock external dependencies (database, Claude API)
- Test error handling paths
- Verify data transformations

### Integration Testing
- Test component interactions
- Test end-to-end query flows
- Test visualization generation
- Test script execution

### Property-Based Testing
- Use Hypothesis library for Python
- Generate random queries and verify properties
- Test edge cases automatically
- Verify invariants hold across inputs

### User Acceptance Testing
- Test with real compensation questions
- Verify output quality and relevance
- Test conversation flow
- Gather feedback on insights and suggestions

## Implementation Phases

### Phase 1: Core Infrastructure (Week 1-2)
- Implement ConversationManager
- Implement QueryOrchestrator
- Enhance NLU with context awareness
- Add comprehensive error handling

### Phase 2: Analysis Enhancement (Week 3-4)
- Implement AnalysisEngine
- Add insight generation
- Implement ResultFormatter
- Add summary generation

### Phase 3: Visualization (Week 5-6)
- Implement VisualizationEngine
- Create chart templates
- Add auto-visualization logic
- Implement multi-panel layouts

### Phase 4: Advanced Features (Week 7-8)
- Add proactive suggestions
- Implement export capabilities
- Add report generation
- Enhance script generation

### Phase 5: Polish & Testing (Week 9-10)
- Comprehensive testing
- Performance optimization
- Documentation
- User feedback integration

## Performance Considerations

- **Caching**: Cache database query results for repeated questions
- **Lazy Loading**: Load visualization libraries only when needed
- **Async Operations**: Use async for Claude API calls
- **Connection Pooling**: Reuse database connections
- **Result Pagination**: Limit initial results, offer to show more

## Security Considerations

- **SQL Injection**: Always use parameterized queries
- **API Key Protection**: Never log or expose API keys
- **File System Access**: Restrict script generation to designated directories
- **Input Validation**: Sanitize all user inputs
- **Rate Limiting**: Implement rate limiting for API calls
