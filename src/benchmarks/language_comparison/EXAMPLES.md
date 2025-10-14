# Benchmark Examples

This document provides practical examples of running benchmarks and interpreting results.

## Example 1: Quick Smoke Test

Test a single simple task across all variants:

```bash
node benchmark/index.js --task fibonacci
```

**Expected Output:**
```
=== LLM TypeScript/JavaScript Benchmark Suite ===

[openai-gpt4] [typescript] Running: fibonacci
✓ Completed in 2341ms - Score: 87.50

[openai-gpt4] [javascript] Running: fibonacci
✓ Completed in 1923ms - Score: 82.30

[openai-gpt4] [javascript-jsdoc] Running: fibonacci
✓ Completed in 2156ms - Score: 85.10

... (more variants)

--- Summary ---
Average Score: 84.27/100
```

**What to look for:**
- TypeScript usually scores highest (type safety helps)
- JSDoc is often close to TypeScript
- Plain JavaScript may have lower code quality scores

---

## Example 2: Compare Web Variants

Run a web component task to compare vanilla approaches:

```bash
node benchmark/index.js --task counter-component
```

This will test:
- `typescript` - Pure logic
- `javascript` - Pure logic
- `javascript-jsdoc` - Pure logic with docs
- `javascript-vanilla-web` - Full HTML/CSS/JS implementation
- `javascript-vanilla-web-jsdoc` - Same with JSDoc
- `typescript-vanilla-web` - TypeScript with DOM APIs
- `typescript-react` - React component

**Expected Insights:**
- Vanilla web variants produce more code (HTML/CSS)
- React variant is most concise
- TypeScript variants catch more errors
- All should function identically

---

## Example 3: Test Only React

Run all React benchmarks:

```bash
node benchmark/index.js --variant typescript-react
```

**Use case:** Evaluating LLM performance on React-specific tasks

---

## Example 4: Full Category Test

Test all UI components:

```bash
node benchmark/index.js --category ui-components
```

**What this tests:**
- Modal dialogs
- Data tables
- Form validation
- Complex interactions
- State management

**Expected results:**
- Shows which variants handle complex UI best
- Reveals framework vs. vanilla trade-offs
- Highlights type safety benefits in complex scenarios

---

## Example 5: Provider Comparison

Compare different LLM providers on TypeScript:

```bash
# GPT-4 only
node benchmark/index.js --provider openai-gpt4 --variant typescript

# Claude only
node benchmark/index.js --provider anthropic-claude --variant typescript

# Then compare the reports
```

---

## Example 6: Bug Finding Challenge

Test how well LLMs find bugs:

```bash
node benchmark/index.js --category bug-finding
```

**Expected behavior:**
- TypeScript should catch type-related bugs
- JSDoc may catch some bugs with proper tooling
- Plain JavaScript relies on LLM understanding

---

## Interpreting Results

### Reading Scores

Scores are 0-100 with four components:

1. **Accuracy (40%)**: Does it work?
   - 100: All tests pass, correct output
   - 75: Most tests pass
   - 50: Partial functionality
   - 0: Doesn't work

2. **Performance (20%)**: How efficient?
   - Based on token usage and execution time
   - 100: Very efficient
   - 50: Average
   - 0: Very slow/inefficient

3. **Code Quality (20%)**: Is it maintainable?
   - Checks: indentation, naming, comments, error handling
   - 100: Excellent code quality
   - 50: Basic quality
   - 0: Poor quality

4. **Completeness (20%)**: How thorough?
   - 100: All requirements met, edge cases handled
   - 50: Basic requirements only
   - 0: Incomplete

### Example Score Breakdown

```
Task: todo-app
Provider: openai-gpt4
Variant: typescript

Accuracy: 0.95 (95%)      - One test failed
Performance: 0.80 (80%)   - Moderate token usage
Code Quality: 0.90 (90%)  - Well-written code
Completeness: 0.85 (85%)  - Missing one edge case

Total Score: 89.5/100
```

---

## Common Patterns in Results

### Pattern 1: TypeScript Scores Highest

```
typescript:            87.5
javascript-jsdoc:      82.3
javascript:            78.1
```

**Why:** Type safety catches errors, improves correctness

---

### Pattern 2: Web Variants Have More Code

```
javascript:              50 lines
javascript-vanilla-web:  150 lines (includes HTML/CSS)
typescript-react:        80 lines
```

**Why:** Web variants include presentation layer

---

### Pattern 3: Complex Tasks Show Bigger Gaps

Simple task scores:
```
typescript:   85
javascript:   82
```

Complex task scores:
```
typescript:   88
javascript:   72
```

**Why:** Type safety helps more in complex scenarios

---

## Sample Report Output

### Summary Report (`reports/summary.md`)

