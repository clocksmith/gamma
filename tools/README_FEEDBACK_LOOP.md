# GAMMA Feedback Loop System

Automated testing, error analysis, and fixing system for GAMMA.

## Overview

The feedback loop system provides three complementary tools for testing and fixing GAMMA:

1. **feedback_loop.py** - Automated loop with basic pattern-based fixes
2. **feedback_loop_interactive.py** - Interactive loop designed for Claude Code
3. **log_analyzer.py** - Standalone log analysis utility
4. **auto_fixer.py** - Standalone fix suggestion utility

## Quick Start

### Option 1: Interactive with Claude Code (Recommended)

The interactive loop leverages Claude Code's intelligence to analyze and fix issues:

```bash
# Run in a Claude Code session
python tools/feedback_loop_interactive.py --live
```

This will:
1. Run tests and live gamma.py executions
2. Generate detailed failure reports
3. Pause for you (Claude Code) to analyze and fix
4. Continue iterating until success

### Option 2: Automated Mode

The automated loop attempts to fix common issues automatically:

```bash
# Run tests only
python tools/feedback_loop.py --verbose

# Run tests + live executions with auto-fix
python tools/feedback_loop.py --live --auto-fix --max-iterations 5

# Run with specific test filter
python tools/feedback_loop.py --test-filter "test_engine"
```

## Detailed Usage

### feedback_loop_interactive.py

**Best for:** Working with Claude Code to intelligently diagnose and fix issues

```bash
# Full workflow: tests + live executions
python tools/feedback_loop_interactive.py --live --max-iterations 10

# Tests only
python tools/feedback_loop_interactive.py --no-live

# Custom live modes
python tools/feedback_loop_interactive.py --live-modes "game --help" "game --version" "comparison --help"
```

**Workflow:**
1. Loop runs tests/live executions
2. Generates markdown failure report
3. Saves report to `output/feedback_reports/`
4. Pauses with message to Claude Code
5. Claude Code analyzes and applies fixes
6. Type 'continue' to proceed to next iteration
7. Repeat until success or max iterations

**Output:**
- Console: Real-time execution status
- Files: `output/feedback_reports/feedback_report_TIMESTAMP.md`

### feedback_loop.py

**Best for:** Automated fixing of common issues without human intervention

```bash
# Basic usage
python tools/feedback_loop.py [options]

# Options:
--max-iterations N       # Max fix iterations (default: 5)
--test-command CMD      # Custom test command (default: ./run_tests.sh)
--auto-fix              # Auto-apply fixes without prompting
--verbose               # Show detailed output
--log-file FILE         # Save logs to file
--test-filter PATTERN   # Only run tests matching pattern
--live                  # Run live gamma.py executions
--live-modes MODE...    # Custom live modes
--live-timeout N        # Timeout per live execution (default: 30s)
```

**Examples:**

```bash
# Run with all features
python tools/feedback_loop.py \
  --live \
  --auto-fix \
  --verbose \
  --max-iterations 3 \
  --log-file feedback.log

# Quick test of specific module
python tools/feedback_loop.py \
  --test-filter "test_mind_meld" \
  --max-iterations 2

# Live execution testing only
python tools/feedback_loop.py \
  --live \
  --live-modes "game --help" "comparison --help" "mind-meld --help"
```

**Output:**
- Console: Real-time progress
- Files: `output/feedback_loop_TIMESTAMP.json` (summary)
- Optional: Custom log file (--log-file)

### log_analyzer.py

**Best for:** Analyzing test output from any source

```bash
# Analyze a log file
python tools/log_analyzer.py path/to/test_output.log

# Or pipe test output
./run_tests.sh 2>&1 | python tools/log_analyzer.py

# Use as a module
python3 -c "
from log_analyzer import LogAnalyzer
analyzer = LogAnalyzer()
failures = analyzer.parse_test_output(test_output)
for f in failures:
    print(f'{f.test_name}: {f.error_type}')
"
```

**Features:**
- Parses pytest, unittest, and shell script output
- Extracts error type, message, file location
- Categorizes by severity (critical, high, medium, low)
- Deduplicates failures
- Provides structured failure data

### auto_fixer.py

**Best for:** Getting fix suggestions for known error patterns

```bash
# Demo mode
python tools/auto_fixer.py

# Use as a module
python3 -c "
from auto_fixer import AutoFixer
from log_analyzer import TestFailure

fixer = AutoFixer()
failure = TestFailure(
    test_name='test_example',
    error_type='Import Error',
    error_message=\"No module named 'numpy'\",
    file_path='tests/test_example.py'
)

suggestions = fixer.suggest_fixes(failure)
for s in suggestions:
    print(f'{s[\"description\"]} (confidence: {s[\"confidence\"]})')
"
```

**Supported Fix Types:**
- Import errors (missing modules, wrong paths)
- Attribute errors (missing class attributes)
- Name errors (undefined variables)
- Type errors
- Syntax errors
- Assertion errors

## Live Execution Modes

The `--live` flag enables end-to-end testing of gamma.py in real scenarios:

### Default Modes

```bash
# These run by default with --live
python gamma.py game --help
python gamma.py comparison --help
python gamma.py mind-meld --help
```

### Custom Modes

```bash
# Define your own test scenarios
python tools/feedback_loop.py --live \
  --live-modes \
    "game --help" \
    "game --version" \
    "comparison --help" \
    "mind-meld --help"
```

### Interactive Modes

