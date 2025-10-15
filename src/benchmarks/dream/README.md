# LLM TypeScript/JavaScript Benchmark Suite

A comprehensive benchmarking system for evaluating Large Language Models (LLMs) on TypeScript and JavaScript tasks, including JavaScript with JSDoc annotations.

## Features

- **Multiple Language Variants**: Test LLMs on TypeScript, JavaScript, and JavaScript with JSDoc
- **Comprehensive Task Categories**:
  - Simple coding tasks
  - Large project reviews
  - Needle-in-haystack problems
  - Bug finding challenges
  - Full project implementations
- **Multi-Provider Support**: Works with OpenAI, Anthropic, Google Gemini, and local Ollama models
- **Detailed Evaluation**: Measures accuracy, performance, code quality, and completeness
- **Rich Reporting**: Generates markdown reports and interactive HTML dashboards

## Project Structure

```
benchmark/
├── config.js                 # Benchmark configuration
├── index.js                  # Main entry point
├── runner/
│   ├── benchmark-runner.js   # Orchestrates benchmark execution
│   └── llm-client.js        # LLM API client
├── evaluator/
│   └── evaluator.js         # Evaluates LLM responses
├── reports/
│   └── report-generator.js  # Generates reports and visualizations
├── tasks/
│   ├── simple/              # Simple coding tasks
│   ├── large-projects/      # Large project review tasks
│   ├── needle-in-haystack/  # Finding specific issues in large codebases
│   ├── bug-finding/         # Identifying and fixing bugs
│   └── full-projects/       # Complete project implementations
├── results/                 # Raw benchmark results (JSON)
└── reports/                 # Generated reports (MD, HTML)
```

## Setup

### 1. Install Dependencies

```bash
npm install
# or
npm install tsx chart.js  # For TypeScript execution and charts
```

### 2. Configure API Keys

Set environment variables for the LLM providers you want to test:

```bash
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
export GEMINI_API_KEY="your-gemini-key"
export OLLAMA_BASE_URL="http://localhost:11434"  # Optional, defaults to localhost
```

Or create a `.env` file:

```
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
GEMINI_API_KEY=your-gemini-key
OLLAMA_BASE_URL=http://localhost:11434
```

**For Ollama (Local Models):**
1. Install Ollama from https://ollama.ai
2. Pull models: `ollama pull llama3` or `ollama pull codellama`
3. Ensure Ollama is running (it starts automatically after installation)
4. No API key needed - it runs locally!

### 3. Configure Benchmark Settings

Edit `benchmark/config.js` to customize:
- Which providers to test
- Which language variants to include
- Which task categories to run
- Evaluation criteria weights
- Timeout settings

## Usage

### Run All Benchmarks

```bash
node benchmark/index.js
```

### Run Specific Categories

```bash
# Run only simple tasks
node benchmark/index.js --category simple

# Run only bug-finding tasks
node benchmark/index.js --category bug-finding
```

### Run Specific Language Variants

```bash
# Test only TypeScript
node benchmark/index.js --variant typescript

# Test only JavaScript with JSDoc
node benchmark/index.js --variant javascript-jsdoc
```

### Run Specific Providers

```bash
# Test only GPT-4
node benchmark/index.js --provider openai-gpt4

# Test Claude only with TypeScript
node benchmark/index.js --provider anthropic-claude --variant typescript

# Test Gemini Pro
node benchmark/index.js --provider google-gemini-pro

# Test local Ollama model
node benchmark/index.js --provider ollama-llama3
```

### Run Specific Tasks

```bash
node benchmark/index.js --task fibonacci
```

### List Available Tasks

```bash
node benchmark/index.js --list-tasks
```

## Task Categories

### 1. Simple Tasks

Basic coding challenges like implementing algorithms, data structures, and utility functions.

Examples:
- Fibonacci sequence
- Array filtering
- Class definitions
- Async operations

### 2. Large Project Reviews

Analyzing and comparing implementations of the same feature across different language variants.

Focus areas:
- Type safety comparison
- Maintainability assessment
- Code quality evaluation
- Developer experience

### 3. Needle in Haystack

Finding specific issues, bugs, or patterns in large codebases.

Tests:
- Configuration bugs
- Hidden type errors
- Subtle logical errors
- Performance bottlenecks

