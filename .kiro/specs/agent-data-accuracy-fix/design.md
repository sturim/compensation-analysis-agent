# Design Document

## Overview

This design addresses a critical bug in the Enhanced Agno Agent where SQL queries return incomplete result sets. The root cause is the LIMIT 10 clause combined with WHERE conditions that filter out "Roll-Up" and "Executive" job levels. When a job function has more than 10 standard career levels, or when the filtering removes important data, users receive incomplete and misleading results.

The fix involves:
1. Removing arbitrary LIMIT clauses or making them configurable
2. Removing overly aggressive WHERE filters that exclude valid data
3. Adding validation to ensure query results match database record counts
4. Improving entity parsing to match exact job function names
5. Adding comprehensive logging for query debugging

## Architecture

### Current Architecture Issues

The current query flow has several problems:

```
User Query → Entity Parser → LLM Planner → Query Builder → SQL Execution → Results
                                                ↓
                                          LIMIT 10 (arbitrary)
                                          Filter out Roll-Ups
                                          Filter out Executives
                                                ↓
                                          Missing 50% of data
```

### Proposed Architecture

```
User Query → Enhanced Entity Parser → LLM Planner → Query Builder → SQL Execution
                    ↓                                      ↓              ↓
              Exact matching                      Configurable      Validation
              Case-insensitive                    LIMIT             Layer
              DB validation                       Smart filters         ↓
                                                                   Complete Results
```

## Components and Interfaces

### 1. Enhanced Entity Parser

**Location:** `enhanced_agno/entity_parser.py`

**Changes:**
- Add exact matching for job functions against database values
- Implement case-insensitive matching
- Add validation that extracted entities exist in the database
- Return confidence scores for matches

**New Interface:**
```python
class EntityParser:
    def extract(self, question: str) -> Dict[str, Any]:
        """Extract entities with database validation"""
        
    def validate_against_db(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Validate extracted entities exist in database"""
        
    def get_exact_match(self, term: str, db_values: List[str]) -> Optional[str]:
        """Find exact case-insensitive match in database values"""
        
    def suggest_alternatives(self, term: str, db_values: List[str], max_suggestions: int = 3) -> List[str]:
        """Suggest similar values when exact match not found"""
        
    def requires_user_confirmation(self, extracted: str, matched: str) -> bool:
        """Determine if user confirmation needed before using approximation"""
```

### 2. Query Builder with Validation

**Location:** `enhanced_agno_agent.py` (`_query_database` method)

**Changes:**
- Remove or make configurable the LIMIT 10 clause
- Remove WHERE filters for "Roll-Up" and "Executive" unless explicitly requested
- Add pre-query validation to count expected results
- Add post-query validation to verify completeness
- Add detailed logging of query construction and execution

**New Interface:**
```python
def _query_database(
    self, 
    entities: Dict[str, Any], 
    params: Dict[str, Any],
    limit: Optional[int] = None,
    include_rollups: bool = True,
    include_executives: bool = True
) -> Dict[str, Any]:
    """Query with validation and configurable filters"""
```

### 3. Result Validator

**Location:** `enhanced_agno/result_validator.py` (new file)

**Purpose:** Validate query results for completeness and accuracy

**Interface:**
```python
class ResultValidator:
    def validate_completeness(
        self, 
        query_results: Dict[str, Any],
        expected_count: int
    ) -> Dict[str, Any]:
        """Verify all expected records are present"""
        
    def validate_aggregation(
        self,
        grouped_results: List[Dict],
        total_count: int
    ) -> Dict[str, Any]:
        """Verify grouped counts sum to total"""
        
    def detect_discrepancies(
        self,
        results: Dict[str, Any]
    ) -> List[str]:
        """Detect and report data integrity issues"""
```

### 4. Query Logger

**Location:** `enhanced_agno/query_logger.py` (new file)

**Purpose:** Comprehensive logging for debugging query issues

**Interface:**
```python
class QueryLogger:
    def log_query(self, sql: str, params: List[Any]) -> None:
        """Log SQL query before execution"""
        
    def log_result_count(self, count: int, stage: str) -> None:
        """Log record counts at each stage"""
        
    def log_transformation(
        self, 
        before_count: int, 
        after_count: int, 
        operation: str
    ) -> None:
        """Log data transformations"""
```

## Data Models

### Query Result Model

