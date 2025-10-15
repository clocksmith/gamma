# DREAM: LLM Code Generation Benchmark Suite

**D**ynamic, **R**obust, **E**xtensive, **A**ccurate **M**etrics

A comprehensive benchmark suite for evaluating LLMs on TypeScript vs JavaScript code generation tasks.

## Quick Start

### Prerequisites

- Node.js 18+ installed
- **Either:**
  - API keys for LLM providers (OpenAI, Anthropic, Gemini)
  - **OR** Ollama installed with models (local, free, no API keys needed!)

### Installation

```bash
# Install dependencies
npm install

# Optional: Install TypeScript execution support
npm install -D tsx
```

### Setup API Keys (Cloud) or Ollama (Local)

**Option A: Cloud APIs**
```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GEMINI_API_KEY="..."
```

**Option B: Local Ollama (Recommended - Free!)**
```bash
# Check Ollama is running
ollama list

# No API keys needed!
```

### Run Your First Benchmark

```bash
# Quick smoke test with local Ollama
node index.js --task fibonacci --variant typescript --provider ollama-gemma3-4b-it-qat

# Or with cloud API
node index.js --task fibonacci --variant typescript --provider openai-gpt4

# List all available tasks
node index.js --list-tasks

# Run all simple tasks (compares TS vs JS vs JS+JSDoc)
node index.js --category simple
```

## Features

- **Multi-Variant Testing**: Compare TypeScript, JavaScript, and JavaScript+JSDoc
- **Multiple Providers**: OpenAI, Anthropic, Gemini, and local Ollama models
- **Comprehensive Tasks**: Simple algorithms, bug finding, full projects, UI components
- **Detailed Evaluation**: Accuracy, performance, code quality, completeness metrics
- **Rich Reports**: Markdown summaries and interactive HTML dashboards

## Available Providers

### Cloud Providers
- **OpenAI**: GPT-4, GPT-3.5
- **Anthropic**: Claude
- **Google**: Gemini Pro, Gemini Flash

### Local Ollama Models (Free!)
- **Qwen Coder**: `ollama-qwen3-coder-30b`
- **GPT-OSS**: `ollama-gpt-oss-120b`, `ollama-gpt-oss-20b`
- **DeepSeek**: `ollama-deepseek-r1-32b`
- **Gemma**: `ollama-gemma3-4b-it-qat`, `ollama-gemma3-1b-it-qat`

## Usage Examples

### Test Specific Provider
```bash
# Cloud provider
node index.js --provider openai-gpt4

# Local Ollama
node index.js --provider ollama-qwen3-coder-30b
```

### Compare Language Variants
```bash
# Run simple category across all variants
node index.js --category simple

# Test specific variant only
node index.js --variant typescript
node index.js --variant javascript
node index.js --variant javascript-jsdoc
```

### Run Specific Task
```bash
node index.js --task fibonacci
node index.js --task async-fetch
node index.js --task todo-app
```

### Multiple Runs for Statistical Analysis
```bash
# Run each benchmark 5 times
node index.js --category simple --runs 5
```

### Custom Timeout
```bash
# Set 2 minute timeout for complex tasks
node index.js --category full-projects --timeout 120000
```

### Dry Run (No API Calls)
```bash
# Test with mock responses
node index.js --dry-run
```

## Task Categories

### 1. Simple Tasks
Basic coding challenges: algorithms, data structures, utility functions

**Examples**: fibonacci, array-filter, class-person, async-fetch

### 2. Bug Finding
Identify and fix bugs in existing code

**Examples**: async-race-condition, type-coercion

### 3. Needle in Haystack
Find specific issues or patterns in large codebases

**Examples**: find-config-bug

### 4. Full Projects
Complete, functional applications with identical behavior across all variants

**Examples**: todo-app, weather-app, color-palette-generator

### 5. Web Components
Build interactive UI components

**Examples**: counter-component, color-picker-advanced, form-validation

### 6. Large Projects
Analyze and compare implementations of complex features

**Examples**: code-review-comparison

## Evaluation Criteria

Each benchmark is scored on:

1. **Accuracy (40%)**: Does it work correctly?
   - Test cases pass
   - Correct output
   - No errors

2. **Performance (20%)**: Efficiency
   - Token usage
   - Response time
   - Code efficiency

3. **Code Quality (20%)**: Maintainability
   - Proper indentation
   - Descriptive naming
   - Comments/documentation
   - Error handling

4. **Completeness (20%)**: Thoroughness
   - All requirements met
   - Edge cases handled
   - Comprehensive implementation

## Reports

After running benchmarks, reports are generated in `./reports/`:

