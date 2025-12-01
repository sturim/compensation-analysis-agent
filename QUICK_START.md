# Quick Start Guide - Enhanced Agno Agent MVP

## 1. Install Dependencies

```bash
pip install anthropic pandas matplotlib seaborn python-dotenv
```

## 2. Set Up API Key

```bash
echo "ANTHROPIC_API_KEY=your-actual-api-key-here" > .env
```

Or add to your existing `.env` file.

## 3. Run It!

### Interactive Mode (Recommended)
```bash
python3 enhanced_agno_agent.py -i
```

Then try these questions:
```
❓ What's the salary for Finance Managers?
❓ Compare engineering and sales
❓ Compare them to HR
❓ Show me career progression in finance
```

### Single Question Mode
```bash
python3 enhanced_agno_agent.py "What's the salary for Engineering Managers?"
```

### Demo Mode
```bash
python3 demo_enhanced_agent.py
```

## 4. Check the Results

Charts are saved to `charts/` directory:
```bash
ls -la charts/
open charts/*.png  # macOS
```

## What to Expect

### First Question
```
🤖 Processing: What's the salary for Finance Managers?
   [1/4] Extracting entities...
         Functions: ['Finance']
         Intent: query
   [2/4] Creating execution plan...
         Plan: 2 steps (llm)
   [3/4] Executing plan...
         ✅ Chart saved: charts/distribution_finance_compensation.png
   [4/4] Generating response...

Finance Managers earn an average of $147,793...
[Detailed insights and suggestions]
```

### Follow-up Question (Context Awareness)
```
❓ Compare them to sales

🤖 Processing: Compare them to sales
   [1/4] Extracting entities...
         Functions: ['Sales']
         Intent: compare
         Resolved reference: ['Finance']  ← Remembers!
   ...
```

## Troubleshooting

### "anthropic not installed"
```bash
pip install anthropic
```

### "Claude initialization failed"
Check your `.env` file has the correct API key:
```bash
cat .env
# Should show: ANTHROPIC_API_KEY=sk-ant-...
```

### "No such file: compensation_data.db"
Make sure you're running from the project root directory where `compensation_data.db` exists.

### Charts not displaying
Charts are saved to `charts/` directory. Open them manually:
```bash
open charts/distribution_finance_compensation.png
```

## Tips

1. **Ask follow-up questions** - The agent remembers context!
2. **Use natural language** - "Compare them", "show more", etc.
3. **Check charts/** - All visualizations are saved there
4. **Try comparisons** - "Compare X and Y" works great
5. **Ask for progression** - "Show career progression in X"

## Example Session

```bash
$ python3 enhanced_agno_agent.py -i

🤖 ENHANCED AGNO AGENT - Interactive Mode
======================================================================

❓ Your question: What's the salary for engineering managers?
[Response with chart]

❓ Your question: Compare them to sales managers
[Comparison with chart]

❓ Your question: Show me the top engineering specializations
[Analysis with chart]

❓ Your question: exit
👋 Goodbye!
```

## Next Steps

- Read `ENHANCED_AGNO_MVP_README.md` for detailed documentation
- Read `MVP_IMPLEMENTATION_COMPLETE.md` for technical details
- Check `.kiro/specs/enhanced-agno-agent/` for full design docs

## Need Help?

The agent has built-in fallbacks and will work even without Claude (degraded mode). If you encounter issues, check:
1. API key is set correctly
2. Database file exists
3. Dependencies are installed
4. You're in the correct directory

Enjoy! 🚀
