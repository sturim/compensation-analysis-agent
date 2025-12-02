# Visualization Enhancement Implementation Guide
## For Enhanced Agno Agent Workspace

**Document Purpose:** Practical guide to implement the 3-panel comprehensive salary visualization system described in VISUALIZATION_DESIGN_AND_IMPLEMENTATION.md

**Current Status:** Basic visualization exists, needs enhancement to match reference quality (`engineering_salary_overview.png`)

---

## Current State Analysis

### What We Have ✅

**File:** `enhanced_agno/visualization_engine.py`
- Basic chart types: comparison, distribution, progression, bar
- Professional styling with seaborn
- 300 DPI output
- Automatic chart type selection

**File:** `enhanced_agno_agent.py`
- Natural language query processing
- Entity extraction (job functions, intent)
- Database querying with percentile support
- Integration with visualization engine

### What We Need ✨

**Missing:** 3-panel comprehensive overview matching `engineering_salary_overview.png`
- Top panel: Salary distribution with percentile bands (P10-P90, P25-P75)
- Bottom left: Career progression with gradient colors
- Bottom right: Employee distribution by level

---

## Implementation Plan

### Phase 1: Create SalaryVizGenerator Module

**File to Create:** `enhanced_agno/salary_viz_generator.py`

**Purpose:** Generate comprehensive 3-panel salary visualizations

**Key Features:**
```python
class SalaryVizGenerator:
    def __init__(self, db_path: str, output_dir: str)
    def generate_salary_overview(self, job_function: str) -> Optional[str]
    def generate_comparison_chart(self, func1: str, func2: str) -> Optional[str]
```

**Implementation Steps:**

1. **Create the file structure:**
```bash
touch enhanced_agno/salary_viz_generator.py
```

2. **Implement data fetching with percentiles:**
```python
def _fetch_salary_data(self, job_function: str) -> pd.DataFrame:
    """Fetch salary data with all percentiles"""
    query = """
    SELECT 
        jp.job_level,
        COUNT(DISTINCT jp.id) as positions,
        SUM(cm.base_salary_lfy_emp_count) as employees,
        ROUND(AVG(cm.base_salary_lfy_p10), 0) as p10,
        ROUND(AVG(cm.base_salary_lfy_p25), 0) as p25,
        ROUND(AVG(cm.base_salary_lfy_p50), 0) as p50,
        ROUND(AVG(cm.base_salary_lfy_p75), 0) as p75,
        ROUND(AVG(cm.base_salary_lfy_p90), 0) as p90
    FROM job_positions jp
    JOIN compensation_metrics cm ON jp.id = cm.job_position_id
    WHERE jp.job_function LIKE ?
      AND cm.base_salary_lfy_p50 IS NOT NULL
      AND jp.job_level IN (
          'Entry (P1)', 'Developing (P2)', 'Career (P3)', 'Advanced (P4)',
          'Manager (M3)', 'Expert (P5)', 'Sr Manager (M4)', 'Director (M5)',
          'Principal (P6)', 'Senior Director (M6)'
      )
    GROUP BY jp.job_level
    ORDER BY p50
    """
    # Execute and return DataFrame
```

3. **Implement 3-panel layout:**
```python
def generate_salary_overview(self, job_function: str) -> Optional[str]:
    """Generate comprehensive 3-panel overview"""
    
    # Fetch data
    df = self._fetch_salary_data(job_function)
    
    # Create figure with GridSpec
    fig = plt.figure(figsize=(18, 12))
    gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
    
    # Panel 1: Distribution (top, full width)
    ax1 = fig.add_subplot(gs[0, :])
    self._create_distribution_panel(ax1, df, job_function)
    
    # Panel 2: Progression (bottom left)
    ax2 = fig.add_subplot(gs[1, 0])
    self._create_progression_panel(ax2, df)
    
    # Panel 3: Employee Distribution (bottom right)
    ax3 = fig.add_subplot(gs[1, 1])
    self._create_employee_panel(ax3, df)
    
    # Save
    filename = f"{job_function.lower().replace(' ', '_')}_salary_overview.png"
    filepath = self.output_dir / filename
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close()
    
    return str(filepath)
```

