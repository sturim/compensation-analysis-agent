#!/usr/bin/env python3
"""
Error Handler - Centralized error handling with graceful degradation
"""

import time
import sqlite3
from typing import Dict, Any, Optional, Callable
from functools import wraps


class DatabaseError(Exception):
    """Database-related errors"""
    pass


class ClaudeAPIError(Exception):
    """Claude API-related errors"""
    pass


class VisualizationError(Exception):
    """Visualization-related errors"""
    pass


class ErrorHandler:
    """
    Centralized error handling with appropriate recovery strategies.
    
    Provides graceful degradation and helpful error messages.
    """
    
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self.error_log = []
    
    def handle_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle errors with appropriate recovery strategies.
        
        Args:
            error: The exception that occurred
            context: Context about what was being attempted
            
        Returns:
            Recovery result with status and message
        """
        # Log the error
        self._log_error(error, context)
        
        # Route to specific handler
        if isinstance(error, DatabaseError) or isinstance(error, sqlite3.Error):
            return self._handle_database_error(error, context)
        elif isinstance(error, ClaudeAPIError):
            return self._handle_api_error(error, context)
        elif isinstance(error, VisualizationError):
            return self._handle_visualization_error(error, context)
        else:
            return self._handle_generic_error(error, context)
    
    def _handle_database_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle database errors with retry logic.
        
        Common issues:
        - Connection failures
        - Lock timeouts
        - Query syntax errors
        """
        error_msg = str(error).lower()
        
        # Connection errors - suggest retry
        if 'unable to open' in error_msg or 'connection' in error_msg:
            return {
                'status': 'error',
                'type': 'database_connection',
                'message': 'Unable to connect to database',
                'suggestion': 'Check that compensation_data.db exists and is accessible',
                'recovery': 'retry',
                'user_message': (
                    "❌ Database connection failed.\n"
                    "   • Check that compensation_data.db exists\n"
                    "   • Verify file permissions\n"
                    "   • Try again in a moment"
                )
            }
        
        # Lock errors - suggest retry with delay
        elif 'locked' in error_msg:
            return {
                'status': 'error',
                'type': 'database_locked',
                'message': 'Database is locked',
                'suggestion': 'Wait a moment and retry',
                'recovery': 'retry_with_delay',
                'user_message': (
                    "⏳ Database is temporarily locked.\n"
                    "   • Another process may be using it\n"
                    "   • Retrying automatically..."
                )
            }
        
        # Query errors - suggest alternative
        elif 'syntax' in error_msg or 'no such column' in error_msg:
            return {
                'status': 'error',
                'type': 'query_error',
                'message': f'Query error: {error}',
                'suggestion': 'Try a simpler query or different search terms',
                'recovery': 'fallback',
                'user_message': (
                    "❌ Query failed.\n"
                    f"   • Error: {error}\n"
                    "   • Try rephrasing your question\n"
                    "   • Use simpler search terms"
                )
            }
        
        # Generic database error
        else:
            return {
                'status': 'error',
                'type': 'database_error',
                'message': f'Database error: {error}',
                'suggestion': 'Check database integrity',
                'recovery': 'none',
                'user_message': (
                    f"❌ Database error: {error}\n"
                    "   • The database may be corrupted\n"
                    "   • Contact support if this persists"
                )
            }
    
    def _handle_api_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle API errors with fallback.
        
        Common issues:
        - Rate limiting
        - Authentication failures
        - Network errors
        """
        error_msg = str(error).lower()
        
        # Rate limiting
        if 'rate limit' in error_msg or '429' in error_msg:
            return {
                'status': 'error',
                'type': 'rate_limit',
                'message': 'API rate limit exceeded',
                'suggestion': 'Wait before retrying',
                'recovery': 'fallback',
                'user_message': (
                    "⏳ API rate limit reached.\n"
                    "   • Falling back to basic mode\n"
                    "   • Results will be less detailed"
                )
            }
        
        # Authentication errors
        elif 'auth' in error_msg or '401' in error_msg or '403' in error_msg:
            return {
                'status': 'error',
                'type': 'authentication',
                'message': 'API authentication failed',
                'suggestion': 'Check API key configuration',
                'recovery': 'fallback',
                'user_message': (
                    "❌ API authentication failed.\n"
                    "   • Check ANTHROPIC_API_KEY in .env\n"
                    "   • Falling back to basic mode"
                )
            }
        
        # Network errors
        elif 'network' in error_msg or 'timeout' in error_msg or 'connection' in error_msg:
            return {
                'status': 'error',
                'type': 'network',
                'message': 'Network error',
                'suggestion': 'Check internet connection',
                'recovery': 'retry',
                'user_message': (
                    "🌐 Network error.\n"
                    "   • Check internet connection\n"
                    "   • Retrying..."
                )
            }
        
        # Generic API error
        else:
            return {
                'status': 'error',
                'type': 'api_error',
                'message': f'API error: {error}',
                'suggestion': 'Falling back to basic mode',
                'recovery': 'fallback',
                'user_message': (
                    f"⚠️  API error: {error}\n"
                    "   • Falling back to basic mode\n"
                    "   • Functionality may be limited"
                )
            }
    
    def _handle_visualization_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle visualization errors with alternatives.
        
        Common issues:
        - Missing data
        - Invalid chart types
        - File system errors
        """
        error_msg = str(error).lower()
        
        # Missing data
        if 'empty' in error_msg or 'no data' in error_msg:
            return {
                'status': 'error',
                'type': 'no_data',
                'message': 'No data to visualize',
                'suggestion': 'Broaden search criteria',
                'recovery': 'skip_visualization',
                'user_message': (
                    "📊 Cannot create chart - no data available.\n"
                    "   • Try broader search terms\n"
                    "   • Check that data exists for this query"
                )
            }
        
        # File system errors
        elif 'permission' in error_msg or 'cannot write' in error_msg:
            return {
                'status': 'error',
                'type': 'file_system',
                'message': 'Cannot save chart',
                'suggestion': 'Check directory permissions',
                'recovery': 'skip_visualization',
                'user_message': (
                    "❌ Cannot save chart.\n"
                    "   • Check charts/ directory permissions\n"
                    "   • Continuing without visualization"
                )
            }
        
        # Generic visualization error
        else:
            return {
                'status': 'error',
                'type': 'visualization_error',
                'message': f'Visualization error: {error}',
                'suggestion': 'Providing tabular output instead',
                'recovery': 'skip_visualization',
                'user_message': (
                    f"⚠️  Chart creation failed: {error}\n"
                    "   • Showing data in table format instead"
                )
            }
    
    def _handle_generic_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle generic errors"""
        return {
            'status': 'error',
            'type': 'generic',
            'message': f'Unexpected error: {error}',
            'suggestion': 'Try again or rephrase your question',
            'recovery': 'none',
            'user_message': (
                f"❌ Unexpected error: {error}\n"
                "   • Try rephrasing your question\n"
                "   • Contact support if this persists"
            )
        }
    
    def _log_error(self, error: Exception, context: Dict[str, Any]):
        """Log error for debugging"""
        self.error_log.append({
            'timestamp': time.time(),
            'error': str(error),
            'type': type(error).__name__,
            'context': context
        })
    
    def retry_with_backoff(self, func: Callable, *args, **kwargs) -> Any:
        """
        Retry a function with exponential backoff.
        
        Args:
            func: Function to retry
            *args, **kwargs: Arguments to pass to function
            
        Returns:
            Function result or raises last exception
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt < self.max_retries - 1:
                    # Exponential backoff: 1s, 2s, 4s
                    delay = 2 ** attempt
                    print(f"   ⏳ Retry {attempt + 1}/{self.max_retries} in {delay}s...")
                    time.sleep(delay)
                else:
                    print(f"   ❌ All retries failed")
        
        # All retries failed
        raise last_exception


