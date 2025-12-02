# LLM-Guided Visualization Enhancement

## Problem Solved

The agent was producing unreadable charts (like `chart__compensation.png`) because it used simple rule-based logic to choose chart types. This often resulted in:
- Overcrowded charts with too much data
- Wrong chart type for the data structure
- Poor visual presentation
- Difficult to read labels and values

## Solution Implemented

Added **LLM-guided intelligent visualization** that uses Claude AI to analyze the data and query, then recommend the optimal chart type for clear, insightful visualization.

---

## What Was Added

### 1. **VisualizationAdvisor** (`enhanced_agno/visualization_advisor.py`)

A new component that uses Claude to make intelligent visualization decisions.

**Key Features:**
- Analyzes data characteristics (row count, columns, percentiles, employee counts)
- Considers user intent from the query
- Evaluates available chart types
- Recommends optimal visualization with reasoning
- Falls back to rule-based logic if LLM unavailable

**Available Chart Types:**
1. **comprehensive_overview** - 3-panel dashboard (best for single function with rich data)
2. **comparison** - Side-by-side comparison (best for 2+ functions)
3. **distribution** - Percentile distribution chart (best for showing salary spread)
4. **progression** - Career progression chart (best for showing growth)
5. **simple_bar** - Clean bar chart (best for simple data)

**LLM Decision Process:**
```
User Query + Data Summary → Claude AI → Recommendation
                                          ├─ Chart Type
                                          ├─ Reasoning
                                          ├─ Layout (single/multi-panel)
                                          ├─ Features to include
                                          └─ Suggested title
```

### 2. **Enhanced VisualizationEngine** (`enhanced_agno/visualization_engine.py`)

Updated to use LLM recommendations:

**Changes:**
- Accepts `claude_client` parameter
- Initializes `VisualizationAdvisor` if Claude available
- `auto_visualize()` now accepts `query` and `entities` parameters
- Calls advisor to get recommendation before creating chart
- Displays LLM reasoning to user
- Added `_create_comprehensive_chart()` method for multi-panel layouts
- Added helper methods for percentile distribution, career progression, and employee distribution panels

**New Methods:**
- `_create_comprehensive_chart()` - Creates 3-panel dashboard
- `_plot_percentile_distribution()` - Top panel with percentile bands
- `_plot_career_progression()` - Bottom-left panel with gradient bars
- `_plot_employee_distribution()` - Bottom-right panel with horizontal bars

### 3. **Updated EnhancedAgnoAgent** (`enhanced_agno_agent.py`)

Modified to pass Claude client to visualization engine:

**Changes:**
- Initializes Claude client earlier in `__init__`
- Passes `claude_client` to `VisualizationEngine`
- `_create_visualization()` passes `query` and `entities` to `auto_visualize()`
- Enables LLM-guided decisions throughout the visualization pipeline

---

## How It Works

### Example Flow:

**User Query:** "show me Engineering salaries"

1. **Entity Extraction:**
   ```python
   entities = {
       'functions': ['Engineering'],
       'intent': 'visualize',
       'original_question': 'show me Engineering salaries'
   }
   ```

2. **Data Query:**
   - Fetches Engineering salary data
   - Includes percentiles (P10, P25, P50, P75, P90)
   - Includes employee counts
   - Returns 32 job levels

3. **LLM Analysis:**
   ```
   Claude receives:
   - Query: "show me Engineering salaries"
   - Data: 32 rows, has percentiles, has employee counts
   - Intent: visualize
   
   Claude recommends:
   - Chart Type: comprehensive_overview
   - Reasoning: "Single function with rich percentile data and employee 
                 counts - comprehensive 3-panel dashboard will provide 
                 complete picture with distribution, progression, and 
                 workforce composition"
   - Layout: multi_panel
   - Features: [percentile_bands, gradient_colors, employee_counts]
   ```

4. **Chart Generation:**
   - Creates 3-panel dashboard
   - Top: Salary distribution with percentile bands
   - Bottom-left: Career progression with gradient colors
   - Bottom-right: Employee distribution
   - Saves as `comprehensive_engineering_compensation.png`

5. **User Sees:**
   ```
   🤖 LLM Recommendation: comprehensive_overview
   💡 Reasoning: Single function with rich percentile data...
   ✅ Chart saved to: charts/comprehensive_engineering_compensation.png
   ```

