# Quick Start Guide

Get up and running with the LLM TypeScript/JavaScript Benchmark Suite in 5 minutes!

## Prerequisites

- Node.js 18+ installed
- API keys for at least one LLM provider (OpenAI or Anthropic)

## Step 1: Set Up API Keys

```bash
# Option A: Export environment variables
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."

# Option B: Create .env file
cat > .env << EOF
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
EOF
```

## Step 2: Install Dependencies (Optional)

If you want to run TypeScript tasks:

```bash
npm install -D tsx
```

## Step 3: Run Your First Benchmark

```bash
# Run a simple task
node benchmark/index.js --task fibonacci --variant typescript

# See available tasks
node benchmark/index.js --list-tasks

# Run all simple tasks
node benchmark/index.js --category simple
```

## Step 4: View Results

After running benchmarks, check the reports:

```bash
# View summary report
cat benchmark/reports/summary.md

# View comparison report
cat benchmark/reports/comparison.md

# Open HTML dashboard
open benchmark/reports/dashboard.html
```

## Example Output

```
=== LLM TypeScript/JavaScript Benchmark Suite ===

Loading tasks...
Loaded 8 tasks across 5 categories

[openai-gpt4] [typescript] Running: fibonacci
✓ Completed in 2341ms - Score: 87.50

[openai-gpt4] [javascript] Running: fibonacci
✓ Completed in 1923ms - Score: 82.30

[openai-gpt4] [javascript-jsdoc] Running: fibonacci
✓ Completed in 2156ms - Score: 85.10

Progress: 3/9 (33.3%)

=== Generating Reports ===
Raw results saved to benchmark/results/results-2025-01-15T10-30-45-123Z.json
Summary report saved to benchmark/reports/summary.md
Comparison report saved to benchmark/reports/comparison.md
Detailed report saved to benchmark/reports/detailed.md
HTML dashboard saved to benchmark/reports/dashboard.html

=== Benchmark Complete ===

--- Summary ---
Total Runs: 9
Successful: 9
Failed: 0
Average Score: 84.27/100
Average Duration: 2140ms

--- By Variant ---
typescript: 86.50/100 (3 tasks)
javascript: 81.20/100 (3 tasks)
javascript-jsdoc: 85.10/100 (3 tasks)

--- By Provider ---
openai-gpt4: 84.27/100 (9 tasks)
```

## Common Use Cases

### Compare TypeScript vs JavaScript

```bash
node benchmark/index.js --category simple
```

This will run all simple tasks across all three variants and show you how LLMs perform with and without type information.

### Test a Specific Provider

```bash
node benchmark/index.js --provider anthropic-claude
```

### Quick Smoke Test

```bash
node benchmark/index.js --task fibonacci --variant typescript
```

### Full Benchmark Run

```bash
node benchmark/index.js
```

⚠️ **Warning**: This will run all tasks with all providers and variants. It may take a while and cost money!

## Understanding Results

The benchmark scores each response on:

- **Accuracy**: Does the code work correctly?
- **Performance**: How efficient is the solution?
- **Code Quality**: Is it well-written and maintainable?
- **Completeness**: Does it handle all requirements?

A score of 100 means perfect performance across all criteria.

## Next Steps

1. **Explore Tasks**: Look in `benchmark/tasks/` to see all available benchmarks
2. **Customize Config**: Edit `benchmark/config.js` to adjust settings
3. **Add Tasks**: Create your own benchmark tasks
4. **Analyze Results**: Deep dive into the generated reports

## Troubleshooting

### "Cannot find module" error

Make sure you're running from the project root:
```bash
cd /path/to/dream
node benchmark/index.js
```

### API Key errors

Verify your API keys are set:
```bash
echo $OPENAI_API_KEY
echo $ANTHROPIC_API_KEY
```

### TypeScript tasks failing

Install tsx for TypeScript support:
```bash
npm install -D tsx
```

### Empty reports

Make sure at least one benchmark ran successfully. Check for API errors in the console output.

## Tips

1. **Start Small**: Begin with a single task to verify everything works
2. **Monitor Costs**: Keep an eye on your API usage
3. **Review Results**: Manually check some outputs to validate the scoring
4. **Iterate**: Use insights from results to improve your tasks

Happy benchmarking! 🚀
