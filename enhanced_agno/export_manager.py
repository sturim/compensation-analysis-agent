#!/usr/bin/env python3
"""
Export Manager - Handles exporting results to various formats
"""

import os
import json
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd


class ExportManager:
    """
    Manages exporting analysis results to various formats.
    
    Supports:
    - CSV export
    - JSON export
    - Markdown reports
    """
    
    def __init__(self, export_dir: str = "exports"):
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.export_dir / "csv").mkdir(exist_ok=True)
        (self.export_dir / "json").mkdir(exist_ok=True)
        (self.export_dir / "reports").mkdir(exist_ok=True)
    
    def export_to_csv(self, data: Dict[str, Any], filename: str = None) -> str:
        """
        Export data to CSV format.
        
        Args:
            data: Results dictionary with 'data' key containing records
            filename: Optional filename (auto-generated if not provided)
            
        Returns:
            Path to exported file
        """
        records = data.get('data', [])
        if not records:
            raise ValueError("No data to export")
        
        df = pd.DataFrame(records)
        
        # Generate filename if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"export_{timestamp}.csv"
        
        # Ensure .csv extension
        if not filename.endswith('.csv'):
            filename += '.csv'
        
        filepath = self.export_dir / "csv" / filename
        
        try:
            df.to_csv(filepath, index=False)
            return str(filepath)
        except Exception as e:
            raise IOError(f"Failed to export CSV: {e}")
    
    def export_to_json(self, data: Dict[str, Any], filename: str = None, 
                      include_metadata: bool = True) -> str:
        """
        Export data to JSON format.
        
        Args:
            data: Results dictionary
            filename: Optional filename (auto-generated if not provided)
            include_metadata: Whether to include metadata in export
            
        Returns:
            Path to exported file
        """
        # Generate filename if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"export_{timestamp}.json"
        
        # Ensure .json extension
        if not filename.endswith('.json'):
            filename += '.json'
        
        filepath = self.export_dir / "json" / filename
        
        # Prepare export data
        export_data = {}
        
        if include_metadata:
            export_data['metadata'] = {
                'export_date': datetime.now().isoformat(),
                'row_count': data.get('row_count', 0),
                'status': data.get('status', 'unknown')
            }
        
        export_data['data'] = data.get('data', [])
        
        if 'summary' in data:
            export_data['summary'] = data['summary']
        
        if 'insights' in data:
            export_data['insights'] = data['insights']
        
        try:
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2)
            return str(filepath)
        except Exception as e:
            raise IOError(f"Failed to export JSON: {e}")
    
    def generate_report(self, question: str, results: Dict[str, Any], 
                       response: str, filename: str = None) -> str:
        """
        Generate a markdown report with embedded images.
        
        Args:
            question: The user's question
            results: Query results
            response: Generated response
            filename: Optional filename (auto-generated if not provided)
            
        Returns:
            Path to generated report
        """
        # Generate filename if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_{timestamp}.md"
        
        # Ensure .md extension
        if not filename.endswith('.md'):
            filename += '.md'
        
        filepath = self.export_dir / "reports" / filename
        
        # Build report content
        report_lines = []
        
        # Header
        report_lines.append("# Compensation Analysis Report")
        report_lines.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"\n**Question:** {question}")
        report_lines.append("\n---\n")
        
        # Executive Summary
        if 'summary' in results:
            report_lines.append("## Executive Summary\n")
            report_lines.append(results['summary'])
            report_lines.append("\n")
        
        # Key Insights
        if 'insights' in results and results['insights']:
            report_lines.append("## Key Insights\n")
            for i, insight in enumerate(results['insights'], 1):
                report_lines.append(f"{i}. {insight}")
            report_lines.append("\n")
        
        # Data Table
        if 'data' in results and results['data']:
            report_lines.append("## Detailed Data\n")
            df = pd.DataFrame(results['data'])
            report_lines.append(df.to_markdown(index=False))
            report_lines.append("\n")
        
        # Chart
        if 'chart_path' in results:
            chart_path = results['chart_path']
            # Convert to relative path if possible
            if os.path.exists(chart_path):
                rel_path = os.path.relpath(chart_path, self.export_dir / "reports")
                report_lines.append("## Visualization\n")
                report_lines.append(f"![Chart]({rel_path})\n")
        
        # Analysis Details
        report_lines.append("## Analysis Details\n")
        report_lines.append(response)
        report_lines.append("\n")
        
        # Metadata
        report_lines.append("---\n")
        report_lines.append("## Metadata\n")
        if 'row_count' in results:
            report_lines.append(f"- **Rows:** {results['row_count']}")
        if 'total_employees' in results:
            report_lines.append(f"- **Total Employees:** {results['total_employees']:,}")
        if 'tool_used' in results:
            report_lines.append(f"- **Tool Used:** {results['tool_used']}")
        
        # Write report
        try:
            with open(filepath, 'w') as f:
                f.write('\n'.join(report_lines))
            return str(filepath)
        except Exception as e:
            raise IOError(f"Failed to generate report: {e}")
    
    def export_all(self, question: str, results: Dict[str, Any], 
                  response: str, base_filename: str = None) -> Dict[str, str]:
        """
        Export to all formats at once.
        
        Args:
            question: The user's question
            results: Query results
            response: Generated response
            base_filename: Base filename for all exports
            
        Returns:
            Dictionary mapping format to filepath
        """
        if not base_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"export_{timestamp}"
        
        exports = {}
        
        # CSV export
        try:
            csv_path = self.export_to_csv(results, f"{base_filename}.csv")
            exports['csv'] = csv_path
        except Exception as e:
            exports['csv'] = f"Failed: {e}"
        
        # JSON export
        try:
            json_path = self.export_to_json(results, f"{base_filename}.json")
            exports['json'] = json_path
        except Exception as e:
            exports['json'] = f"Failed: {e}"
        
        # Report export
        try:
            report_path = self.generate_report(question, results, response, f"{base_filename}.md")
            exports['report'] = report_path
        except Exception as e:
            exports['report'] = f"Failed: {e}"
        
        return exports
    
    def list_exports(self, format_type: str = None) -> List[str]:
        """
        List all exported files.
        
        Args:
            format_type: Optional filter by format (csv, json, report)
            
        Returns:
            List of file paths
        """
        files = []
        
        if format_type is None or format_type == 'csv':
            files.extend([str(f) for f in (self.export_dir / "csv").glob("*.csv")])
        
        if format_type is None or format_type == 'json':
            files.extend([str(f) for f in (self.export_dir / "json").glob("*.json")])
        
        if format_type is None or format_type == 'report':
            files.extend([str(f) for f in (self.export_dir / "reports").glob("*.md")])
        
        return sorted(files, reverse=True)  # Most recent first


