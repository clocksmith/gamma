# DREAM Benchmark Suite Guide

**D**ynamic, **R**obust, **E**xtensive, **A**ccurate **M**etrics

A comprehensive, next-generation benchmarking framework for LLM code generation with TypeScript/JavaScript focus.

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Core Concepts](#core-concepts)
- [Advanced Features](#advanced-features)
- [CLI Reference](#cli-reference)
- [API Documentation](#api-documentation)
- [Best Practices](#best-practices)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

## Overview

The DREAM Benchmark Suite provides enterprise-grade benchmarking capabilities for evaluating Large Language Models on code generation tasks, with sophisticated statistical analysis, historical tracking, and interactive visualization.

### What's New in DREAM?

- **Statistical Rigor**: Confidence intervals, significance testing, outlier detection
- **Advanced Metrics**: Cyclomatic complexity, maintainability index, type safety scores
- **Historical Tracking**: Regression detection and trend analysis
- **Interactive Dashboards**: Rich HTML dashboards with filtering and drill-down
- **Property-Based Testing**: Auto-generate comprehensive test suites
- **Preset Configurations**: Pre-configured suites for common scenarios
- **Enhanced Navigation**: Easy exploration and comparison of results

## Key Features

### 1. Statistical Analysis

Comprehensive statistical methods for robust benchmarking:

```javascript
import { StatisticalAnalyzer } from './utils/statistical-analyzer.js';

const results = [85, 87, 86, 89, 88];
const stats = StatisticalAnalyzer.calculateStats(results);

console.log(stats.mean);           // 87
console.log(stats.median);         // 87
console.log(stats.stdDev);         // 1.41
console.log(stats.percentiles.p95); // 88.8

// Confidence intervals
const ci = StatisticalAnalyzer.confidenceInterval(results, 0.95);
console.log(`95% CI: ${ci.lower.toFixed(2)} - ${ci.upper.toFixed(2)}`);

// Statistical significance testing
const group1 = [85, 87, 86, 89, 88];
const group2 = [82, 84, 83, 85, 84];
const tTest = StatisticalAnalyzer.tTest(group1, group2);
console.log(`Significant difference: ${tTest.isSignificant}`);
console.log(`Effect size: ${tTest.effectSize}`);
```

### 2. Advanced Code Metrics

Creative and sophisticated code analysis:

```javascript
import { AdvancedMetrics } from './utils/advanced-metrics.js';

const code = `
function fibonacci(n: number): number {
  if (n <= 1) return n;
  return fibonacci(n - 1) + fibonacci(n - 2);
}
`;

const analysis = AdvancedMetrics.analyzeCode(code, 'typescript');

console.log(analysis.complexity);        // Cyclomatic complexity: 3
console.log(analysis.maintainability);   // Maintainability index: 85/100
console.log(analysis.typeSafety);        // Type safety score: 75/100
console.log(analysis.bugRisk);           // Bug risk: low
console.log(analysis.readability);       // Readability: highly readable
```

**Available Metrics:**
- Cyclomatic Complexity
- Maintainability Index
- Type Safety Score (TypeScript/JSDoc)
- Halstead Complexity
- Code Readability Score
- Bug Risk Analysis
- Code Duplication Detection
- Dependency Complexity

### 3. Historical Tracking & Regression Detection

Track performance over time and catch regressions:

```javascript
import { HistoricalTracker } from './utils/historical-tracker.js';

const tracker = new HistoricalTracker();

// Save results to history
await tracker.saveResults(results, {
  preset: 'comprehensive',
  git_branch: 'main'
});

// Compare with baseline
const comparison = await tracker.compareWithBaseline(currentResults, 5);

if (comparison.regressions.length > 0) {
  console.log('⚠️  Regressions detected!');
  console.log(tracker.generateRegressionReport(comparison.regressions));
}

// Analyze trends
const trends = await tracker.analyzeTrends('score', 'variant');
for (const [variant, analysis] of Object.entries(trends.trends)) {
  console.log(`${variant}: ${analysis.trend.trend} (${analysis.trend.percentChange.toFixed(1)}%)`);
}
```

### 4. Interactive Dashboard

Beautiful, functional HTML dashboards with:
- Real-time filtering and sorting
- Statistical summaries and charts
- Drill-down into individual results
- CSV/JSON export capabilities
- Responsive design for all devices

```javascript
import { DashboardGenerator } from './utils/dashboard-generator.js';

await DashboardGenerator.generate(
  results,
  './reports/dashboard.html'
);
```

### 5. Property-Based Test Generation

Automatically generate comprehensive test suites:

```javascript
import { TestGenerator } from './utils/test-generator.js';

const functionSignature = {
  name: 'add',
  params: [
    { name: 'a', type: 'number' },
    { name: 'b', type: 'number' }
  ],
  description: 'Adds two numbers'
};

// Generate property-based tests
const tests = TestGenerator.generatePropertyTests(functionSignature, [
  'commutativity',
  'identity',
  'boundaryConditions',
  'typeInvariance'
]);

// Generate fuzzing tests
const fuzzTests = TestGenerator.generateFuzzingTests(functionSignature, 100);

// Generate stress tests
const stressTests = TestGenerator.generateStressTests(functionSignature);
```

### 6. Benchmark Presets

Pre-configured suites for common scenarios:

```bash
# Quick validation (fast smoke test)
node dream-cli.js run --preset quick

# Comprehensive (full test suite)
node dream-cli.js run --preset comprehensive

# Performance-focused
node dream-cli.js run --preset performance

# Quality-focused
node dream-cli.js run --preset quality

# Type safety comparison
node dream-cli.js run --preset typeSafety

# Cost-optimized
node dream-cli.js run --preset costOptimized

# CI/CD pipeline
node dream-cli.js run --preset ci
```

## Quick Start

### Basic Usage

```bash
# Install dependencies
npm install

# Run quick test
node dream-cli.js run --preset quick

# Run with specific provider and variant
node dream-cli.js run --provider openai-gpt4 --variant typescript

# Run with historical tracking and comparison
node dream-cli.js run --preset comprehensive --historical --compare

# Run with advanced metrics
node dream-cli.js run --preset quality --advanced-metrics
```

### Using Presets

```bash
# List all available presets
node dream-cli.js presets

# Use a preset
node dream-cli.js run --preset performance

# Override preset settings
node dream-cli.js run --preset quick --runs 5 --timeout 60000
```

### Historical Analysis

```bash
# View benchmark history
node dream-cli.js history

# Compare recent results
node dream-cli.js compare

# Analyze trends over time
node dream-cli.js analyze
```

## Installation

### Prerequisites

- Node.js 16+ or Node.js 18+
- npm or yarn
- API keys for LLM providers (or use --dry-run)

### Setup

```bash
# Clone repository
git clone <repo-url>
cd src/benchmarks/language_comparison

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Verify installation
node dream-cli.js --help
```

### Required API Keys

Add to `.env` file:

```env
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
GEMINI_API_KEY=your-gemini-key
OLLAMA_BASE_URL=http://localhost:11434  # Optional
```

## Core Concepts

### Benchmark Structure

```javascript
{
  name: "task-name",
  description: "Task description",
  category: "simple|large-projects|...",
  difficulty: "easy|medium|hard",
  variants: {
    typescript: "TypeScript-specific prompt",
    javascript: "JavaScript-specific prompt",
    "javascript-jsdoc": "JavaScript with JSDoc prompt"
  },
  testCases: [
    { test: "console.assert(fibonacci(5) === 5);" }
  ],
  requirements: ["function", "fibonacci", "export"]
}
```

### Evaluation Criteria

Each benchmark is evaluated on:

1. **Accuracy (40%)**: Correctness of the solution
2. **Performance (20%)**: Efficiency and speed
3. **Code Quality (20%)**: Best practices and maintainability
4. **Completeness (20%)**: Thoroughness of implementation

### Results Structure

```javascript
{
  taskName: "fibonacci",
  provider: "openai-gpt4",
  variant: "typescript",
  run: 1,
  duration: 1523,
  evaluation: {
    scores: {
      accuracy: 1.0,
      performance: 0.9,
      codeQuality: 0.85,
      completeness: 0.95
    },
    totalScore: 92.5,
    metrics: {
      codeLength: { ... },
      tokenMetrics: { ... },
      efficiency: { ... }
    }
  },
  success: true
}
```

## Advanced Features

### Custom Metrics

Add your own metrics to the evaluation:

```javascript
import { AdvancedMetrics } from './utils/advanced-metrics.js';

// Extend the AdvancedMetrics class
class CustomMetrics extends AdvancedMetrics {
  static analyzeCustomAspect(code) {
    // Your custom analysis logic
    return {
      score: 85,
      details: { ... }
    };
  }
}
```

### Custom Presets

Create custom benchmark presets:

```javascript
import { PresetManager } from './presets.js';

const myPreset = PresetManager.createCustomPreset(
  'my-preset',
  'My custom benchmark suite',
  {
    categories: ['simple', 'bug-finding'],
    runs: 3,
    timeout: 90000,
    providers: ['openai-gpt4'],
    variants: ['typescript'],
    evaluationWeights: {
      accuracy: 0.5,
      performance: 0.2,
      codeQuality: 0.2,
      completeness: 0.1
    }
  }
);
```

### Programmatic API

Use the benchmark suite programmatically:

```javascript
import { BenchmarkRunner } from './runner/benchmark-runner.js';
import { BenchmarkConfig } from './config.js';

const config = {
  ...BenchmarkConfig,
  runs: 5,
  timeout: 120000
};

const runner = new BenchmarkRunner(config);

const results = await runner.run({
  category: 'simple',
  providers: ['openai-gpt4'],
  variants: ['typescript']
});

// Process results
console.log(`Completed ${results.length} tests`);
```

## CLI Reference

### Commands

- `run` - Run benchmarks (default)
- `presets` - List available presets
- `history` - Show benchmark history
- `compare` - Compare recent results
- `analyze` - Analyze trends
- `help` - Show help

### Options

- `--preset, -p <name>` - Use a benchmark preset
- `--provider <name>` - Run only specified provider(s)
- `--variant, -v <name>` - Run only specified variant(s)
- `--category, -c <name>` - Run only specified category(s)
- `--task, -t <name>` - Run only specified task
- `--runs, -r <n>` - Number of runs per test
- `--timeout <ms>` - Timeout per test
- `--compare` - Compare with historical baseline
- `--historical` - Save results to history
- `--advanced-metrics, -am` - Compute advanced code metrics
- `--no-dashboard` - Skip dashboard generation
- `--output, -o <path>` - Output path for dashboard
- `--dry-run, --mock` - Use mock LLM responses
- `--quiet, -q` - Suppress verbose output

## Best Practices

### 1. Use Multiple Runs for Statistical Validity

```bash
node dream-cli.js run --preset comprehensive --runs 5
```

### 2. Track History for Regression Detection

```bash
node dream-cli.js run --preset regression --historical --compare
```

### 3. Use Presets for Consistency

```bash
# Always use the same preset for comparable results
node dream-cli.js run --preset performance
```

### 4. Monitor Costs

```bash
# Check estimated costs before running
node dream-cli.js presets

# Use cost-optimized preset for development
node dream-cli.js run --preset costOptimized
```

### 5. Leverage Advanced Metrics

```bash
# Get deeper insights
node dream-cli.js run --preset quality --advanced-metrics
```

## Examples

### Example 1: Quick Validation

```bash
node dream-cli.js run --preset quick
```

### Example 2: Comprehensive with History

```bash
node dream-cli.js run --preset comprehensive --historical --compare --advanced-metrics
```

### Example 3: Provider Comparison

```bash
node dream-cli.js run \
  --category simple \
  --provider openai-gpt4 anthropic-claude openai-gpt35 \
  --variant typescript \
  --runs 5
```

### Example 4: Type Safety Analysis

```bash
node dream-cli.js run --preset typeSafety --advanced-metrics
```

### Example 5: Custom Configuration

```bash
node dream-cli.js run \
  --variant typescript javascript \
  --provider openai-gpt4 \
  --category simple bug-finding \
  --runs 3 \
  --timeout 120000 \
  --historical
```

## Troubleshooting

### No API Keys

If you don't have API keys, use dry-run mode:

```bash
node dream-cli.js run --preset quick --dry-run
```

### Timeout Issues

Increase timeout for complex tasks:

```bash
node dream-cli.js run --timeout 300000  # 5 minutes
```

### Missing Dependencies

```bash
npm install
```

### Permission Issues

Make CLI executable:

```bash
chmod +x dream-cli.js
```

## Architecture

```
language_comparison/
├── utils/
│   ├── statistical-analyzer.js    # Statistical analysis
│   ├── advanced-metrics.js        # Code metrics
│   ├── historical-tracker.js      # History & regression
│   ├── dashboard-generator.js     # Interactive dashboards
│   └── test-generator.js          # Test generation
├── runner/
│   ├── benchmark-runner.js        # Core runner
│   └── llm-client.js             # LLM API client
├── evaluator/
│   └── evaluator.js              # Result evaluation
├── reports/
│   └── report-generator.js       # Report generation
├── tasks/                        # Benchmark tasks
├── presets.js                    # Benchmark presets
├── dream-cli.js                  # Enhanced CLI
└── config.js                     # Configuration
```

## Contributing

Contributions welcome! Areas of interest:
- Additional metrics
- New benchmark presets
- Enhanced visualizations
- Additional LLM providers
- Documentation improvements

## License

MIT License

## Support

For issues or questions:
- Open an issue on GitHub
- Check existing documentation
- Review examples in `/examples`

---

Built with ❤️ for the LLM benchmarking community