---

## Benefits

### Before (Rule-Based):
- ❌ Simple if/else logic
- ❌ Often wrong chart type
- ❌ Overcrowded visualizations
- ❌ Poor readability
- ❌ No reasoning provided

### After (LLM-Guided):
- ✅ Intelligent analysis of data
- ✅ Optimal chart type selection
- ✅ Clear, readable visualizations
- ✅ Professional appearance
- ✅ Explains reasoning
- ✅ Adapts to data characteristics
- ✅ Considers user intent

---

## Usage

### Automatic (Recommended):
Just use the agent normally - LLM guidance is automatic!

```python
from enhanced_agno_agent import EnhancedAgnoAgent

agent = EnhancedAgnoAgent()
agent.ask("show me Engineering salaries")  # LLM chooses best chart
agent.ask("compare Sales vs Finance")      # LLM analyzes and recommends
```

### Test Script:
```bash
python3 test_llm_guided_viz.py
```

This will demonstrate the LLM making intelligent decisions for different query types.

---

## Configuration

### Requirements:
- Claude API key in `.env` file: `ANTHROPIC_API_KEY=your_key_here`
- `anthropic` Python package installed

### Fallback:
If Claude is unavailable, the system automatically falls back to improved rule-based logic. No errors, just less intelligent decisions.

---

## Technical Details

### LLM Prompt Structure:

The advisor sends Claude:
1. **User Query** - Original question
2. **Data Summary** - Row count, columns, data characteristics
3. **Available Chart Types** - With descriptions of when each is best
4. **Request** - JSON response with recommendation

### Response Format:
```json
{
  "chart_type": "comprehensive_overview",
  "reasoning": "Single function with rich data...",
  "layout": "multi_panel",
  "features": ["percentile_bands", "gradient_colors"],
  "title": "Engineering Salary Overview",
  "insights": ["Key insight 1", "Key insight 2"]
}
```

### Performance:
- LLM call adds ~1-2 seconds to visualization
- Cached for similar queries (future enhancement)
- Fallback is instant if LLM unavailable

---

## Examples of LLM Decisions

### Query: "show me Engineering salaries"
**LLM Chooses:** `comprehensive_overview`
**Reasoning:** Single function with percentiles and employee data - show complete picture

### Query: "compare Sales and Finance"
**LLM Chooses:** `comparison`
**Reasoning:** Two functions - side-by-side comparison best for highlighting differences

### Query: "what's the career path in Marketing"
**LLM Chooses:** `progression`
**Reasoning:** Career path intent - progression chart shows growth trajectory

### Query: "Finance salaries for Manager level"
**LLM Chooses:** `simple_bar`
**Reasoning:** Small dataset (1 level) - clean bar chart is clearest

---

## Files Modified

1. ✅ `enhanced_agno/visualization_advisor.py` - NEW
2. ✅ `enhanced_agno/visualization_engine.py` - ENHANCED
3. ✅ `enhanced_agno_agent.py` - UPDATED
4. ✅ `test_llm_guided_viz.py` - NEW TEST

---

## Next Steps

### To Use:
1. Ensure Claude API key is configured
2. Run any query - LLM guidance is automatic
3. Observe the reasoning in console output
4. Check generated charts in `charts/` folder

### To Test:
```bash
python3 test_llm_guided_viz.py
```

### To Verify:
Compare old charts (like `chart__compensation.png`) with new LLM-guided charts. You'll see:
- Better chart type selection
- Clearer layouts
- More readable labels
- Professional appearance
- Appropriate use of colors and spacing

---

## Troubleshooting

### "LLM-Guided Visualization: ⚠️ Using rule-based fallback"
**Cause:** Claude client not available
**Solution:** Check API key in `.env` file

### Charts still look basic
**Cause:** Data might not have percentiles or employee counts
**Solution:** Ensure database queries include all percentile columns

### LLM recommendation seems wrong
**Cause:** Prompt might need tuning for specific use case
**Solution:** Modify prompt in `visualization_advisor.py` line 90

---

**Status:** ✅ Fully Implemented and Ready to Use
**Version:** 1.0
**Date:** December 2, 2024
