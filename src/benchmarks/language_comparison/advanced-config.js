/**
 * Advanced Benchmark Configuration
 * Comprehensive testing with temperature variations, multiple runs, and statistical analysis
 */

export const AdvancedBenchmarkConfig = {
  // Test configuration
  testing: {
    // Run each test multiple times for statistical significance
    runsPerConfig: 5,

    // Temperature variations to test (0.0 = deterministic, 1.0 = creative)
    temperatures: [0.0, 0.2, 0.7, 1.0],

    // Calculate variance and standard deviation
    statisticalAnalysis: true,

    // Fail fast or continue on errors
    continueOnError: true
  },

  // LLM Providers
  providers: [
    {
      name: 'ollama-gpt-oss-20b',
      model: 'gpt-oss:20b',
      baseUrl: process.env.OLLAMA_BASE_URL || 'http://localhost:11434'
    },
    {
      name: 'ollama-gemma3-27b',
      model: 'gemma3:27b-it-qat',
      baseUrl: process.env.OLLAMA_BASE_URL || 'http://localhost:11434'
    }
  ].filter(p => p.apiKey || p.baseUrl),

  // Language variants to test
  variants: [
    'typescript',
    'javascript',
    'javascript-jsdoc'
  ],

  // Task categories with enhanced evaluation
  categories: {
    'simple': {
      enabled: true,
      weight: 1.0,
      timeout: 60000,  // Increased for multiple runs
      evaluationType: 'unit-test'  // Run actual unit tests
    },
    'web-components': {
      enabled: true,
      weight: 1.5,
      timeout: 120000,
      evaluationType: 'playwright'  // Use Playwright for E2E testing
    },
    'ui-components': {
      enabled: true,
      weight: 1.5,
      timeout: 120000,
      evaluationType: 'playwright-visual'  // Include visual regression
    },
    'full-projects': {
      enabled: true,
      weight: 2.0,
      timeout: 180000,
      evaluationType: 'integration'  // Full integration tests
    }
  },

  // Enhanced evaluation criteria
  evaluation: {
    // Core criteria
    accuracy: 0.40,      // Correctness (40%)
    performance: 0.20,   // Efficiency (20%)
    codeQuality: 0.20,   // Best practices (20%)
    completeness: 0.20,  // Thoroughness (20%)

    // Accuracy scoring
    accuracyScoring: {
      // Weight test cases by complexity
      testCaseWeights: true,

      // Partial credit for close answers
      partialCredit: true,

      // Allow small numerical deviations
      numericalTolerance: 0.0001,

      // Check output format correctness
      formatValidation: true
    },

    // Consistency scoring (across multiple runs)
    consistencyScoring: {
      enabled: true,

      // Penalize high variance across runs
      variancePenalty: 0.1,

      // Reward deterministic outputs
      determinismBonus: 0.05
    }
  },

  // Playwright configuration for UI testing
  playwright: {
    enabled: true,

    browsers: ['chromium'],  // Can add 'firefox', 'webkit'

    // Visual regression testing
    visualRegression: {
      enabled: true,
      threshold: 0.05,  // 5% pixel difference tolerance
      compareScreenshots: true
    },

    // Functional testing
    functional: {
      // Test user interactions
      testInteractions: true,

      // Verify DOM structure
      validateDOM: true,

      // Check accessibility
      a11yChecks: true
    },

    // Performance metrics
    performance: {
      // Measure load time
      loadTime: true,

      // Check for console errors
      noConsoleErrors: true,

      // Memory leaks
      memoryLeaks: false  // Experimental
    }
  },

  // Output settings
  output: {
    resultsDir: 'benchmark/results',
    reportsDir: 'benchmark/reports',
    screenshotsDir: 'benchmark/screenshots',
    saveResponses: true,
    verbose: true,

    // Statistical reporting
    includeStatistics: true,
    generateConfidenceIntervals: true
  }
};
