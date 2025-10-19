# GAMMA Feedback Loop - Quick Start Guide

## What is this?

An automated system that:
1. ✅ Runs gamma.py end-to-end in different modes
2. ✅ Runs all tests
3. 📊 Analyzes failures and errors
4. 🤖 Works with Claude Code to fix issues
5. 🔄 Iterates until everything passes

## 60-Second Start

### Option 1: Interactive with Claude Code (Recommended)

This works directly within Claude Code CLI to intelligently fix issues:

```bash
# Run the interactive loop
python3 tools/feedback_loop_interactive.py --live
```

**What happens:**
1. Runs `python3 gamma.py game --help`, `comparison --help`, etc.
2. Runs `./run_tests.sh`
3. Shows you a detailed failure report
4. Pauses and asks Claude Code (me!) to analyze and fix
5. You type 'continue' and it repeats
6. Stops when all tests pass or max iterations reached

### Option 2: Automated (No interaction)

Tries to auto-fix common issues:

```bash
# Auto-fix mode
python3 tools/feedback_loop.py --live --auto-fix --verbose
```

## Common Use Cases

### 1. "I just changed something, test it end-to-end"

```bash
python3 tools/feedback_loop_interactive.py --live --max-iterations 3
```

### 2. "Run quick sanity check"

```bash
python3 tools/feedback_loop.py --live --live-modes "game --help" "game --version"
```

### 3. "Fix test failures automatically"

```bash
python3 tools/feedback_loop.py --auto-fix --max-iterations 5
```

### 4. "Only test one module"

```bash
python3 tools/feedback_loop.py --test-filter "test_mind_meld" --verbose
```

### 5. "Debug why gamma.py crashes"

```bash
python3 tools/feedback_loop_interactive.py \
  --no-tests \
  --live-modes "game" "chat" "tutorial"
```

## Understanding Output

### Success Looks Like:

```
================================================================================
ITERATION 2/5
================================================================================

📡 Running live end-to-end executions...
  ✓ PASSED: game --help (0.45s)
  ✓ PASSED: comparison --help (0.52s)

🧪 Running tests...
  ✓ ALL TESTS PASSED (45.23s)

================================================================================
✅ SUCCESS! All tests and executions passed!
================================================================================
```

### Failure Looks Like:

```
================================================================================
ITERATION 1/5
================================================================================

📡 Running live end-to-end executions...
  ✗ FAILED: game --help (exit code: 1)
    Found 1 error(s)

🧪 Running tests...
  ✗ TESTS FAILED (exit code: 1)
    Found 3 failure(s)

================================================================================
FAILURE ANALYSIS
================================================================================

# GAMMA Feedback Loop - Failure Report

## Live Execution: gamma.py game --help
Status: ✗ FAILED

### Failures (1):
1. **import_error**
   - Type: Import Error
   - Severity: critical
   - Message: No module named 'transformers'
   - Location: src/game/cli.py:15

[... detailed analysis ...]

================================================================================
⏸️  PAUSING FOR FIXES
================================================================================

Claude Code, please:
1. Review the failure report above
2. Analyze the errors and their root causes
3. Apply fixes using Edit/Write tools
4. When done, type 'continue' to proceed to next iteration
```

## Files Created

```
output/
├── feedback_reports/
│   └── feedback_report_20251019_103015.md   # Detailed failure analysis
└── feedback_loop_20251019_103015.json       # Execution summary
```

## How It Works with Claude Code

### The Interactive Loop:

