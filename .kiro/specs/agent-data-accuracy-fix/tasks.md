# Implementation Plan

- [x] 1. Create result validation infrastructure
  - Create ResultValidator class to verify query completeness
  - Implement validation methods for aggregation and count verification
  - Add discrepancy detection logic
  - _Requirements: 1.3, 1.4, 4.1, 4.4_

- [ ]* 1.1 Write property test for aggregation invariant
  - **Property 4: Aggregation invariant**
  - **Validates: Requirements 1.4, 4.1**

- [x] 2. Create query logging infrastructure
  - Create QueryLogger class for comprehensive query debugging
  - Implement logging for SQL queries, parameters, and result counts
  - Add transformation logging to track data flow
  - _Requirements: 2.1, 2.2, 2.3_

- [x] 3. Fix query builder to remove data loss
  - Remove aggressive WHERE filters for Roll-Up and Executive levels
  - Make LIMIT clause configurable with sensible defaults
  - Add parameters for include_rollups and include_executives
  - Update _query_database method signature
  - _Requirements: 1.1, 1.2, 1.5_

- [ ]* 3.1 Write property test for complete result retrieval
  - **Property 1: Complete result retrieval**
  - **Validates: Requirements 1.1**

- [ ]* 3.2 Write property test for job level completeness
  - **Property 2: Job level completeness**
  - **Validates: Requirements 1.2**

- [x] 4. Integrate validation into query execution
  - Add pre-query count to determine expected results
  - Add post-query validation to verify completeness
  - Integrate ResultValidator into _query_database method
  - Return validation results in query response
  - _Requirements: 4.1, 4.2, 4.4_

- [ ]* 4.1 Write property test for employee count accuracy
  - **Property 3: Employee count accuracy**
  - **Validates: Requirements 1.3, 4.1**

- [x] 5. Enhance entity parser with exact matching
  - Implement get_exact_match for case-insensitive matching
  - Add validate_against_db to check entities exist in database
  - Cache distinct job function values for performance
  - Update extract method to use exact matching
  - _Requirements: 3.1, 3.4_

- [ ]* 5.1 Write property test for case-insensitive matching
  - **Property 5: Case-insensitive matching**
  - **Validates: Requirements 3.1**

- [ ]* 5.2 Write property test for entity validation
  - **Property 6: Entity validation**
  - **Validates: Requirements 3.4**

- [x] 6. Add alternative suggestion with user confirmation
  - Implement suggest_alternatives method using fuzzy matching
  - Add requires_user_confirmation logic
  - Update agent to prompt user when approximation needed
  - Prevent automatic approximation without confirmation
  - _Requirements: 3.2, 3.3, 3.4_

- [x] 7. Update result formatting for transparency
  - Modify result format to include total_available count
  - Add indication when results are limited
  - Show "Showing X of Y records" message
  - Update ResultFormatter to display validation warnings
  - _Requirements: 4.2, 4.3_

- [ ]* 7.1 Write property test for limited result transparency
  - **Property 7: Limited result transparency**
  - **Validates: Requirements 4.2**

- [x] 8. Add comprehensive error handling
  - Implement error responses for no results found
  - Add partial results handling with suggestions
  - Implement data integrity issue alerts
  - Add invalid entity error responses with alternatives
  - _Requirements: 3.3, 4.3_

- [x] 9. Integrate query logger into execution flow
  - Add QueryLogger to EnhancedAgnoAgent initialization
  - Log queries before execution in _query_database
  - Log result counts at each transformation stage
  - Add debug mode flag to control logging verbosity
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 10. Add database indexes for performance
  - Create index on job_positions.job_function
  - Create index on job_positions.job_level
  - Verify index creation with EXPLAIN QUERY PLAN
  - _Requirements: Performance optimization_

- [x] 11. Update tests with real database data
  - Update existing unit tests to use actual database
  - Add integration test for Creative function (57 records)
  - Add integration test for multiple job levels (13 levels)
  - Add integration test for case variations
  - _Requirements: All requirements_

- [x] 12. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