4. **Implement individual panels:**
```python
def _create_distribution_panel(self, ax, df, job_function):
    """Top panel: Salary distribution with percentile bands"""
    x_pos = range(len(df))
    
    # Plot percentile bands
    ax.fill_between(x_pos, df['p25'], df['p75'], 
                    alpha=0.3, color='#2E86AB', label='25th-75th Percentile')
    
    # Plot P10 and P90 lines
    ax.plot(x_pos, df['p10'], '--', linewidth=1.5, 
           color='#A23B72', label='10th Percentile', alpha=0.7)
    ax.plot(x_pos, df['p90'], '--', linewidth=1.5, 
           color='#F18F01', label='90th Percentile', alpha=0.7)
    
    # Plot median line
    ax.plot(x_pos, df['p50'], 'o-', linewidth=2, markersize=10,
           color='#2E86AB', label='Median (P50)', zorder=3)
    
    # Add labels with salary and employee count
    for i, row in df.iterrows():
        ax.text(i, row['p50'] + 5000, 
               f"${row['p50']:,.0f}\n({row['employees']:,} emp)",
               ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # Styling
    ax.set_xticks(x_pos)
    ax.set_xticklabels(df['job_level'], rotation=45, ha='right')
    ax.set_ylabel('Base Salary ($)')
    ax.set_title(f'{job_function} Base Salary Distribution by Level',
                fontsize=16, fontweight='bold')
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))

def _create_progression_panel(self, ax, df):
    """Bottom left: Career progression with gradient"""
    x_pos = range(len(df))
    bars = ax.bar(x_pos, df['p50'], alpha=0.7)
    
    # Apply gradient colors
    colors = plt.cm.viridis(df['p50'] / df['p50'].max())
    for bar, color in zip(bars, colors):
        bar.set_color(color)
    
    # Add value labels
    for i, val in enumerate(df['p50']):
        ax.text(i, val, f'${val:,.0f}',
               ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # Styling
    ax.set_xticks(x_pos)
    ax.set_xticklabels(df['job_level'], rotation=45, ha='right')
    ax.set_ylabel('Median Base Salary ($)')
    ax.set_title('Career Progression - Median Salary by Level',
                fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))

def _create_employee_panel(self, ax, df):
    """Bottom right: Employee distribution"""
    y_pos = range(len(df))
    
    # Horizontal bars
    ax.barh(y_pos, df['employees'], color='#F18F01', alpha=0.7)
    
    # Add value labels
    for i, val in enumerate(df['employees']):
        ax.text(val, i, f' {val:,}',
               ha='left', va='center', fontsize=9, fontweight='bold')
    
    # Styling
    ax.set_yticks(y_pos)
    ax.set_yticklabels(df['job_level'])
    ax.set_xlabel('Number of Employees')
    ax.set_title('Employee Distribution by Level',
                fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='x')
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x):,}'))
```

### Phase 2: Integrate with VisualizationEngine

**File to Modify:** `enhanced_agno/visualization_engine.py`

**Changes Needed:**

1. **Add import and initialization:**
```python
# At top of file
try:
    from enhanced_agno.salary_viz_generator import SalaryVizGenerator
    SALARY_VIZ_AVAILABLE = True
except ImportError:
    SALARY_VIZ_AVAILABLE = False

class VisualizationEngine:
    def __init__(self, output_dir: str = "charts", db_path: str = "compensation_data.db"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.db_path = db_path
        
        # Initialize comprehensive viz if available
        if SALARY_VIZ_AVAILABLE:
            self.salary_viz = SalaryVizGenerator(db_path, str(self.output_dir))
        else:
            self.salary_viz = None
        
        # Existing styling code...
```

2. **Add routing methods:**
```python
def create_salary_overview(self, job_function: str) -> Optional[str]:
    """Create comprehensive 3-panel salary overview"""
    if self.salary_viz:
        return self.salary_viz.generate_salary_overview(job_function)
    else:
        print("⚠️  Comprehensive visualization not available, using basic chart")
        return None

def create_comparison_chart(self, function1: str, function2: str) -> Optional[str]:
    """Create comparison chart between two functions"""
    if self.salary_viz:
        return self.salary_viz.generate_comparison_chart(function1, function2)
    else:
        print("⚠️  Comparison visualization not available")
        return None
```

### Phase 3: Update Enhanced Agno Agent

**File to Modify:** `enhanced_agno_agent.py`

**Changes Needed:**

1. **Update VisualizationEngine initialization:**
```python
# In __init__ method
self.viz_engine = VisualizationEngine(db_path=self.db_path)
```

2. **Enhance _create_visualization method:**
```python
def _create_visualization(self, results: Dict[str, Any], 
                         entities: Dict[str, Any], params: Dict[str, Any]) -> Optional[str]:
    """Create visualization from results"""
    query_results = results.get('query_results', {})
    
    if query_results.get('status') != 'success':
        return None
    
    functions = entities.get('functions', [])
    intent = entities.get('intent', 'query')
    
    # Route to comprehensive overview for single function
    if len(functions) == 1 and intent in ['query', 'visualize', 'progression']:
        job_function = functions[0]
        chart_path = self.viz_engine.create_salary_overview(job_function)
        if chart_path:
            return chart_path
    
    # Route to comparison for multiple functions
    elif len(functions) >= 2 and intent == 'compare':
        chart_path = self.viz_engine.create_comparison_chart(functions[0], functions[1])
        if chart_path:
            return chart_path
    
    # Fallback to basic visualization
    data = query_results.get('data', [])
    if not data:
        return None
    
    df = pd.DataFrame(data)
    chart_type = params.get('type', 'distribution')
    title = f"{' vs '.join(functions)} Compensation"
    
    return self.viz_engine.auto_visualize(df, chart_type, title)
```

---

## Testing Strategy

### Test 1: Single Function Overview

```python
# test_comprehensive_viz.py
from enhanced_agno_agent import EnhancedAgnoAgent

agent = EnhancedAgnoAgent()

# Test Engineering overview
response = agent.ask("show me Engineering salaries with visualization")
# Expected: charts/engineering_salary_overview.png

# Test Finance overview
response = agent.ask("visualize Finance salaries")
# Expected: charts/finance_salary_overview.png
```

