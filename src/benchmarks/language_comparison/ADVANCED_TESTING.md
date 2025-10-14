# Advanced Testing Framework

Comprehensive evaluation system that addresses real-world testing needs:
- **Multiple runs with temperature variations** to test consistency
- **Statistical analysis** to measure variance and reliability
- **Partial credit scoring** for close answers
- **Playwright E2E testing** for UI components
- **Visual regression testing** to ensure UI accuracy
- **Accessibility testing** for inclusive design

## Quick Start

### 1. Install Dependencies

```bash
cd benchmark
npm install playwright pixelmatch pngjs
npx playwright install chromium
```

### 2. Run Advanced Benchmarks

```bash
# Simple function testing with multiple runs
node advanced-runner.js --task fibonacci --runs 5 --temperatures 0.0,0.2,0.7

# UI component testing with Playwright
node advanced-runner.js --task counter-component --ui-test

# Full statistical analysis
node advanced-runner.js --category simple --runs 10 --full-analysis
```

## Key Features

### 1. Temperature Variation Testing

Tests model at different creativity levels:

```javascript
temperatures: [
  0.0,  // Deterministic - should produce identical results
  0.2,  // Slightly varied - default for most tasks
  0.7,  // Creative - more variation
  1.0   // Maximum creativity - high variance expected
]
```

**Why This Matters:**
- Temperature 0.0 tests if model can be deterministic
- Higher temperatures test if model maintains correctness while being creative
- Variance analysis shows which models are more stable

### 2. Multiple Runs Per Configuration

Run each test 5-10 times to get statistical significance:

```javascript
runsPerConfig: 5  // Run each temperature setting 5 times
```

**Metrics Calculated:**
- **Mean Score** - Average performance
- **Standard Deviation** - How much variance
- **Consistency Score** - Penalize high variance
- **Code Similarity** - Are outputs deterministic?

### 3. Enhanced Accuracy Scoring

#### Partial Credit System

Instead of pass/fail, award partial credit for close answers:

```javascript
// Example: fibonacci(10) expects 55
Actual: 56    → 90% credit (within 1% error)
Actual: 58    → 70% credit (within 5% error)
Actual: 60    → 50% credit (within 10% error)
Actual: 70    → 30% credit (within 25% error)
Actual: 100   → 0% credit (too far off)
```

#### Deviation Metrics

Track how far outputs deviate from expected:

```javascript
{
  absoluteError: 1,           // How far off
  percentError: 1.8%,         // Percent deviation
  withinTolerance: true       // < 5% error
}
```

### 4. Playwright E2E Testing

For UI components, test actual functionality:

#### Counter Component Example

```javascript
{
  "name": "counter-component",
  "evaluationType": "playwright",
  "interactions": [
    {
      "name": "initial_state",
      "type": "check",
      "selector": "#count",
      "expected": { "text": "0" }
    },
    {
      "name": "increment",
      "type": "click",
      "selector": "#increment",
      "expected": { "selector": "#count", "text": "1" }
    },
    {
      "name": "decrement",
      "type": "click",
      "selector": "#decrement",
      "expected": { "selector": "#count", "text": "0" }
    }
  ],
  "expectedElements": ["#count", "#increment", "#decrement"]
}
```

**What Gets Tested:**
- ✅ Elements exist in DOM
- ✅ Click interactions work
- ✅ State updates correctly
- ✅ No console errors
- ✅ Visual appearance matches
- ✅ Accessibility compliance

### 5. Visual Regression Testing

Compare screenshots pixel-by-pixel:

```javascript
visualRegression: {
  enabled: true,
  threshold: 0.05,  // 5% pixel difference allowed
  compareScreenshots: true
}
```

**Process:**
1. First run creates baseline screenshot
2. Subsequent runs compare against baseline
3. Report pixel difference percentage
4. Save diff image highlighting changes

**Example Output:**
```
Visual Regression Test:
  Baseline: counter-component-baseline.png
  Current:  counter-component-1730745120.png
  Diff:     0.3% pixels different ✓
  Status:   PASS (below 5% threshold)
```

### 6. Statistical Analysis

Full statistical breakdown across runs:

```javascript
statistics: {
  scores: {
    mean: 87.5,
    median: 88.0,
    stdDev: 2.1,          // Low variance = good
    variance: 4.41,
    min: 84.0,
    max: 91.0,
    range: 7.0
  },
  accuracy: {
    mean: 0.95,           // 95% correct on average
    stdDev: 0.03,         // Very consistent
    consistency: 0.97     // High consistency
  },
  consistency: 0.94,      // Overall consistency score
  codeVariability: 0.2    // 20% unique outputs (80% same)
}
```

## Example Task Configuration

### Simple Function with Statistical Testing

```json
{
  "name": "fibonacci",
  "category": "simple",
  "evaluationType": "unit-test",
  "testCases": [
    { "test": "console.assert(fibonacci(0) === 0)" },
    { "test": "console.assert(fibonacci(10) === 55)" }
  ],
  "testConfig": {
    "runs": 5,
    "temperatures": [0.0, 0.2, 0.7],
    "partialCredit": true,
    "numericalTolerance": 0.01
  }
}
```