def with_error_handling(error_handler: ErrorHandler):
    """
    Decorator for automatic error handling.
    
    Usage:
        @with_error_handling(error_handler)
        def my_function():
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                context = {
                    'function': func.__name__,
                    'args': args,
                    'kwargs': kwargs
                }
                result = error_handler.handle_error(e, context)
                
                # Print user message
                if 'user_message' in result:
                    print(result['user_message'])
                
                # Return error result
                return result
        
        return wrapper
    return decorator


if __name__ == "__main__":
    # Test error handler
    print("="*70)
    print("ERROR HANDLER TEST")
    print("="*70)
    
    handler = ErrorHandler()
    
    # Test database error
    print("\n1. Database Error:")
    db_error = sqlite3.OperationalError("unable to open database file")
    result = handler.handle_error(db_error, {'operation': 'query'})
    print(result['user_message'])
    
    # Test API error
    print("\n2. API Error:")
    api_error = ClaudeAPIError("rate limit exceeded")
    result = handler.handle_error(api_error, {'operation': 'generate'})
    print(result['user_message'])
    
    # Test visualization error
    print("\n3. Visualization Error:")
    viz_error = VisualizationError("no data to visualize")
    result = handler.handle_error(viz_error, {'operation': 'chart'})
    print(result['user_message'])
