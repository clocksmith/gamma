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

  // DECOUPLED DIMENSIONS FOR FLEXIBLE BENCHMARKING
  // Language, prompt level, framework, and code style are now separate
  // This allows independent control and better analysis

  // Core languages to test
  languages: ['javascript', 'typescript', 'javascript-jsdoc'],

  // Prompt quality levels (instruction clarity)
  promptLevels: ['novice', 'beginner', 'intermediate', 'advanced', 'expert'],

  // Frameworks (optional, task-specific)
  frameworks: ['vanilla', 'react', 'node'],

  // Code style preferences (optional)
  codeStyles: ['default', 'no-comments', 'documented', 'inline-comments'],

  // Default temperature for LLM sampling (1.0 for good variation, 0.0 for deterministic)
  temperature: 1.0,

  // Legacy variants array (backward compatibility)
  // These are auto-generated from combinations or can be specified manually
  variants: [
    // Default variants (use 'expert' level prompts)
    'javascript',
    'typescript',
    'javascript-jsdoc',

    // Legacy code style variants (backward compatibility)
    'javascript-no-comments',
    'javascript-inline-comments',
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

  // Task categories with bias levels and proper mappings
  // biasLevel: 'deterministic' = fully deterministic tests with no bias
  //            'low-bias' = non-deterministic with minimal bias
  //            'medium-bias' = non-deterministic with moderate bias
  //            'high-bias' = subjective evaluation with higher bias
  categories: {
    '1-foundations': {
      enabled: true,
      weight: 1.0,
      timeout: 60000, // 60 seconds
      biasLevel: 'deterministic',
      description: 'Basic algorithms and data structures'
    },
    '2-scripting-and-automation': {
      enabled: true,
      weight: 1.5,
      timeout: 60000, // 1 minute
      biasLevel: 'deterministic',
      description: 'CLI tools and file operations'
    },
    '3-server-side-development': {
      enabled: true,
      weight: 2.0,
      timeout: 120000, // 2 minutes
      biasLevel: 'low-bias',
      description: 'API and backend services'
    },
    '4-web-fundamentals': {
      enabled: true,
      weight: 2.5,
      timeout: 180000, // 3 minutes
      biasLevel: 'low-bias',
      description: 'DOM manipulation and web APIs'
    },
    '5-react-component-library': {
      enabled: true,
      weight: 2.5,
      timeout: 180000, // 3 minutes
      biasLevel: 'medium-bias',
      description: 'React UI components',
      aliases: ['ui-components']
    },
    '6-full-stack-applications': {
      enabled: true,
      weight: 3.0,
      timeout: 300000, // 5 minutes
      biasLevel: 'medium-bias',
      description: 'Complete applications',
      aliases: ['full-projects']
    },
    '7-debugging-and-maintenance': {
      enabled: true,
      weight: 2.0,
      timeout: 90000, // 1.5 minutes
      biasLevel: 'high-bias',
      description: 'Bug finding and code analysis',
      aliases: ['bug-finding', 'needle-in-haystack', 'large-projects']
    }
  },

  // Evaluation criteria with all metrics (camelCase naming)
  evaluation: {
    // Core metrics (weights must sum to 1.0)
    accuracy: {
      weight: 0.30,
      description: 'Correctness of the solution',
      includeF1: true,
      includePrecisionRecall: true
    },
    performance: {
      weight: 0.20,
      description: 'Time taken and efficiency',
      includeTokenEfficiency: true,
      includeRuntimeMetrics: true
    },
    codeQuality: {
      weight: 0.25,
      description: 'Code style, readability, best practices',
      includeComplexityMetrics: true,
      includeMaintainability: true
    },
    completeness: {
      weight: 0.15,
      description: 'How complete the solution is'
    },
    complexity: {
      weight: 0.10,
      description: 'Code complexity and maintainability',
      includeCyclomaticComplexity: true,
      includeHalsteadMetrics: true,
      includeMaintainabilityIndex: true
    }
  },

  // All available metrics that should be tracked and reported independently
  availableMetrics: [
    'accuracy',
    'f1Score',
    'precision',
    'recall',
    'performance',
    'tokenEfficiency',
    'runtimePerformance',
    'codeQuality',
    'completeness',
    'cyclomaticComplexity',
    'halsteadDifficulty',
    'halsteadVolume',
    'halsteadEffort',
    'maintainabilityIndex',
    'maxNestingDepth',
    'avgLineLength',
    'linesOfCode',
    'editSimilarity',
    'astSimilarity'
  ],

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
  runs: 1,

  // Helper function to resolve category aliases
  resolveCategory(categoryName) {
    // Direct match
    if (this.categories[categoryName]) {
      return categoryName;
    }
    // Check aliases
    for (const [key, config] of Object.entries(this.categories)) {
      if (config.aliases && config.aliases.includes(categoryName)) {
        return key;
      }
    }
    return categoryName; // Return original if no match found
  },

  // Get all categories grouped by bias level
  getCategoriesByBiasLevel() {
    const grouped = {
      deterministic: [],
      'low-bias': [],
      'medium-bias': [],
      'high-bias': []
    };
    for (const [key, config] of Object.entries(this.categories)) {
      if (config.biasLevel && grouped[config.biasLevel]) {
        grouped[config.biasLevel].push({ name: key, ...config });
      }
    }
    return grouped;
  },

  // Helper function to generate prompt level variants
  // Returns all combinations of languages and prompt levels
  getPromptLevelVariants(options = {}) {
    const {
      languages = ['typescript', 'javascript', 'javascript-jsdoc'],
      levels = ['novice', 'beginner', 'intermediate', 'advanced', 'expert']
    } = options;

    const variants = [];

    for (const language of languages) {
      for (const level of levels) {
        variants.push(`${language}-${level}`);
      }
    }

    return variants;
  },

  // Helper function to get all prompt level variants for a specific level
  // Useful for testing a specific prompt quality across all languages
  getVariantsForLevel(level) {
    const languages = ['typescript', 'javascript', 'javascript-jsdoc'];
    return languages.map(lang => `${lang}-${level}`);
  },

  // Helper function to get all prompt level variants for a specific language
  // Useful for testing all prompt qualities for a specific language
  getVariantsForLanguage(language) {
    const levels = ['novice', 'beginner', 'intermediate', 'advanced', 'expert'];
    return levels.map(level => `${language}-${level}`);
  },

  /**
   * Generate variant combinations from separate dimensions
   * @param {Object} options - Options for generating combinations
   * @returns {Array} Array of variant configuration objects
   */
  generateCombinations(options = {}) {
    const {
      languages = this.languages,
      promptLevels = ['expert'], // Default to expert only
      frameworks = [],
      codeStyles = []
    } = options;

    const combinations = [];

    for (const language of languages) {
      for (const promptLevel of promptLevels) {
        // Base combination
        const base = {
          language,
          promptLevel,
          variantString: `${language}-${promptLevel}`
        };

        if (frameworks.length === 0 && codeStyles.length === 0) {
          combinations.push(base);
        } else {
          // Add framework variations
          for (const framework of (frameworks.length > 0 ? frameworks : [''])) {
            for (const codeStyle of (codeStyles.length > 0 ? codeStyles : [''])) {
              const variant = { ...base };
              if (framework) variant.framework = framework;
              if (codeStyle) variant.codeStyle = codeStyle;

              // Update variant string
              const parts = [language, promptLevel];
              if (framework) parts.push(framework);
              if (codeStyle) parts.push(codeStyle);
              variant.variantString = parts.join('-');

              combinations.push(variant);
            }
          }
        }
      }
    }

    return combinations;
  },

  /**
   * Parse a legacy variant string into separate dimensions
   * E.g., "typescript-expert" → {language: 'typescript', promptLevel: 'expert'}
   * E.g., "javascript-react-novice" → {language: 'javascript', framework: 'react', promptLevel: 'novice'}
   */
  parseVariantString(variantString) {
    if (!variantString) return null;

    const parts = variantString.split('-');
    const result = {
      variantString,
      language: null,
      promptLevel: null,
      framework: null,
      codeStyle: null
    };

    // Identify prompt level (always last if present)
    const lastPart = parts[parts.length - 1];
    if (this.promptLevels.includes(lastPart)) {
      result.promptLevel = lastPart;
      parts.pop();
    } else {
      // Default to expert if no level specified
      result.promptLevel = 'expert';
    }

    // Identify language (first part or combination)
    if (parts[0] === 'javascript' && parts[1] === 'jsdoc') {
      result.language = 'javascript-jsdoc';
      parts.splice(0, 2);
    } else if (this.languages.includes(parts[0])) {
      result.language = parts[0];
      parts.shift();
    } else if (parts[0] === 'react' && this.languages.includes('typescript')) {
      // Special case: react-typescript-...
      result.language = 'typescript';
      result.framework = 'react';
      parts.shift();
    }

    // Remaining parts could be framework or code style
    for (const part of parts) {
      if (this.frameworks.includes(part)) {
        result.framework = part;
      } else if (this.codeStyles.includes(part) || ['no-comments', 'inline-comments', 'tsdoc', 'jsdoc', 'untested', 'tested', 'vanilla-web'].includes(part)) {
        result.codeStyle = part;
      }
    }

    return result;
  },

  /**
   * Convert dimension object back to variant string
   */
  toVariantString(dimensions) {
    const parts = [];
    if (dimensions.language) parts.push(dimensions.language);
    if (dimensions.framework) parts.push(dimensions.framework);
    if (dimensions.promptLevel) parts.push(dimensions.promptLevel);
    if (dimensions.codeStyle) parts.push(dimensions.codeStyle);
    return parts.join('-');
  }
};
