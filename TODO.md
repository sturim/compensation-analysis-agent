# TODO - Enhanced Agno Agent

## 🔴 High Priority

### Smart Tool Matching - Needs Revisit
**Status:** Currently implemented but needs review

**Current Behavior:**
- Tool matching logic in `enhanced_agno/tool_inventory.py`
- Prevents simple queries from matching comparison tools
- Example: "that of sales" doesn't match `finance_vs_sales_chart`

**Issues to Review:**
- May be too restrictive or not restrictive enough
- Need to validate matching logic across different query types
- Consider edge cases and user intent

**Files Involved:**
- `enhanced_agno/tool_inventory.py` - `match_query_to_tool()` method
- Lines ~145-195

**Test Cases to Consider:**
1. "that of sales" → Should NOT match comparison tools ✓
2. "compare finance and sales" → SHOULD match `finance_vs_sales_chart` ✓
3. "show me sales" → Should NOT match comparison tools (?)
4. "sales analysis" → Should match `sales_analysis` if exists (?)

**Questions:**
- Should we match tools more aggressively or conservatively?
- How to handle ambiguous queries?
- Should we ask user for confirmation before using a tool?

**Next Steps:**
1. Review current matching logic
2. Test with various query patterns
3. Consider adding confidence scores
4. Possibly add user confirmation for tool selection

---

## 🟡 Medium Priority

### Web Interface Development
- Create Flask/FastAPI backend
- Build React/Vue frontend
- Integrate session context with localStorage
- Add export functionality to UI

### Session Persistence
- Store sessions in database (SQLite/PostgreSQL)
- Add session expiration
- Implement session cleanup

---

## 🟢 Low Priority

### Documentation
- API documentation
- Deployment guide
- User manual

### Performance Optimization
- Cache database queries
- Optimize LLM calls
- Add connection pooling

---

## ✅ Completed

- [x] Session context retention
- [x] Entity parser improvements
- [x] Rich visual formatting
- [x] Intelligent insights generation
- [x] Error handling with retry
- [x] Export capabilities
- [x] Proactive suggestions
- [x] Tool inventory and reuse

---

**Last Updated:** December 1, 2024