if __name__ == "__main__":
    # Test export manager
    print("="*70)
    print("EXPORT MANAGER TEST")
    print("="*70)
    
    manager = ExportManager()
    
    # Test data
    test_results = {
        'status': 'success',
        'row_count': 3,
        'total_employees': 18969,
        'data': [
            {'job_level': 'Entry (P1)', 'avg_salary': 105000, 'employees': 3368},
            {'job_level': 'Manager (M3)', 'avg_salary': 219000, 'employees': 8133},
            {'job_level': 'Director (M5)', 'avg_salary': 271000, 'employees': 7468},
        ],
        'summary': 'Average salary: $198,333 | 18,969 employees | 3 levels',
        'insights': [
            'Salary range spans $105K to $271K, a 158% difference',
            'Largest concentration at Manager (M3) with 8,133 employees',
        ]
    }
    
    # Test CSV export
    print("\n1. CSV Export:")
    csv_path = manager.export_to_csv(test_results, "test_export.csv")
    print(f"   ✅ Exported to: {csv_path}")
    
    # Test JSON export
    print("\n2. JSON Export:")
    json_path = manager.export_to_json(test_results, "test_export.json")
    print(f"   ✅ Exported to: {json_path}")
    
    # Test report generation
    print("\n3. Report Generation:")
    report_path = manager.generate_report(
        "What's the salary for Engineering?",
        test_results,
        "Engineering salaries range from $105K to $271K...",
        "test_report.md"
    )
    print(f"   ✅ Generated report: {report_path}")
    
    # List exports
    print("\n4. List Exports:")
    exports = manager.list_exports()
    for export in exports[:5]:  # Show first 5
        print(f"   • {export}")
