#!/usr/bin/env python3
"""
Result Formatter - Formats results for beautiful display
Makes output clear, organized, and professional
"""

from typing import Dict, List, Any
import pandas as pd


class ResultFormatter:
    """Formats results with rich text and visual hierarchy"""
    
    def __init__(self):
        # Box drawing characters
        self.box = {
            'tl': '╔', 'tr': '╗', 'bl': '╚', 'br': '╝',
            'h': '═', 'v': '║', 'cross': '╬',
            'top': '╦', 'bottom': '╩', 'left': '╠', 'right': '╣'
        }
    
    def format_response(self, question: str, results: Dict[str, Any], 
                       response: str) -> str:
        """
        Format complete response with all elements using rich visual hierarchy.
        
        This makes output much more readable and professional.
        """
        output = []
        
        # Header with question
        output.append(self._format_header("ANALYSIS RESULTS"))
        output.append("")
        output.append(f"❓ {question}")
        output.append("")
        
        # Summary box (if available) - Most important, show first
        if 'summary' in results:
            output.append(self._format_summary_box(results['summary']))
            output.append("")
        
        # DATA TABLE
        if 'data' in results and results['data']:
            df = pd.DataFrame(results['data'])
            output.append(self.format_table(df, "Detailed Data"))
            output.append("")
        
        # Insights section with visual hierarchy
        if 'insights' in results and results['insights']:
            output.append(self._format_insights_section(results['insights']))
            output.append("")
        
        # Main response in a box
        if response and response.strip():
            output.append(self._format_response_box(response))
            output.append("")
        
        # Metadata section
        metadata = []
        if 'chart_path' in results:
            metadata.append(f"📊 Chart: {results['chart_path']}")
        if 'tool_used' in results:
            metadata.append(f"🔧 Tool: {results['tool_used']}")
        if 'row_count' in results:
            metadata.append(f"📈 Rows: {results['row_count']}")
        
        if metadata:
            output.append(self._format_metadata_section(metadata))
            output.append("")
        
        # Footer
        output.append(self._format_footer())
        
        return "\n".join(output)
    
    def _format_summary_box(self, summary: str) -> str:
        """Format summary in a highlighted box"""
        width = min(max(len(summary) + 4, 70), 100)
        
        lines = []
        lines.append("┏" + "━" * (width - 2) + "┓")
        lines.append("┃" + " 📊 EXECUTIVE SUMMARY".ljust(width - 2) + "┃")
        lines.append("┣" + "━" * (width - 2) + "┫")
        
        # Wrap summary if too long
        if len(summary) > width - 4:
            words = summary.split()
            current_line = ""
            for word in words:
                if len(current_line) + len(word) + 1 <= width - 4:
                    current_line += word + " "
                else:
                    lines.append("┃ " + current_line.ljust(width - 3) + "┃")
                    current_line = word + " "
            if current_line:
                lines.append("┃ " + current_line.ljust(width - 3) + "┃")
        else:
            lines.append("┃ " + summary.ljust(width - 3) + "┃")
        
        lines.append("┗" + "━" * (width - 2) + "┛")
        
        return "\n".join(lines)
    
    def _format_insights_section(self, insights: List[str]) -> str:
        """Format insights with visual hierarchy"""
        lines = []
        lines.append("┌" + "─" * 68 + "┐")
        lines.append("│ 💡 KEY INSIGHTS".ljust(69) + "│")
        lines.append("├" + "─" * 68 + "┤")
        
        for i, insight in enumerate(insights, 1):
            # Wrap long insights
            if len(insight) > 64:
                words = insight.split()
                current_line = f"│ {i}. "
                for word in words:
                    if len(current_line) + len(word) + 1 <= 68:
                        current_line += word + " "
                    else:
                        lines.append(current_line.ljust(69) + "│")
                        current_line = "│    " + word + " "
                if current_line.strip() != "│":
                    lines.append(current_line.ljust(69) + "│")
            else:
                lines.append(f"│ {i}. {insight}".ljust(69) + "│")
        
        lines.append("└" + "─" * 68 + "┘")
        
        return "\n".join(lines)
    
    def _format_response_box(self, response: str) -> str:
        """Format main response in a box"""
        lines = []
        lines.append("┌" + "─" * 68 + "┐")
        lines.append("│ 📝 ANALYSIS DETAILS".ljust(69) + "│")
        lines.append("├" + "─" * 68 + "┤")
        
        # Split response into lines and wrap
        for line in response.split('\n'):
            if len(line) > 64:
                words = line.split()
                current_line = "│ "
                for word in words:
                    if len(current_line) + len(word) + 1 <= 68:
                        current_line += word + " "
                    else:
                        lines.append(current_line.ljust(69) + "│")
                        current_line = "│ " + word + " "
                if current_line.strip() != "│":
                    lines.append(current_line.ljust(69) + "│")
            else:
                lines.append(("│ " + line).ljust(69) + "│")
        
        lines.append("└" + "─" * 68 + "┘")
        
        return "\n".join(lines)
    
    def _format_metadata_section(self, metadata: List[str]) -> str:
        """Format metadata section"""
        lines = []
        lines.append("─" * 70)
        for item in metadata:
            lines.append(item)
        return "\n".join(lines)
    
    def _format_header(self, title: str) -> str:
        """Format header with box"""
        width = max(len(title) + 4, 70)
        top = self.box['tl'] + self.box['h'] * (width - 2) + self.box['tr']
        middle = self.box['v'] + f" {title}".ljust(width - 2) + self.box['v']
        bottom = self.box['bl'] + self.box['h'] * (width - 2) + self.box['br']
        
        return f"{top}\n{middle}\n{bottom}"
    
    def _format_section(self, title: str, content: str) -> str:
        """Format section with title"""
        return f"{'─' * 70}\n{title.upper()}\n{'─' * 70}\n{content}" if content else f"\n💡 {title.upper()}"
    
    def _format_footer(self) -> str:
        """Format footer"""
        return "─" * 70
    
    def format_table(self, data: pd.DataFrame, title: str = "") -> str:
        """Format data as a professional table with box-drawing characters"""
        if data.empty:
            return "No data to display"
        
        output = []
        
        # Format numbers in the dataframe
        formatted_df = data.copy()
        for col in formatted_df.columns:
            if 'salary' in col.lower() or 'pay' in col.lower():
                formatted_df[col] = formatted_df[col].apply(
                    lambda x: f"${x:,.0f}" if pd.notna(x) and x > 0 else "N/A"
                )
            elif 'employees' in col.lower() or 'count' in col.lower() or 'positions' in col.lower():
                formatted_df[col] = formatted_df[col].apply(
                    lambda x: f"{x:,.0f}" if pd.notna(x) else "N/A"
                )
        
        # Calculate column widths
        col_widths = {}
        for col in formatted_df.columns:
            max_width = max(
                len(str(col)),
                formatted_df[col].astype(str).str.len().max()
            )
            col_widths[col] = min(max_width + 2, 40)  # Cap at 40 chars
        
        total_width = sum(col_widths.values()) + len(col_widths) + 1
        
        # Top border
        output.append(self.box['tl'] + self.box['h'] * (total_width - 2) + self.box['tr'])
        
        # Title row (if provided)
        if title:
            output.append(self.box['v'] + f" {title}".ljust(total_width - 2) + self.box['v'])
            output.append(self.box['left'] + self.box['h'] * (total_width - 2) + self.box['right'])
        
        # Header row
        header_parts = []
        for col in formatted_df.columns:
            header_parts.append(str(col).ljust(col_widths[col]))
        output.append(self.box['v'] + self.box['v'].join(header_parts) + self.box['v'])
        
        # Separator after header
        sep_parts = []
        for col in formatted_df.columns:
            sep_parts.append(self.box['h'] * col_widths[col])
        output.append(self.box['left'] + self.box['cross'].join(sep_parts) + self.box['right'])
        
        # Data rows
        for _, row in formatted_df.iterrows():
            row_parts = []
            for col in formatted_df.columns:
                value = str(row[col])
                # Truncate if too long
                if len(value) > col_widths[col] - 2:
                    value = value[:col_widths[col] - 5] + "..."
                row_parts.append(value.ljust(col_widths[col]))
            output.append(self.box['v'] + self.box['v'].join(row_parts) + self.box['v'])
        
        # Bottom border
        output.append(self.box['bl'] + self.box['h'] * (total_width - 2) + self.box['br'])
        
        return "\n".join(output)
    
    def format_number(self, value: float, format_type: str = 'currency', 
                     precision: int = None) -> str:
        """
        Format numbers consistently across all displays.
        
        Args:
            value: The number to format
            format_type: Type of formatting (currency, percentage, count, decimal)
            precision: Optional decimal precision override
        
        Returns:
            Formatted string
        """
        if pd.isna(value):
            return "N/A"
        
        if format_type == 'currency':
            # Currency: always with $ and thousands separators, no decimals by default
            decimal_places = precision if precision is not None else 0
            return f"${value:,.{decimal_places}f}"
        
        elif format_type == 'percentage':
            # Percentage: 1 decimal place by default
            decimal_places = precision if precision is not None else 1
            return f"{value:.{decimal_places}f}%"
        
        elif format_type == 'count':
            # Count: always integer with thousands separators
            return f"{int(value):,}"
        
        elif format_type == 'decimal':
            # Decimal: 2 decimal places by default
            decimal_places = precision if precision is not None else 2
            return f"{value:,.{decimal_places}f}"
        
        elif format_type == 'compact':
            # Compact: K, M, B notation
            if abs(value) >= 1_000_000_000:
                return f"${value/1_000_000_000:.1f}B"
            elif abs(value) >= 1_000_000:
                return f"${value/1_000_000:.1f}M"
            elif abs(value) >= 1_000:
                return f"${value/1_000:.1f}K"
            else:
                return f"${value:.0f}"
        
        else:
            # Default: 2 decimal places with thousands separators
            return f"{value:,.2f}"
    
    def format_currency_range(self, min_val: float, max_val: float) -> str:
        """Format a currency range consistently"""
        return f"{self.format_number(min_val, 'currency')} - {self.format_number(max_val, 'currency')}"
    
    def format_change(self, old_val: float, new_val: float, show_percentage: bool = True) -> str:
        """Format a change between two values"""
        diff = new_val - old_val
        pct_change = (diff / old_val * 100) if old_val != 0 else 0
        
        sign = "+" if diff > 0 else ""
        
        if show_percentage:
            return f"{sign}{self.format_number(diff, 'currency')} ({sign}{pct_change:.1f}%)"
        else:
            return f"{sign}{self.format_number(diff, 'currency')}"


if __name__ == "__main__":
    # Test the formatter
    formatter = ResultFormatter()
    
    test_results = {
        'summary': 'Average salary: $219,000 | 8,133 employees | 26 positions',
        'insights': [
            'Salary range spans $105K to $271K, a 158% difference',
            'Largest concentration at Manager (M3) with 8,133 employees',
        ],
        'chart_path': 'charts/engineering_analysis.png',
        'tool_used': 'engineering_analysis'
    }
    
    output = formatter.format_response(
        "What's the salary for engineering managers?",
        test_results,
        "Engineering managers earn an average of $219,000..."
    )
    
    print(output)
