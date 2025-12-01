#!/usr/bin/env python3
"""
Result Validator - Validates query results for completeness and accuracy
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of validation checks"""
    is_complete: bool
    expected_count: int
    actual_count: int
    discrepancies: List[str]
    warnings: List[str]


class ResultValidator:
    """Validates query results for data integrity"""
    
    def validate_completeness(
        self, 
        query_results: Dict[str, Any],
        expected_count: int
    ) -> ValidationResult:
        """
        Verify all expected records are present in query results.
        
        Args:
            query_results: The results from database query
            expected_count: Expected number of records
            
        Returns:
            ValidationResult with completeness check
        """
        actual_count = query_results.get('row_count', 0)
        discrepancies = []
        warnings = []
        
        if actual_count < expected_count:
            discrepancies.append(
                f"Missing records: expected {expected_count}, got {actual_count}"
            )
        elif actual_count > expected_count:
            warnings.append(
                f"More records than expected: expected {expected_count}, got {actual_count}"
            )
        
        is_complete = actual_count == expected_count
        
        return ValidationResult(
            is_complete=is_complete,
            expected_count=expected_count,
            actual_count=actual_count,
            discrepancies=discrepancies,
            warnings=warnings
        )
    
    def validate_aggregation(
        self,
        grouped_results: List[Dict],
        total_count: int
    ) -> ValidationResult:
        """
        Verify grouped counts sum to total count.
        
        Args:
            grouped_results: List of grouped records with employee counts
            total_count: Expected total employee count
            
        Returns:
            ValidationResult with aggregation check
        """
        # Sum employee counts from grouped results
        sum_of_groups = sum(
            record.get('employees', 0) 
            for record in grouped_results
        )
        
        discrepancies = []
        warnings = []
        
        if sum_of_groups != total_count:
            discrepancies.append(
                f"Aggregation mismatch: sum of groups ({sum_of_groups}) "
                f"!= total count ({total_count})"
            )
        
        is_complete = sum_of_groups == total_count
        
        return ValidationResult(
            is_complete=is_complete,
            expected_count=total_count,
            actual_count=sum_of_groups,
            discrepancies=discrepancies,
            warnings=warnings
        )
    
    def detect_discrepancies(
        self,
        results: Dict[str, Any]
    ) -> List[str]:
        """
        Detect and report data integrity issues in results.
        
        Args:
            results: Query results dictionary
            
        Returns:
            List of discrepancy messages
        """
        discrepancies = []
        
        # Check if status indicates issues
        if results.get('status') == 'error':
            discrepancies.append(f"Query error: {results.get('message', 'Unknown error')}")
            return discrepancies
        
        # Check for empty results when data expected
        if results.get('status') == 'no_results':
            discrepancies.append("No results returned from query")
            return discrepancies
        
        # Check row_count vs data length consistency
        row_count = results.get('row_count', 0)
        data = results.get('data', [])
        if len(data) != row_count:
            discrepancies.append(
                f"Row count mismatch: row_count={row_count}, len(data)={len(data)}"
            )
        
        # Check total_employees vs sum of employee counts
        total_employees = results.get('total_employees', 0)
        if data:
            sum_employees = sum(record.get('employees', 0) for record in data)
            if sum_employees != total_employees:
                discrepancies.append(
                    f"Employee count mismatch: total_employees={total_employees}, "
                    f"sum(employees)={sum_employees}"
                )
        
        return discrepancies
    
    def validate_query_result(
        self,
        results: Dict[str, Any],
        expected_record_count: Optional[int] = None,
        expected_employee_count: Optional[int] = None
    ) -> ValidationResult:
        """
        Comprehensive validation of query results.
        
        Args:
            results: Query results dictionary
            expected_record_count: Expected number of records (optional)
            expected_employee_count: Expected total employee count (optional)
            
        Returns:
            ValidationResult with all checks
        """
        discrepancies = self.detect_discrepancies(results)
        warnings = []
        
        # Validate record count if expected value provided
        if expected_record_count is not None:
            actual_count = results.get('row_count', 0)
            if actual_count != expected_record_count:
                discrepancies.append(
                    f"Record count mismatch: expected {expected_record_count}, "
                    f"got {actual_count}"
                )
        
        # Validate employee count if expected value provided
        if expected_employee_count is not None:
            actual_employee_count = results.get('total_employees', 0)
            if actual_employee_count != expected_employee_count:
                discrepancies.append(
                    f"Employee count mismatch: expected {expected_employee_count}, "
                    f"got {actual_employee_count}"
                )
        
        is_complete = len(discrepancies) == 0
        
        return ValidationResult(
            is_complete=is_complete,
            expected_count=expected_record_count or 0,
            actual_count=results.get('row_count', 0),
            discrepancies=discrepancies,
            warnings=warnings
        )