### 4. Bug Finding

Identifying and fixing bugs in existing code.

Examples:
- Race conditions
- Memory leaks
- Type errors
- Logic bugs

### 5. Full Project Implementations

Building complete, functional applications with identical behavior across all variants.

Requirements:
- Same functionality
- Same API surface
- Same behavior
- Production-ready code

## Evaluation Criteria

Each benchmark is evaluated on four criteria:

1. **Accuracy (40%)**: Correctness of the solution
   - Does it work as expected?
   - Do test cases pass?
   - Is the output correct?

2. **Performance (20%)**: Efficiency and speed
   - Token usage
   - Response time
   - Code efficiency

3. **Code Quality (20%)**: Best practices and maintainability
   - Proper indentation
   - Descriptive naming
   - Comments and documentation
   - Error handling

4. **Completeness (20%)**: How thorough the solution is
   - All requirements met
   - Edge cases handled
   - Comprehensive implementation

## Reports

After running benchmarks, several reports are generated:

### 1. Summary Report (`reports/summary.md`)
- Overall statistics
- Performance by variant
- Performance by provider
- Performance by category

### 2. Comparison Report (`reports/comparison.md`)
- Direct comparison matrix
- Detailed criteria breakdown
- TypeScript vs JavaScript vs JSDoc comparison

### 3. Detailed Report (`reports/detailed.md`)
- Individual task results
- Per-task breakdowns
- Success/failure details

### 4. HTML Dashboard (`reports/dashboard.html`)
- Interactive visualizations
- Charts and graphs
- Real-time statistics

Open the dashboard in your browser:
```bash
open benchmark/reports/dashboard.html
```

## Creating Custom Tasks

Tasks are defined as JSON files in the `tasks/` directory. Here's the structure:

```json
{
  "name": "task-name",
  "description": "Brief description",
  "category": "simple",
  "difficulty": "easy|medium|hard",
  "variants": {
    "typescript": "Prompt for TypeScript version...",
    "javascript": "Prompt for JavaScript version...",
    "javascript-jsdoc": "Prompt for JavaScript with JSDoc..."
  },
  "testCases": [
    {
      "test": "console.assert(...);"
    }
  ],
  "requirements": ["keyword1", "keyword2"],
  "expectedOutput": "optional expected output",
  "bugLocation": "optional for bug-finding tasks",
  "needleText": "optional for needle-in-haystack",
  "needleLocation": "optional location info"
}
```

Place your JSON file in the appropriate category folder:
- `tasks/simple/` - Simple coding tasks
- `tasks/large-projects/` - Large project reviews
- `tasks/needle-in-haystack/` - Finding issues in code
- `tasks/bug-finding/` - Bug identification tasks
- `tasks/full-projects/` - Complete implementations

## Key Insights

This benchmark suite helps answer important questions:

1. **Type Safety Impact**: How much does TypeScript's type system help LLMs produce correct code?

2. **JSDoc Effectiveness**: Can JSDoc annotations provide similar benefits to TypeScript for LLMs?

3. **Provider Comparison**: Which LLM providers perform best on JavaScript/TypeScript tasks?

4. **Task Complexity**: How do LLMs handle simple vs. complex tasks across variants?

5. **Code Quality**: Do LLMs produce better quality code with type information?

## Best Practices

1. **Run Multiple Times**: Run benchmarks multiple times to account for variability
2. **Use Consistent Prompts**: Keep prompts as similar as possible across variants
3. **Set Appropriate Timeouts**: Adjust timeouts based on task complexity
4. **Monitor Costs**: Be aware of API costs when running extensive benchmarks
5. **Review Results**: Manually review some responses to validate automated scoring

## Contributing

To add new tasks:

1. Create a JSON file in the appropriate category folder
2. Include all three variants (TypeScript, JavaScript, JavaScript+JSDoc)
3. Make implementations as similar as possible
4. Add test cases if applicable
5. Document expected behavior

## License

MIT License - See LICENSE file for details

## Support

For issues or questions:
- Open an issue on GitHub
- Check the documentation
- Review example tasks for guidance

---

**Note**: This benchmark suite requires API keys for LLM providers. Costs may vary based on usage. Always monitor your API usage and set appropriate limits.