1. **Run** the interactive script in Claude Code CLI
2. **Wait** for failure report
3. **Claude Code analyzes** the errors (that's me!)
4. **Claude Code fixes** using Edit/Write tools
5. **You type** 'continue'
6. **Loop repeats** until success

### Example Session:

```
You: Run the feedback loop
Claude: [Runs python3 tools/feedback_loop_interactive.py --live]
System: [Shows failure report]
Claude: I see an ImportError for 'transformers'. Let me check requirements.txt...
Claude: [Uses Read tool on requirements.txt]
Claude: [Uses Edit tool to add 'transformers>=4.30.0']
Claude: The fix is applied. Shall I continue to the next iteration?
You: yes
Claude: [Types 'continue' in the interactive loop]
System: [Runs tests again...]
System: ✅ SUCCESS! All tests passed!
```

## Modes Reference

### Live Modes (--live)

These run `gamma.py` end-to-end to catch runtime errors:

| Mode | Command | What it tests |
|------|---------|---------------|
| `game --help` | Show help text | CLI parsing, imports |
| `game --version` | Show version | Version string |
| `comparison --help` | Comparison mode help | Comparison module |
| `mind-meld --help` | Mind meld help | Mind meld module |
| `game` | Interactive game | Full game mode (with auto-exit) |
| `game --chat` | Chat mode | Chat interface (with auto-exit) |

### Test Modes

```bash
# All tests (default)
--test-command "./run_tests.sh"

# Specific test file
--test-command "python3 -m pytest tests/test_engine.py -v"

# Test pattern
--test-filter "engine"
```

## Tips

### 🎯 Start Small

```bash
# Test just help commands first
python3 tools/feedback_loop.py --live --live-modes "game --help"
```

### 🔍 Use Verbose

Always use `--verbose` to see what's happening:

```bash
python3 tools/feedback_loop.py --live --verbose
```

### 📝 Save Logs

For complex issues:

```bash
python3 tools/feedback_loop.py --live --verbose --log-file debug.log
```

### ⏱️ Adjust Timeouts

If gamma.py takes a while to start:

```bash
python3 tools/feedback_loop.py --live --live-timeout 60
```

### 🎛️ Iterate Carefully

Don't set too many iterations:

```bash
# Good: Quick feedback
--max-iterations 3

# Bad: Wastes time if stuck
--max-iterations 20
```

## Troubleshooting

### "Command not found: python"

Use `python3`:

```bash
# Update gamma.py shebang to use python3
sed -i '' '1s/python/python3/' gamma.py
```

### "Tests hang forever"

Lower the timeout:

```bash
python3 tools/feedback_loop.py --live --live-timeout 10
```

### "No failures detected but tests fail"

The log parser might not recognize the format. Check:

```bash
./run_tests.sh 2>&1 | python3 tools/log_analyzer.py
```

### "Too many errors, overwhelming"

Filter to one module:

```bash
python3 tools/feedback_loop.py --test-filter "core" --max-iterations 2
```

## Next Steps

1. **Read the full docs:** `tools/README_FEEDBACK_LOOP.md`
2. **Try it:** `python3 tools/feedback_loop_interactive.py --live`
3. **Let Claude Code fix issues** using the interactive mode
4. **Iterate** until all tests pass

## Advanced: Custom Workflow

You can create custom test scenarios:

```bash
# Create a custom script
cat > my_feedback_test.sh << 'EOF'
#!/bin/bash
python3 tools/feedback_loop_interactive.py \
  --live \
  --live-modes \
    "game --help" \
    "game --version" \
    "comparison --help" \
    "mind-meld --help" \
  --test-command "./run_tests.sh" \
  --max-iterations 5
EOF

chmod +x my_feedback_test.sh
./my_feedback_test.sh
```

## Philosophy

The feedback loop is designed to:

- ✅ **Catch runtime errors** that tests might miss
- ✅ **Automate repetitive** fix-test-fix cycles
- ✅ **Leverage Claude Code** for intelligent problem solving
- ✅ **Provide clear context** for debugging
- ✅ **Iterate rapidly** until everything works

It's not magic - it's a systematic approach to testing and fixing that works with you (Claude Code) to ensure GAMMA runs correctly end-to-end.

---

**Questions?** Check the full documentation in `tools/README_FEEDBACK_LOOP.md`

**Found a bug?** The feedback loop can help fix itself! Run:
```bash
python3 tools/feedback_loop_interactive.py --test-filter "feedback" --live
```