### UI Component with E2E Testing

```json
{
  "name": "counter-component",
  "category": "ui-components",
  "evaluationType": "playwright",
  "interactions": [
    {
      "name": "increment_button",
      "type": "click",
      "selector": "button[data-action='increment']",
      "expected": {
        "selector": "[data-count]",
        "text": "1"
      }
    }
  ],
  "visualRegression": true,
  "accessibility": true,
  "performance": {
    "maxLoadTime": 1000
  }
}
```

## Running Comprehensive Tests

### Option 1: Single Task, Multiple Temperatures

```bash
node advanced-runner.js \
  --task fibonacci \
  --provider ollama-gemma3-27b \
  --runs 10 \
  --temperatures 0.0,0.2,0.5,0.7,1.0
```

**Output:**
```
Temperature 0.0 (10 runs):
  Mean Score: 92.5 ± 1.2
  Consistency: 98% (highly deterministic)

Temperature 0.2 (10 runs):
  Mean Score: 91.8 ± 2.5
  Consistency: 95%

Temperature 0.7 (10 runs):
  Mean Score: 88.3 ± 8.7
  Consistency: 76% (more creative but less consistent)
```

### Option 2: UI Testing with Visual Regression

```bash
node advanced-runner.js \
  --task counter-component \
  --provider ollama-gemma3-27b \
  --ui-test \
  --visual-regression
```

**Output:**
```
Playwright E2E Tests:
  ✓ Elements render correctly
  ✓ Increment button works
  ✓ Decrement button works
  ✓ Counter state persists
  ✗ Visual regression: 8.3% difference (threshold: 5%)
  ✓ No console errors
  ✓ Accessibility: WCAG Level A

Overall Score: 85/100
```

### Option 3: Full Comparison Across Models

```bash
node advanced-runner.js \
  --category simple \
  --runs 5 \
  --temperatures 0.0,0.2 \
  --all-providers
```

**Generates Report:**
```
Statistical Comparison:

Provider          | Temp | Mean Score | Std Dev | Consistency
------------------------------------------------------------
ollama-gpt-oss    | 0.0  | 89.2       | 1.5     | 97%
ollama-gpt-oss    | 0.2  | 88.5       | 3.2     | 94%
ollama-gemma3     | 0.0  | 91.8       | 2.1     | 96%
ollama-gemma3     | 0.2  | 90.3       | 4.5     | 91%
```

## Interpreting Results

### Good Model Characteristics

1. **Low Standard Deviation** (< 5)
   - Consistent outputs across runs
   - Reliable for production

2. **High Consistency Score** (> 0.9)
   - Similar code structure each time
   - Predictable behavior

3. **Temperature Stability**
   - Performance doesn't degrade much at temp 0.2-0.5
   - Can be creative while staying correct

4. **Visual Regression Pass Rate** (> 95%)
   - UI outputs match expected design
   - No unexpected visual bugs

### Red Flags

1. **High Variance** (std dev > 10)
   - Unpredictable outputs
   - May fail in production

2. **Temperature Sensitivity**
   - Large score drop at temp > 0.2
   - Cannot handle creative prompts

3. **Visual Regression Failures**
   - UI looks different each time
   - Inconsistent styling

## Best Practices

### 1. Start with Low Temperature

```bash
# Test determinism first
node advanced-runner.js --task fibonacci --temp 0.0 --runs 10
```

If std dev > 5 at temp 0.0, the model is non-deterministic even when it should be!

### 2. Use Multiple Runs for Important Tasks

```bash
# Production-critical code needs high confidence
node advanced-runner.js --task auth-component --runs 20
```

### 3. Visual Regression for All UI

```bash
# Always check visual consistency
node advanced-runner.js --category ui-components --visual-regression
```

### 4. Track Metrics Over Time

```bash
# Export results for trending
python3 analyze_advanced_results.py --export-csv --time-series
```

## Advanced Analysis

### Compare Model Stability

```bash
python3 analyze_advanced_results.py \
  --compare-providers \
  --metric consistency \
  --chart stability.png
```

### Find Optimal Temperature

```bash
python3 analyze_advanced_results.py \
  --temperature-analysis \
  --provider ollama-gemma3-27b
```

### Visual Regression Report

```bash
python3 analyze_advanced_results.py \
  --visual-regression-summary \
  --threshold 0.05
```

## Why This Matters

### Speed Alone Doesn't Matter

A model that generates code in 5 seconds but:
- Produces different outputs each time (inconsistent)
- Fails 20% of test cases (unreliable)
- Breaks visual design (poor quality)

is WORSE than a model that takes 20 seconds but:
- Produces identical outputs (deterministic)
- Passes 100% of test cases (reliable)
- Matches design perfectly (high quality)

### Real-World Use Cases

**Production Code:**
- Need low temperature (0.0-0.2)
- Need high consistency (> 95%)
- Need 100% test pass rate

**Prototyping:**
- Can use higher temperature (0.5-0.7)
- Can accept some variance
- Speed matters more

**UI Development:**
- Need visual regression testing
- Need accessibility compliance
- Need cross-browser testing

This framework tests what actually matters for real-world usage! 🎯