- **summary.md**: Overall statistics by variant/provider/category
- **comparison.md**: Direct comparison matrix
- **detailed.md**: Individual task results
- **dashboard.html**: Interactive visualizations

View the dashboard:
```bash
open reports/dashboard.html
```

## Creating Custom Tasks

Tasks are JSON files in the `tasks/` directory:

```json
{
  "name": "my-task",
  "description": "Brief description",
  "category": "simple",
  "difficulty": "easy",
  "variants": {
    "typescript": "TypeScript-specific prompt...",
    "javascript": "JavaScript-specific prompt...",
    "javascript-jsdoc": "JavaScript with JSDoc prompt..."
  },
  "testCases": [
    { "test": "console.assert(myFunction(5) === 10);" }
  ],
  "requirements": ["function", "export", "async"]
}
```

Place in appropriate category folder:
- `tasks/simple/`
- `tasks/bug-finding/`
- `tasks/needle-in-haystack/`
- `tasks/full-projects/`
- `tasks/web-components/`
- `tasks/large-projects/`

## Configuration

Edit `config.js` to customize:

- **Providers**: Which LLMs to test
- **Variants**: Which language variants to include
- **Categories**: Which task categories to enable
- **Evaluation Weights**: Adjust scoring criteria
- **Timeouts**: Set per-category limits
- **Output**: Results and reports directories

## Key Insights

This benchmark helps answer:

1. **Type Safety Impact**: Does TypeScript help LLMs produce better code?
2. **JSDoc Effectiveness**: Can JSDoc provide similar benefits to TypeScript?
3. **Provider Comparison**: Which LLMs excel at JavaScript/TypeScript?
4. **Task Complexity**: How do LLMs handle simple vs complex tasks?
5. **Code Quality**: Do types improve LLM-generated code quality?

## Best Practices

1. **Start Small**: Test with one task first
2. **Use Local Models**: Try Ollama to avoid API costs
3. **Run Multiple Times**: Use `--runs 5` for statistical validity
4. **Monitor Costs**: Track API usage for cloud providers
5. **Review Results**: Manually verify some outputs

## Troubleshooting

### No API Keys
Use local Ollama or dry-run mode:
```bash
node index.js --dry-run
```

### Timeout Issues
Increase timeout for complex tasks:
```bash
node index.js --timeout 180000  # 3 minutes
```

### TypeScript Tasks Failing
Install tsx:
```bash
npm install -D tsx
```

### Ollama Not Found
Install Ollama from https://ollama.ai and pull models:
```bash
ollama pull qwen2.5-coder
ollama pull gemma3
```

## Command Reference

```bash
# Core options
--category <name>     Run specific category
--task <name>         Run specific task
--provider <name>     Use specific provider
--variant <name>      Test specific variant
--runs <n>            Number of runs per test
--timeout <ms>        Timeout per test
--dry-run            Use mock responses
--list-tasks         Show all available tasks
--help               Show help
```

## Architecture

```
dream/
├── index.js                  # Main entry point
├── config.js                 # Configuration
├── runner/
│   ├── benchmark-runner.js   # Core benchmark logic
│   ├── llm-client.js         # LLM API client
│   └── mock-llm-client.js    # Mock for testing
├── evaluator/
│   └── evaluator.js          # Code evaluation
├── reports/
│   └── report-generator.js   # Report generation
├── tasks/                    # Benchmark tasks
│   ├── simple/
│   ├── bug-finding/
│   ├── full-projects/
│   └── ...
├── results/                  # Generated results
└── reports/                  # Generated reports
```

## Contributing

To add new tasks:

1. Create JSON file in appropriate category folder
2. Include all three variants (TypeScript, JavaScript, JS+JSDoc)
3. Make prompts as similar as possible across variants
4. Add test cases when applicable
5. Document expected behavior

## API Keys Setup

Get API keys from:
- **OpenAI**: https://platform.openai.com/api-keys
- **Anthropic**: https://console.anthropic.com/
- **Gemini**: https://makersuite.google.com/app/apikey
- **Ollama**: No API key needed (local)

## License

MIT License - See LICENSE file for details

---

**Quick Commands Cheat Sheet:**

```bash
# Fastest way to test
node index.js --task fibonacci --variant typescript --provider ollama-gemma3-1b-it-qat

# Compare TS vs JS vs JS+JSDoc
node index.js --category simple --provider ollama-qwen3-coder-30b

# Full comparison across providers
node index.js --task fibonacci --runs 3

# List everything
node index.js --list-tasks
```

**Made for developers who want to understand how LLMs handle TypeScript vs JavaScript.**
