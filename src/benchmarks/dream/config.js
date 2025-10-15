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
    }
  ],

  // Language variants to test
  variants: [
    'typescript',
    'javascript',
    'javascript-jsdoc',
    'javascript-vanilla-web',      // JavaScript with vanilla Web APIs, HTML, CSS
    'javascript-vanilla-web-jsdoc', // Same as above with JSDoc
    'typescript-vanilla-web',      // TypeScript vanilla as possible with Web APIs
    'typescript-react'             // TypeScript React without too many deps
  ],

  // Task categories
  categories: {
    simple: {
      enabled: true,
      weight: 1.0,
      timeout: 30000 // 30 seconds
    },
    'large-projects': {
      enabled: true,
      weight: 2.0,
      timeout: 120000 // 2 minutes
    },
    'needle-in-haystack': {
      enabled: true,
      weight: 1.5,
      timeout: 60000 // 1 minute
    },
    'bug-finding': {
      enabled: true,
      weight: 2.0,
      timeout: 90000 // 1.5 minutes
    },
    'full-projects': {
      enabled: true,
      weight: 3.0,
      timeout: 300000 // 5 minutes
    },
    'web-components': {
      enabled: true,
      weight: 2.5,
      timeout: 180000 // 3 minutes
    },
    'ui-components': {
      enabled: true,
      weight: 2.5,
      timeout: 180000 // 3 minutes
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
    resultsDir: './benchmark/results',
    reportsDir: './benchmark/reports',
    verbose: true,
    saveResponses: true
  }
};
