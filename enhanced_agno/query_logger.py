#!/usr/bin/env python3
"""
Query Logger - Comprehensive logging for debugging query issues
"""

from typing import List, Any, Optional
import time
from datetime import datetime


class QueryLogger:
    """Logs query execution details for debugging"""
    
    def __init__(self, enabled: bool = True, verbose: bool = False):
        """
        Initialize query logger.
        
        Args:
            enabled: Whether logging is enabled
            verbose: Whether to show verbose output
        """
        self.enabled = enabled
        self.verbose = verbose
        self.query_history = []
    
    def log_query(self, sql: str, params: List[Any]) -> None:
        """
        Log SQL query before execution.
        
        Args:
            sql: SQL query string
            params: Query parameters
        """
        if not self.enabled:
            return
        
        timestamp = datetime.now().isoformat()
        
        log_entry = {
            'timestamp': timestamp,
            'type': 'query',
            'sql': sql,
            'params': params
        }
        
        self.query_history.append(log_entry)
        
        if self.verbose:
            print(f"\n[{timestamp}] 🔍 SQL QUERY:")
            print(f"  SQL: {sql[:200]}..." if len(sql) > 200 else f"  SQL: {sql}")
            print(f"  Params: {params}")
    
    def log_result_count(self, count: int, stage: str) -> None:
        """
        Log record counts at each stage.
        
        Args:
            count: Number of records
            stage: Stage name (e.g., 'raw_query', 'after_filter', 'final')
        """
        if not self.enabled:
            return
        
        timestamp = datetime.now().isoformat()
        
        log_entry = {
            'timestamp': timestamp,
            'type': 'count',
            'stage': stage,
            'count': count
        }
        
        self.query_history.append(log_entry)
        
        if self.verbose:
            print(f"[{timestamp}] 📊 {stage}: {count} records")
    
    def log_transformation(
        self, 
        before_count: int, 
        after_count: int, 
        operation: str
    ) -> None:
        """
        Log data transformations.
        
        Args:
            before_count: Record count before transformation
            after_count: Record count after transformation
            operation: Description of operation
        """
        if not self.enabled:
            return
        
        timestamp = datetime.now().isoformat()
        
        log_entry = {
            'timestamp': timestamp,
            'type': 'transformation',
            'operation': operation,
            'before_count': before_count,
            'after_count': after_count,
            'delta': after_count - before_count
        }
        
        self.query_history.append(log_entry)
        
        if self.verbose:
            delta = after_count - before_count
            delta_str = f"+{delta}" if delta >= 0 else str(delta)
            print(f"[{timestamp}] 🔄 {operation}: {before_count} → {after_count} ({delta_str})")
    
    def log_execution_time(self, operation: str, duration_ms: float) -> None:
        """
        Log execution time for operations.
        
        Args:
            operation: Operation name
            duration_ms: Duration in milliseconds
        """
        if not self.enabled:
            return
        
        timestamp = datetime.now().isoformat()
        
        log_entry = {
            'timestamp': timestamp,
            'type': 'timing',
            'operation': operation,
            'duration_ms': duration_ms
        }
        
        self.query_history.append(log_entry)
        
        if self.verbose:
            print(f"[{timestamp}] ⏱️  {operation}: {duration_ms:.2f}ms")
    
    def log_validation(self, validation_result: Any) -> None:
        """
        Log validation results.
        
        Args:
            validation_result: ValidationResult object
        """
        if not self.enabled:
            return
        
        timestamp = datetime.now().isoformat()
        
        log_entry = {
            'timestamp': timestamp,
            'type': 'validation',
            'is_complete': validation_result.is_complete,
            'expected_count': validation_result.expected_count,
            'actual_count': validation_result.actual_count,
            'discrepancies': validation_result.discrepancies,
            'warnings': validation_result.warnings
        }
        
        self.query_history.append(log_entry)
        
        if self.verbose:
            status = "✅ PASS" if validation_result.is_complete else "❌ FAIL"
            print(f"[{timestamp}] {status} Validation:")
            print(f"  Expected: {validation_result.expected_count}")
            print(f"  Actual: {validation_result.actual_count}")
            if validation_result.discrepancies:
                print(f"  Discrepancies: {validation_result.discrepancies}")
            if validation_result.warnings:
                print(f"  Warnings: {validation_result.warnings}")
    
    def log_error(self, error: Exception, context: dict) -> None:
        """
        Log errors with context.
        
        Args:
            error: Exception that occurred
            context: Context dictionary with additional info
        """
        if not self.enabled:
            return
        
        timestamp = datetime.now().isoformat()
        
        log_entry = {
            'timestamp': timestamp,
            'type': 'error',
            'error': str(error),
            'error_type': type(error).__name__,
            'context': context
        }
        
        self.query_history.append(log_entry)
        
        if self.verbose:
            print(f"[{timestamp}] ❌ ERROR: {type(error).__name__}")
            print(f"  Message: {error}")
            print(f"  Context: {context}")
    
    def get_summary(self) -> dict:
        """
        Get summary of logged queries.
        
        Returns:
            Dictionary with query statistics
        """
        total_queries = sum(1 for entry in self.query_history if entry['type'] == 'query')
        total_errors = sum(1 for entry in self.query_history if entry['type'] == 'error')
        total_validations = sum(1 for entry in self.query_history if entry['type'] == 'validation')
        
        failed_validations = sum(
            1 for entry in self.query_history 
            if entry['type'] == 'validation' and not entry.get('is_complete', True)
        )
        
        return {
            'total_queries': total_queries,
            'total_errors': total_errors,
            'total_validations': total_validations,
            'failed_validations': failed_validations,
            'total_entries': len(self.query_history)
        }
    
    def clear_history(self) -> None:
        """Clear query history"""
        self.query_history = []
    
    def export_history(self) -> List[dict]:
        """
        Export query history.
        
        Returns:
            List of log entries
        """
        return self.query_history.copy()