```python
@dataclass
class QueryResult:
    status: str  # 'success', 'partial', 'error'
    data: List[Dict[str, Any]]
    row_count: int
    total_available: int  # Total records matching criteria
    validation: ValidationResult
    query_info: QueryInfo
```

### Validation Result Model

```python
@dataclass
class ValidationResult:
    is_complete: bool
    expected_count: int
    actual_count: int
    discrepancies: List[str]
    warnings: List[str]
```

### Query Info Model

```python
@dataclass
class QueryInfo:
    sql: str
    params: List[Any]
    execution_time_ms: float
    filters_applied: List[str]
    limit_applied: Optional[int]
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Complete result retrieval
*For any* job function query, the number of records returned SHALL equal the number of records in the database matching that job function (when no LIMIT is applied)
**Validates: Requirements 1.1**

### Property 2: Job level completeness
*For any* job function with N distinct job levels in the database, the aggregated results SHALL contain exactly N groups
**Validates: Requirements 1.2**

### Property 3: Employee count accuracy
*For any* query result, the sum of employee counts across all groups SHALL equal the sum of base_salary_lfy_emp_count in the database for matching records
**Validates: Requirements 1.3, 4.1**

### Property 4: Aggregation invariant
*For any* aggregated query result, the sum of grouped employee counts SHALL equal the total_employees field in the result
**Validates: Requirements 1.4, 4.1**

### Property 5: Case-insensitive matching
*For any* job function in the database, querying with different case variations (lowercase, uppercase, title case) SHALL return identical result sets
**Validates: Requirements 3.1**

### Property 6: Entity validation
*For any* extracted job function entity, it SHALL either match a value in the database's distinct job_function column or be flagged as invalid
**Validates: Requirements 3.4**

### Property 7: Limited result transparency
*For any* query with a LIMIT clause, the result SHALL include both the limited row count and the total available count
**Validates: Requirements 4.2**

## Error Handling

### Error Categories

1. **No Results Found**
   - Cause: Job function doesn't exist or no data available
   - Response: Suggest similar job functions from database
   - Example: "Creative" misspelled as "Creativ"

2. **Partial Results**
   - Cause: LIMIT applied, more data available
   - Response: Indicate total count and offer to show more
   - Example: "Showing 10 of 57 Creative positions"

3. **Data Integrity Issues**
   - Cause: Aggregation doesn't sum correctly
   - Response: Alert user and log diagnostic information
   - Example: "Warning: Sum of grouped counts (45) doesn't match total (57)"

4. **Invalid Entity**
   - Cause: Extracted entity doesn't exist in database
   - Response: Show available options and request user confirmation before using approximation
   - Example: "Job function 'Creatives' not found. Did you mean: Creative, Creative Services? Please confirm which one you'd like to use."
   - Behavior: System SHALL NOT automatically use an approximation without explicit user confirmation

### Error Response Format

```python
{
    "status": "error" | "warning" | "partial",
    "message": "User-friendly message",
    "details": {
        "error_type": "no_results" | "partial_results" | "integrity_issue",
        "suggestions": ["Alternative 1", "Alternative 2"],
        "diagnostic_info": {...}
    }
}
```

## Testing Strategy

### Unit Testing

We will write unit tests for:

1. **Entity Parser Exact Matching**
   - Test case: "creative" matches "Creative" in database
   - Test case: "ENGINEERING" matches "Engineering"
   - Test case: "invalid function" returns no match

2. **Query Builder Filter Logic**
   - Test case: include_rollups=False excludes Roll-Up levels
   - Test case: include_executives=True includes Executive levels
   - Test case: No LIMIT when limit=None

3. **Result Validator**
   - Test case: Detect when grouped counts don't sum to total
   - Test case: Detect when result count doesn't match expected
   - Test case: Pass validation when data is complete

### Property-Based Testing

We will use **Hypothesis** (Python's property-based testing library) to verify correctness properties. Each test will run a minimum of 100 iterations.

**Property-based tests will:**

1. **Test Complete Retrieval (Property 1)**
   - Generate: Random job function from database
   - Execute: Query without LIMIT
   - Verify: Result count matches database count for that function
   - Tag: **Feature: agent-data-accuracy-fix, Property 1: Complete result retrieval**

2. **Test Job Level Completeness (Property 2)**
   - Generate: Random job function from database
   - Execute: Query and aggregate by job level
   - Verify: Number of groups equals distinct job levels in database
   - Tag: **Feature: agent-data-accuracy-fix, Property 2: Job level completeness**

3. **Test Employee Count Accuracy (Property 3)**
   - Generate: Random job function and filters
   - Execute: Query and sum employee counts
   - Verify: Sum matches database SUM(base_salary_lfy_emp_count)
   - Tag: **Feature: agent-data-accuracy-fix, Property 3: Employee count accuracy**

4. **Test Aggregation Invariant (Property 4)**
   - Generate: Random query parameters
   - Execute: Query with aggregation
   - Verify: Sum of grouped counts equals total_employees field
   - Tag: **Feature: agent-data-accuracy-fix, Property 4: Aggregation invariant**

5. **Test Case-Insensitive Matching (Property 5)**
   - Generate: Random job function, random case variation
   - Execute: Query with different cases
   - Verify: All variations return identical results
   - Tag: **Feature: agent-data-accuracy-fix, Property 5: Case-insensitive matching**

6. **Test Entity Validation (Property 6)**
   - Generate: Mix of valid and invalid job function names
   - Execute: Entity extraction and validation
   - Verify: Valid names pass, invalid names are flagged
   - Tag: **Feature: agent-data-accuracy-fix, Property 6: Entity validation**

7. **Test Limited Result Transparency (Property 7)**
   - Generate: Random query with LIMIT
   - Execute: Query
   - Verify: Result contains both limited count and total count
   - Tag: **Feature: agent-data-accuracy-fix, Property 7: Limited result transparency**

### Integration Testing

Integration tests will verify the complete flow:

1. User query → Entity extraction → Query execution → Result validation
2. Test with known data: "Creative" should return 57 records
3. Test with multiple job levels: Verify all 13 Creative levels appear
4. Test with case variations: "creative", "CREATIVE", "Creative" return same results

### Test Data

We will use the actual compensation database for testing since it contains real-world complexity:
- 11,219 job positions
- 45 distinct job functions
- Multiple job levels per function
- Real data distribution

## Implementation Notes

### Critical Bug Location

The bug is in `enhanced_agno_agent.py`, `_query_database` method, lines ~280-320:

```python
# PROBLEMATIC CODE:
query = f"""
    ...
    WHERE {where_clause}
        AND {percentile_col} IS NOT NULL
        AND {percentile_col} > 0
        AND jp.job_level NOT LIKE '%Roll-Up%'      # ← Removes valid data
        AND jp.job_level NOT LIKE '%Executive%'    # ← Removes valid data
    GROUP BY jp.job_function, jp.job_level
    ORDER BY {order_by}
    LIMIT 10                                        # ← Arbitrary limit
"""
```

### Fix Strategy

1. **Remove aggressive filters** - Only filter Roll-Ups/Executives when explicitly requested
2. **Make LIMIT configurable** - Default to no limit, or use a high value like 100
3. **Add validation** - Count expected results before query, verify after
4. **Improve entity matching** - Use exact case-insensitive matching against DB values
5. **Add logging** - Log query, params, and result counts at each stage

### Backward Compatibility

To maintain backward compatibility:
- Add new parameters with sensible defaults
- Keep existing method signatures
- Add deprecation warnings for old behavior
- Provide migration guide for existing code

## Performance Considerations

### Query Performance

- Removing LIMIT may return more rows, but most job functions have < 20 levels
- Add indexes on job_function and job_level if not present
- Consider pagination for very large result sets

### Validation Performance

- Pre-query count adds one extra query (fast with indexes)
- Post-query validation is in-memory (negligible cost)
- Logging has minimal overhead

### Optimization Strategies

1. Cache distinct job function values for entity validation
2. Use EXPLAIN QUERY PLAN to optimize SQL
3. Add database indexes if missing:
   ```sql
   CREATE INDEX IF NOT EXISTS idx_job_function ON job_positions(job_function);
   CREATE INDEX IF NOT EXISTS idx_job_level ON job_positions(job_level);
   ```

## Migration Plan

### Phase 1: Add Validation (Non-Breaking)
- Add ResultValidator class
- Add validation to existing queries
- Log discrepancies but don't fail

### Phase 2: Fix Query Builder (Breaking)
- Remove aggressive filters
- Make LIMIT configurable
- Update tests

### Phase 3: Enhance Entity Parser (Non-Breaking)
- Add exact matching
- Add database validation
- Maintain backward compatibility

### Phase 4: Add Logging (Non-Breaking)
- Add QueryLogger class
- Integrate into query flow
- Add debug mode flag