### Test 2: Comparison Chart

```python
# Test comparison
response = agent.ask("compare Engineering vs Finance salaries")
# Expected: charts/comparison_engineering_finance.png
```

### Test 3: Fallback Behavior

```python
# Test with missing data
response = agent.ask("show me NonExistent function salaries")
# Expected: Graceful error message, no crash
```

---

## Implementation Checklist

### Phase 1: Core Module
- [ ] Create `enhanced_agno/salary_viz_generator.py`
- [ ] Implement `SalaryVizGenerator` class
- [ ] Implement `_fetch_salary_data()` method
- [ ] Implement `generate_salary_overview()` method
- [ ] Implement `_create_distribution_panel()` method
- [ ] Implement `_create_progression_panel()` method
- [ ] Implement `_create_employee_panel()` method
- [ ] Test standalone generation

### Phase 2: Integration
- [ ] Update `enhanced_agno/visualization_engine.py`
- [ ] Add import with try/except
- [ ] Update `__init__` to accept db_path
- [ ] Add `create_salary_overview()` method
- [ ] Add `create_comparison_chart()` method
- [ ] Test routing logic

### Phase 3: Agent Enhancement
- [ ] Update `enhanced_agno_agent.py`
- [ ] Pass db_path to VisualizationEngine
- [ ] Update `_create_visualization()` method
- [ ] Add routing logic for single/multiple functions
- [ ] Test end-to-end with natural language queries

### Phase 4: Validation
- [ ] Generate Engineering overview
- [ ] Compare with reference (`engineering_salary_overview.png`)
- [ ] Verify 3-panel layout
- [ ] Verify percentile bands
- [ ] Verify gradient colors
- [ ] Verify employee counts
- [ ] Test multiple job functions
- [ ] Test comparison charts
- [ ] Test error handling

---

## Quick Start Commands

```bash
# 1. Create the new module
touch enhanced_agno/salary_viz_generator.py

# 2. Copy implementation from VISUALIZATION_DESIGN_AND_IMPLEMENTATION.md
# (See Appendix 10.1 for complete code)

# 3. Test standalone
python3 -c "
from enhanced_agno.salary_viz_generator import SalaryVizGenerator
viz = SalaryVizGenerator()
viz.generate_salary_overview('Engineering')
"

# 4. Test through agent
python3 -c "
from enhanced_agno_agent import EnhancedAgnoAgent
agent = EnhancedAgnoAgent()
agent.ask('show me Engineering salaries with visualization')
"

# 5. Compare output
open charts/engineering_salary_overview.png
# Compare with reference chart
```

---

## Expected Outcomes

### Before Implementation
- Basic single-panel charts
- Limited percentile visualization
- No comprehensive overviews

### After Implementation
- ✅ 3-panel comprehensive salary overviews
- ✅ Percentile bands (P10-P90, P25-P75)
- ✅ Career progression with gradient colors
- ✅ Employee distribution visualization
- ✅ Natural language interface
- ✅ Comparison charts
- ✅ Publication-quality output (300 DPI)

---

## Troubleshooting

### Issue: Import Error for SalaryVizGenerator
**Solution:** Ensure file is in correct location: `enhanced_agno/salary_viz_generator.py`

### Issue: No percentile data in database
**Solution:** Verify columns exist: `base_salary_lfy_p10`, `p25`, `p50`, `p75`, `p90`

### Issue: Charts look different from reference
**Solution:** Check:
- Figure size: (18, 12)
- DPI: 300
- Color scheme matches
- GridSpec layout correct

### Issue: SQL parameter binding error
**Solution:** Use LIKE with wildcards: `WHERE jp.job_function LIKE ?` with param `f'%{function}%'`

---

## Next Steps After Implementation

1. **Generate all function overviews:**
```python
functions = ['Engineering', 'Finance', 'Sales', 'Marketing', 'HR']
for func in functions:
    agent.ask(f"visualize {func} salaries")
```

2. **Create comparison matrix:**
```python
comparisons = [
    ('Engineering', 'Finance'),
    ('Sales', 'Marketing'),
    ('HR', 'Operations')
]
for func1, func2 in comparisons:
    agent.ask(f"compare {func1} vs {func2}")
```

3. **Document new capabilities:**
- Update README with visualization examples
- Add screenshots to documentation
- Create user guide for visualization requests

---

## Reference Files

**Source Document:** `VISUALIZATION_DESIGN_AND_IMPLEMENTATION.md`
- Section 3.1: SalaryVizGenerator details
- Section 10.1: Complete code example
- Section 6: Usage guide

**Reference Chart:** `charts/engineering_salary_overview.png`
- Target quality and layout
- Color scheme reference
- Label positioning

**Current Implementation:**
- `enhanced_agno/visualization_engine.py` - Basic charts
- `enhanced_agno_agent.py` - Agent integration
- `compensation_data.db` - Data source

---

**Document Version:** 1.0  
**Created:** December 2, 2024  
**Purpose:** Practical implementation guide for workspace  
**Status:** Ready for implementation
