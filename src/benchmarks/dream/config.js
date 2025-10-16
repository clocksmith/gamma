/**
 * Benchmark Configuration
 * Configure which tests to run and evaluation criteria
 */

export const BenchmarkConfig = {
  // LLM Providers to test
  providers: [
    {
      name: 'openai-gpt4',
      apiKey: process.env.OPENAI_API_KEY,
      model: 'gpt-4-turbo-preview'
    },
    {
      name: 'anthropic-claude',
      apiKey: process.env.ANTHROPIC_API_KEY,
      model: 'claude-3-opus-20240229'
    },
    {
      name: 'openai-gpt35',
      apiKey: process.env.OPENAI_API_KEY,
      model: 'gpt-3.5-turbo'
    },
    {
      name: 'gemini-pro',
      apiKey: process.env.GEMINI_API_KEY,
      model: 'gemini-1.5-pro-latest'
    },
    {
      name: 'gemini-flash',
      apiKey: process.env.GEMINI_API_KEY,
      model: 'gemini-1.5-flash-latest'
    },
    // Ollama models (local)
    {
      name: 'ollama-qwen3-coder-30b',
      baseUrl: process.env.OLLAMA_BASE_URL || 'http://localhost:11434',
      model: 'qwen3-coder:30b'
    },
    {
      name: 'ollama-qwen3-30b',
      baseUrl: process.env.OLLAMA_BASE_URL || 'http://localhost:11434',
      model: 'qwen3:30b'
    },
    {
      name: 'ollama-gpt-oss-120b',
      baseUrl: process.env.OLLAMA_BASE_URL || 'http://localhost:11434',
      model: 'gpt-oss:120b'
    },
    {
      name: 'ollama-gpt-oss-20b',
      baseUrl: process.env.OLLAMA_BASE_URL || 'http://localhost:11434',
      model: 'gpt-oss:20b'
    },
    {
      name: 'ollama-deepseek-r1-32b',
      baseUrl: process.env.OLLAMA_BASE_URL || 'http://localhost:11434',
      model: 'deepseek-r1:32b'
    },
    {
      name: 'ollama-gemma3-27b-it-qat',
      baseUrl: process.env.OLLAMA_BASE_URL || 'http://localhost:11434',
      model: 'gemma3:27b-it-qat'
    },
    {
      name: 'ollama-gemma3-4b-it-qat',
      baseUrl: process.env.OLLAMA_BASE_URL || 'http://localhost:11434',
      model: 'gemma3:4b-it-qat'
    },
    {
      name: 'ollama-gemma3-1b-it-qat',
      baseUrl: process.env.OLLAMA_BASE_URL || 'http://localhost:11434',
      model: 'gemma3:1b-it-qat'
    }
  ],

  // Language variants to test
  variants: [
    'javascript',
    'typescript',
    'javascript-no-comments',
    'javascript-inline-comments',
    'javascript-jsdoc',
    'javascript-vanilla-web',
    'javascript-vanilla-web-jsdoc',
    'typescript-no-comments',
    'typescript-inline-comments',
    'typescript-tsdoc',
    'typescript-vanilla-web',
    'typescript-react',
    'typescript-react-no-comments',
    'typescript-react-tsdoc',
    'javascript-untested',
    'javascript-tested',
    'typescript-untested',
    'typescript-tested',
    'react-typescript-untested',
    'react-typescript-tested',
  ],

  // Task categories
  categories: {
    '1-foundations': {
      enabled: true,
      weight: 1.0,
      timeout: 60000 // 60 seconds
    },
    '2-scripting-and-automation': {
      enabled: true,
      weight: 1.5,
      timeout: 60000 // 1 minute
    },
    '3-server-side-development': {
      enabled: true,
      weight: 2.0,
      timeout: 120000 // 2 minutes
    },
    '4-web-fundamentals': {
      enabled: true,
      weight: 2.5,
      timeout: 180000 // 3 minutes
    },
    '5-react-component-library': {
      enabled: true,
      weight: 2.5,
      timeout: 180000 // 3 minutes
    },
    '6-full-stack-applications': {
      enabled: true,
      weight: 3.0,
      timeout: 300000 // 5 minutes
    },
    '7-debugging-and-maintenance': {
      enabled: true,
      weight: 2.0,
      timeout: 90000 // 1.5 minutes
    }
  },

  // Evaluation criteria
  evaluation: {
    accuracy: {
      weight: 0.4,
      description: 'Correctness of the solution'
    },
    performance: {
      weight: 0.2,
      description: 'Time taken and efficiency'
    },
    codeQuality: {
      weight: 0.2,
      description: 'Code style, readability, best practices'
    },
    completeness: {
      weight: 0.2,
      description: 'How complete the solution is'
    }
  },

  // Output settings
  output: {
    resultsDir: './results',
    reportsDir: './reports',
    verbose: true,
    saveResponses: true
  },

  // Directory paths for reports (aliases for compatibility)
  resultsDirectory: './results',
  reportsDirectory: './reports',

  // Default number of runs per benchmark
  runs: 1
};
