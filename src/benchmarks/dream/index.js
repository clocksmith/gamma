#!/usr/bin/env node

/**
 * LLM TypeScript/JavaScript Benchmark Suite
 * Main entry point for running benchmarks
 */

import { BenchmarkRunner } from './runner/benchmark-runner.js';
import { BenchmarkConfig } from './config.js';

async function main() {
  const args = process.argv.slice(2);

  // Parse command line arguments
  const filters = {
    providers: [],
    variants: [],
  };
  let dryRun = false;
  let runs = null;

  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case '--category':
        filters.category = args[++i];
        break;
      case '--task':
        filters.taskName = args[++i];
        break;
      case '--provider':
        filters.providers.push(args[++i]);
        break;
      case '--variant':
        filters.variants.push(args[++i]);
        break;
      case '--runs':
        runs = parseInt(args[++i], 10);
        if (isNaN(runs) || runs < 1) {
          console.error('Error: --runs must be a positive integer.');
          process.exit(1);
        }
        break;
      case '--timeout':
        filters.timeout = parseInt(args[++i], 10);
        if (isNaN(filters.timeout) || filters.timeout < 1) {
          console.error('Error: --timeout must be a positive integer in milliseconds.');
          process.exit(1);
        }
        break;
      case '--dry-run':
      case '--mock':
        dryRun = true;
        break;
      case '--help':
        printHelp();
        process.exit(0);
      case '--list-tasks':
        await listTasks();
        process.exit(0);
      default:
        console.error(`Unknown argument: ${args[i]}`);
        printHelp();
        process.exit(1);
    }
  }

  // Check for API keys unless in dry-run mode
  if (!dryRun) {
    const hasApiKeys = BenchmarkConfig.providers.some(p => p.apiKey || p.baseUrl);
    if (!hasApiKeys) {
      console.warn('⚠️  Warning: No API keys or Ollama installation found.');
      console.warn('   Set OPENAI_API_KEY, ANTHROPIC_API_KEY, or GEMINI_API_KEY in .env file');
      console.warn('   Or install Ollama locally from https://ollama.ai');
      console.warn('   Or use --dry-run to test with mock responses\n');
      console.log('Switching to dry-run mode with mock LLM responses...\n');
      dryRun = true;
    }
  }

  const config = { ...BenchmarkConfig };
  if (dryRun) {
    config.dryRun = true;
  }
  if (runs) {
    config.runs = runs;
  }

  const runner = new BenchmarkRunner(config);

  try {
    if (dryRun) {
      console.log('🔬 DRY RUN MODE - Using mock LLM responses\n');
    }

    const hasFilters = filters.providers.length > 0 || filters.variants.length > 0 || filters.category || filters.taskName;

    if (hasFilters) {
      console.log('Running filtered benchmarks...');
      await runner.run(filters);
    } else {
      console.log('Running all benchmarks...');
      await runner.runAll();
    }
  } catch (error) {
    console.error('Benchmark failed:', error);
    console.error(error.stack);
    process.exit(1);
  }
}

function printHelp() {
  console.log(`
LLM TypeScript/JavaScript Benchmark Suite

Usage:
  node benchmark/index.js [options]

Options:
  --category <name>    Run only tests in specified category
                       (simple, large-projects, needle-in-haystack, bug-finding,
                        full-projects, web-components, ui-components)
  --task <name>        Run only the specified task
  --provider <name>    Run only with specified provider
  --variant <name>     Run only specified variant
                       (typescript, javascript, javascript-jsdoc,
                        javascript-vanilla-web, javascript-vanilla-web-jsdoc,
                        typescript-vanilla-web, typescript-react)
  --runs <number>      Run each benchmark <number> times (e.g., --runs 10)
  --timeout <ms>       Set a custom timeout in milliseconds for each task (e.g., --timeout 120000)
  --dry-run, --mock    Run with mock LLM responses (no API keys needed)
  --list-tasks         List all available tasks
  --help               Show this help message

Examples:
  node benchmark/index.js
  node benchmark/index.js --category simple
  node benchmark/index.js --variant typescript
  node benchmark/index.js --provider openai-gpt4 --variant typescript
  node benchmark/index.js --task fibonacci

Environment Variables:
  OPENAI_API_KEY       OpenAI API key
  ANTHROPIC_API_KEY    Anthropic API key
  GEMINI_API_KEY       Google Gemini API key
  OLLAMA_BASE_URL      Ollama base URL (default: http://localhost:11434)
`);
}

async function listTasks() {
  const runner = new BenchmarkRunner(BenchmarkConfig);
  const tasks = await runner.loadTasks();

  console.log('\nAvailable Tasks:\n');

  const categories = [...new Set(tasks.map(t => t.category))];
  for (const category of categories) {
    console.log(`\n${category}:`);
    const categoryTasks = tasks.filter(t => t.category === category);
    for (const task of categoryTasks) {
      console.log(`  - ${task.name}: ${task.description}`);
    }
  }

  console.log(`\nTotal: ${tasks.length} tasks\n`);
}

// Run if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(console.error);
}

export { BenchmarkRunner, BenchmarkConfig };