```markdown
# LLM TypeScript/JavaScript Benchmark Summary

## Overall Performance
- Average Score: 84.27/100
- Average Duration: 2.14s

## Performance by Language Variant
### typescript
- Score: 86.50/100
- Avg Duration: 2.31s
- Tasks: 12

### javascript
- Score: 81.20/100
- Avg Duration: 1.89s
- Tasks: 12

### javascript-jsdoc
- Score: 85.10/100
- Avg Duration: 2.05s
- Tasks: 12
```

### Comparison Report (`reports/comparison.md`)

```markdown
# LLM Comparison Report

## TypeScript vs JavaScript vs JavaScript+JSDoc

| Provider | typescript | javascript | javascript-jsdoc |
|----------|------------|------------|------------------|
| openai-gpt4 | 86.50 | 81.20 | 85.10 |
| anthropic-claude | 88.20 | 82.50 | 86.30 |
```

---

## Real-World Use Cases

### Use Case 1: Choosing a Stack

**Goal:** Should we use TypeScript or JavaScript+JSDoc?

**Benchmark:**
```bash
node benchmark/index.js --variant typescript
node benchmark/index.js --variant javascript-jsdoc
```

**Compare:**
- Accuracy scores (does JSDoc catch enough errors?)
- Code quality (is JSDoc well-maintained?)
- Complexity handling (how do they compare on hard tasks?)

**Decision factors:**
- If TypeScript scores 5+ points higher: Use TypeScript
- If scores are close: Consider team preference
- Check specific task categories relevant to your project

---

### Use Case 2: Framework Decision

**Goal:** React or vanilla JavaScript?

**Benchmark:**
```bash
node benchmark/index.js --category ui-components
```

**Look at:**
- Code length (is React more concise?)
- Complexity (is vanilla too complex for your team?)
- Maintainability (code quality scores)

---

### Use Case 3: Evaluating LLMs

**Goal:** Which LLM is best for our codebase?

**Benchmark:**
```bash
# Run all providers
node benchmark/index.js
```

**Analyze:**
- Overall scores by provider
- Performance on tasks similar to your work
- Cost vs. quality trade-offs

---

## Tips for Running Benchmarks

### 1. Start Small
```bash
# Don't start with this:
node benchmark/index.js  # 100+ tasks!

# Start with this:
node benchmark/index.js --task fibonacci
```

### 2. Target Your Stack
```bash
# If you use TypeScript React:
node benchmark/index.js --variant typescript-react

# Compare against alternatives:
node benchmark/index.js --variant typescript-vanilla-web
```

### 3. Test Incrementally
```bash
# Day 1: Simple tasks
node benchmark/index.js --category simple

# Day 2: Web components
node benchmark/index.js --category web-components

# Day 3: Full projects
node benchmark/index.js --category full-projects
```

### 4. Monitor Costs
- Each task = 1-3 API calls
- Set API spending limits
- Use cheaper models for initial testing:
  ```bash
  # Edit config.js to only include gpt-3.5-turbo
  ```

### 5. Review Manually
- Don't just trust scores
- Read some generated code
- Check for patterns or issues
- Validate edge cases

---

## Troubleshooting Examples

### Example: Low Scores Across the Board

**Symptom:**
```
All scores: 40-50/100
```

**Possible causes:**
1. Task prompts too vague
2. API models outdated
3. Evaluation criteria too strict

**Solutions:**
- Review task prompts
- Check model versions in config
- Adjust evaluation weights

---

### Example: Huge Variance Between Variants

**Symptom:**
```
typescript:   90/100
javascript:   45/100
```

**Analysis:**
- Task may favor TypeScript unfairly
- Prompts may not be equivalent
- Evaluation may over-weight type safety

**Solutions:**
- Review task prompts for bias
- Ensure prompts are truly equivalent
- Check if evaluation is fair

---

### Example: All Tests Failing

**Symptom:**
```
✗ Failed: Timeout
✗ Failed: Timeout
```

**Solutions:**
1. Increase timeout in config.js
2. Simplify complex tasks
3. Check API rate limits
4. Verify API keys are valid

---

## Advanced Examples

### Custom Evaluation

Edit `evaluator/evaluator.js` to add custom checks:

```javascript
// Add custom code quality check
evaluateCustomQuality(code) {
  let score = 0;

  // Check for specific patterns your team uses
  if (code.includes('use strict')) score += 0.2;
  if (/^\/\*\*/.test(code)) score += 0.3; // Has doc comment

  return score;
}
```

### Filter Reports by Score

```bash
# Run benchmark
node benchmark/index.js

# Filter results
cat benchmark/results/results-*.json | \
  jq '.[] | select(.evaluation.totalScore > 85)'
```

### Compare Against Baseline

```bash
# Save baseline
node benchmark/index.js > baseline.txt

# Make changes, run again
node benchmark/index.js > current.txt

# Compare
diff baseline.txt current.txt
```

---

## Next Steps

1. Run your first benchmark (Example 1)
2. Review the generated reports
3. Explore the HTML dashboard
4. Try category-specific tests
5. Create custom tasks for your use cases

Happy benchmarking! 🎯
