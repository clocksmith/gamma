# Benchmark Results Analysis

Helper tools to analyze and visualize benchmark results with detailed metrics.

## Tools Available

### 1. Python Analyzer (`analyze_results.py`)

**Features:**
- Comprehensive metrics display
- Provider and variant comparisons
- Code length, token efficiency, and speed metrics
- CSV export for further analysis

**Usage:**

```bash
# Basic analysis
python3 benchmark/analyze_results.py benchmark/results/results-*.json

# With CSV export
python3 benchmark/analyze_results.py benchmark/results/results-*.json --csv

# Specific file
python3 benchmark/analyze_results.py benchmark/results/results-2025-10-14T17-31-53-729Z.json
```

### 2. JavaScript/Node Analyzer (`analyze_results.cjs`)

**Same features as Python version, but runs with Node.js**

**Usage:**

```bash
# Basic analysis
node benchmark/analyze_results.cjs benchmark/results/results-*.json

# With CSV export
node benchmark/analyze_results.cjs benchmark/results/results-*.json --csv

# Specific file
node benchmark/analyze_results.cjs benchmark/results/results-2025-10-14T17-31-53-729Z.json
```

## Metrics Tracked

### Performance Metrics
- **Duration** - Total time to generate code (seconds)
- **Tokens/Second** - Generation speed
- **Output Tokens** - Total tokens generated
- **Code Lines** - Actual lines of code (excluding comments/whitespace)

### Code Quality Metrics
- **Total Characters** - Overall code length
- **Comment Lines** - Documentation added
- **Chars/Token** - Token efficiency ratio
- **Accuracy Score** - Test case pass rate
- **Code Quality Score** - Best practices adherence
- **Completeness Score** - Requirement fulfillment

### Comparison Metrics
- **By Provider** - Compare different LLMs (GPT-4, Claude, Gemini, Ollama models)
- **By Variant** - Compare TypeScript vs JavaScript vs JSDoc
- **By Task** - Compare performance across different coding tasks

## Sample Output

```
================================================================================
BENCHMARK RESULTS ANALYSIS: results-2025-10-14T17-31-53-729Z.json
================================================================================

📊 Overview:
   Total Runs: 3
   ✓ Successful: 3
   ✗ Failed: 0
   Success Rate: 100.0%

⚡ Performance Metrics:
   Average Duration: 18.55s
   Average Tokens/Second: 4.71
   Average Output Tokens: 89
   Average Code Lines: 6.0

🤖 Provider Comparison:
   Provider             | Runs   | Avg Time   | Tok/s    | Lines   | Tokens
   --------------------------------------------------------------------------
   ollama-gemma3-27b    | 3      | 18.55s     | 4.7      | 6.0     | 89

📝 Variant Comparison:
   Variant              | Runs   | Avg Time   | Lines   | Chars   | Comments  | Chars/Tok
   ---------------------------------------------------------------------------------------
   javascript           | 1      | 20.01s     | 6.0     | 293     | 6.0       | 2.90
   javascript-jsdoc     | 1      | 21.16s     | 6.0     | 292     | 6.0       | 2.73
   typescript           | 1      | 14.46s     | 6.0     | 129     | 0.0       | 2.22
```

## CSV Export

The `--csv` flag exports results to CSV format for analysis in spreadsheet tools or data visualization libraries.

**CSV Columns:**
```
provider,variant,task,duration_s,tokens_per_sec,code_lines,output_tokens,
total_chars,comment_lines,chars_per_token,accuracy,quality,completeness
```

**Example:**
```bash
python3 benchmark/analyze_results.py benchmark/results/results-*.json --csv
# Creates: benchmark/results/results-2025-10-14T17-31-53-729Z.csv
```

You can then import this CSV into:
- **Excel/Google Sheets** - For pivot tables and charts
- **Pandas** - For Python data analysis
- **R** - For statistical analysis
- **Tableau/PowerBI** - For advanced visualizations

## Use Cases

### 1. Compare Local Models
```bash
# Run benchmarks on your local Ollama models
node benchmark/index.js --task fibonacci --provider ollama-gpt-oss-20b
node benchmark/index.js --task fibonacci --provider ollama-gemma3-27b

# Analyze and compare
python3 benchmark/analyze_results.py benchmark/results/results-*.json
```

### 2. Evaluate Cloud vs Local
```bash
# Compare cloud API performance with local models
node benchmark/index.js --task fibonacci
python3 benchmark/analyze_results.py benchmark/results/results-*.json --csv
```

### 3. TypeScript vs JavaScript Analysis
```bash
# Run full benchmark suite
node benchmark/index.js --category simple

# Analyze variant differences
python3 benchmark/analyze_results.py benchmark/results/results-*.json
```

### 4. Track Performance Over Time
```bash
# Export all results to CSV for trending
for file in benchmark/results/results-*.json; do
  python3 benchmark/analyze_results.py "$file" --csv
done
```

## Key Insights From Metrics

### Speed Comparison
- **Local models** (Ollama): 4-6 tokens/second, ~15-20s for simple tasks
- **Cloud APIs** (GPT-4, Claude): 20-40 tokens/second, ~2-5s for simple tasks
- **Tradeoff**: Cloud is faster but costs money, local is free but slower

### Code Efficiency
- **TypeScript**: Usually fewer characters (more concise)
- **JavaScript + JSDoc**: More characters due to documentation
- **Chars/Token**: Lower is more efficient (TypeScript ~2.2, JSDoc ~2.7)

### Quality Patterns
- **TypeScript**: Higher accuracy on complex tasks
- **JSDoc**: Good middle ground between speed and safety
- **Plain JS**: Fastest generation but more prone to type errors

## Tips

1. **Use wildcards** to analyze the most recent results:
   ```bash
   python3 benchmark/analyze_results.py benchmark/results/results-*.json
   ```

2. **Export to CSV** for deeper analysis in other tools:
   ```bash
   python3 benchmark/analyze_results.py benchmark/results/results-*.json --csv
   ```

3. **Compare specific providers** by filtering CSV data

4. **Track trends** by analyzing multiple result files over time