For modes that expect user input, the loop automatically provides exit commands:

```bash
# These would hang without auto-input
python gamma.py game --chat         # Auto-sends: /quit, exit
python gamma.py game --tutorial     # Auto-sends: q, exit
```

## Understanding the Output

### Success
```
================================================================================
✅ SUCCESS! All tests and executions passed!
================================================================================
Iteration: 3
Total tests run: 127+
All live modes: ✓
```

### Failure Report Structure

```markdown
# GAMMA Feedback Loop - Failure Report

Iteration: 2
Timestamp: 2025-10-19T10:30:15

================================================================================

## Live Execution: gamma.py game --help
Status: ✗ FAILED
Duration: 2.34s

### Failures (1):
1. **test_import**
   - Type: Import Error
   - Severity: critical
   - Message: No module named 'transformers'
   - Location: src/game/cli.py:15

## Summary
Total failures: 3
By severity:
  - CRITICAL: 1
  - HIGH: 1
  - MEDIUM: 1
```

## Integration with Development Workflow

### Pre-commit Testing

```bash
# Add to .git/hooks/pre-commit
python tools/feedback_loop.py --test-filter "critical" --max-iterations 1
```

### CI/CD Integration

```bash
# In GitHub Actions, GitLab CI, etc.
- name: Run Feedback Loop
  run: |
    python tools/feedback_loop.py \
      --live \
      --auto-fix \
      --max-iterations 3 \
      --log-file ci-feedback.log
```

### Development Iteration

```bash
# While developing a feature
while true; do
  python tools/feedback_loop.py \
    --test-filter "your_feature" \
    --max-iterations 2 \
    --verbose

  read -p "Continue? (y/n): " continue
  [ "$continue" != "y" ] && break
done
```

## How It Works

### 1. Execution Phase
- Runs test command (default: `./run_tests.sh`)
- Optionally runs live `gamma.py` executions
- Captures stdout, stderr, exit codes
- Measures execution time

### 2. Analysis Phase
- Parses output using multiple strategies:
  - pytest format detection
  - unittest format detection
  - Shell script format detection
  - Python traceback parsing
- Extracts structured failure data
- Categorizes by type and severity
- Deduplicates failures

### 3. Fix Phase

**Automated (feedback_loop.py):**
- Pattern-matches error types
- Suggests fixes with confidence levels
- Can auto-apply safe fixes (e.g., add to requirements.txt)
- Prompts for risky fixes

**Interactive (feedback_loop_interactive.py):**
- Generates detailed markdown report
- Presents to Claude Code
- Waits for intelligent analysis and fixes
- Continues after manual confirmation

### 4. Iteration Phase
- Re-runs tests with fixes applied
- Compares new failures to previous
- Tracks fix effectiveness
- Stops when all pass or max iterations reached

## Troubleshooting

### "No failures detected but tests failed"

The parser might not recognize your test format. Check:
```bash
# View raw output
./run_tests.sh 2>&1 | tee test_output.txt

# Try log analyzer directly
python tools/log_analyzer.py test_output.txt
```

### "Timeout in live execution"

Increase timeout:
```bash
python tools/feedback_loop.py --live --live-timeout 60
```

### "Fix not being applied"

Check fix type support:
```bash
# See what fixes are available
python tools/auto_fixer.py

# Some fixes require manual intervention
# Use interactive mode for these:
python tools/feedback_loop_interactive.py --live
```

### "Too many iterations"

Focus on critical issues first:
```bash
# Filter tests
python tools/feedback_loop.py --test-filter "critical"

# Reduce iterations, fix manually
python tools/feedback_loop.py --max-iterations 2 --verbose
```

## Best Practices

1. **Start with Interactive Mode**
   - Let Claude Code understand the codebase
   - Fix critical issues first
   - Build confidence in the system

2. **Use Test Filters**
   - Focus on one module at a time
   - Avoid overwhelming the fixer

3. **Check Logs**
   - Always use `--verbose` when debugging
   - Save logs with `--log-file` for complex issues

4. **Combine with Manual Testing**
   - Automated fixes catch common issues
   - Manual review ensures quality

5. **Iterate Incrementally**
   - Start with small max-iterations
   - Gradually increase as codebase stabilizes

## File Structure

```
tools/
├── feedback_loop.py                 # Automated loop
├── feedback_loop_interactive.py     # Interactive loop for Claude Code
├── log_analyzer.py                  # Log parsing utility
├── auto_fixer.py                    # Fix suggestion utility
└── README_FEEDBACK_LOOP.md         # This file

output/
├── feedback_reports/                # Generated reports
│   └── feedback_report_*.md
└── feedback_loop_*.json            # Execution summaries
```

## Future Enhancements

- [ ] Support for more test frameworks
- [ ] Machine learning-based fix suggestions
- [ ] Integration with git for automatic commits
- [ ] Performance regression detection
- [ ] Coverage-aware iteration
- [ ] Parallel test execution
- [ ] Web UI for viewing results

## Contributing

To add support for a new error type:

1. Add pattern to `log_analyzer.py`:
```python
ERROR_PATTERNS = {
    'your_error': re.compile(r"YourError: (.+)"),
}
```

2. Add fix logic to `auto_fixer.py`:
```python
def _fix_your_error(self, failure: TestFailure) -> List[Dict[str, Any]]:
    # Return fix suggestions
    pass
```

3. Update tests

## License

Same as GAMMA (MIT License)
