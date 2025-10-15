/**
 * Benchmark Presets and Templates
 * Pre-configured benchmark suites for common scenarios
 */

export const BenchmarkPresets = {
  /**
   * Quick validation - Fast smoke test
   */
  quick: {
    name: 'Quick Validation',
    description: 'Fast smoke test for basic functionality',
    categories: ['simple'],
    runs: 1,
    timeout: 30000,
    providers: ['openai-gpt4'],
    variants: ['typescript', 'javascript']
  },

  /**
   * Comprehensive - Full test suite
   */
  comprehensive: {
    name: 'Comprehensive Suite',
    description: 'Complete test coverage across all categories',
    categories: ['simple', 'large-projects', 'needle-in-haystack', 'bug-finding', 'full-projects'],
    runs: 3,
    timeout: 300000,
    providers: ['openai-gpt4', 'anthropic-claude', 'openai-gpt35'],
    variants: ['typescript', 'javascript', 'javascript-jsdoc']
  },

  /**
   * Performance focused - Speed and efficiency
   */
  performance: {
    name: 'Performance Benchmark',
    description: 'Focus on speed and token efficiency',
    categories: ['simple', 'large-projects'],
    runs: 5,
    timeout: 120000,
    providers: ['openai-gpt4', 'openai-gpt35'],
    variants: ['typescript', 'javascript'],
    evaluationWeights: {
      accuracy: 0.3,
      performance: 0.5,  // Higher weight on performance
      codeQuality: 0.1,
      completeness: 0.1
    }
  },

  /**
   * Quality focused - Code quality and maintainability
   */
  quality: {
    name: 'Quality Benchmark',
    description: 'Focus on code quality and best practices',
    categories: ['simple', 'full-projects'],
    runs: 3,
    timeout: 180000,
    providers: ['openai-gpt4', 'anthropic-claude'],
    variants: ['typescript', 'javascript-jsdoc'],
    evaluationWeights: {
      accuracy: 0.2,
      performance: 0.1,
      codeQuality: 0.5,  // Higher weight on quality
      completeness: 0.2
    }
  },

  /**
   * Type safety comparison
   */
  typeSafety: {
    name: 'Type Safety Analysis',
    description: 'Compare TypeScript vs JavaScript vs JSDoc',
    categories: ['simple', 'large-projects', 'bug-finding'],
    runs: 3,
    timeout: 120000,
    providers: ['openai-gpt4', 'anthropic-claude'],
    variants: ['typescript', 'javascript', 'javascript-jsdoc']
  },

  /**
   * Provider comparison
   */
  providerComparison: {
    name: 'Provider Comparison',
    description: 'Compare all available LLM providers',
    categories: ['simple'],
    runs: 5,
    timeout: 60000,
    providers: ['openai-gpt4', 'anthropic-claude', 'openai-gpt35', 'google-gemini-pro'],
    variants: ['typescript']
  },

  /**
   * Stress test
   */
  stress: {
    name: 'Stress Test',
    description: 'Test with large, complex tasks',
    categories: ['large-projects', 'full-projects'],
    runs: 3,
    timeout: 600000,  // 10 minutes
    providers: ['openai-gpt4'],
    variants: ['typescript', 'javascript']
  },

  /**
   * Regression test
   */
  regression: {
    name: 'Regression Test',
    description: 'Quick regression check against baseline',
    categories: ['simple', 'bug-finding'],
    runs: 3,
    timeout: 90000,
    providers: ['openai-gpt4'],
    variants: ['typescript', 'javascript'],
    compareWithHistory: true,
    regressionThresholds: {
      score: -5,  // Alert if score drops by 5%
      duration: 20  // Alert if duration increases by 20%
    }
  },

  /**
   * Cost optimization
   */
  costOptimized: {
    name: 'Cost Optimized',
    description: 'Balance cost and performance',
    categories: ['simple', 'large-projects'],
    runs: 1,
    timeout: 60000,
    providers: ['openai-gpt35'],  // Use cheaper models
    variants: ['javascript'],  // Simpler variant
    evaluationWeights: {
      accuracy: 0.4,
      performance: 0.3,
      codeQuality: 0.2,
      completeness: 0.1
    }
  },

  /**
   * Web components focus
   */
  webComponents: {
    name: 'Web Components',
    description: 'Test web component and UI generation',
    categories: ['web-components', 'ui-components'],
    runs: 2,
    timeout: 180000,
    providers: ['openai-gpt4', 'anthropic-claude'],
    variants: ['javascript-vanilla-web', 'javascript-vanilla-web-jsdoc', 'typescript-vanilla-web', 'typescript-react']
  },

  /**
   * CI/CD friendly
   */
  ci: {
    name: 'CI/CD Pipeline',
    description: 'Fast tests suitable for CI/CD',
    categories: ['simple'],
    runs: 1,
    timeout: 45000,
    providers: ['openai-gpt35'],
    variants: ['typescript'],
    failFast: true,
    saveResponses: false
  }
};

export class PresetManager {
  /**
   * Get preset configuration
   */
  static getPreset(presetName) {
    return BenchmarkPresets[presetName] || null;
  }

  /**
   * List all available presets
   */
  static listPresets() {
    return Object.entries(BenchmarkPresets).map(([key, preset]) => ({
      key,
      name: preset.name,
      description: preset.description
    }));
  }

  /**
   * Apply preset to config
   */
  static applyPreset(baseConfig, presetName) {
    const preset = this.getPreset(presetName);
    if (!preset) {
      throw new Error(`Preset not found: ${presetName}`);
    }

    return {
      ...baseConfig,
      ...preset,
      runs: preset.runs || baseConfig.runs || 1,
      timeout: preset.timeout || baseConfig.timeout
    };
  }

  /**
   * Create custom preset from current config
   */
  static createCustomPreset(name, description, config) {
    return {
      name,
      description,
      ...config,
      custom: true
    };
  }

  /**
   * Validate preset configuration
   */
  static validatePreset(preset) {
    const errors = [];

    if (!preset.name) errors.push('Preset must have a name');
    if (!preset.categories || preset.categories.length === 0) {
      errors.push('Preset must specify categories');
    }
    if (!preset.providers || preset.providers.length === 0) {
      errors.push('Preset must specify providers');
    }
    if (!preset.variants || preset.variants.length === 0) {
      errors.push('Preset must specify variants');
    }
    if (preset.runs && (preset.runs < 1 || preset.runs > 100)) {
      errors.push('Runs must be between 1 and 100');
    }
    if (preset.timeout && preset.timeout < 1000) {
      errors.push('Timeout must be at least 1000ms');
    }

    return {
      valid: errors.length === 0,
      errors
    };
  }

  /**
   * Estimate preset runtime
   */
  static estimateRuntime(preset, tasksCount = 10) {
    const runs = preset.runs || 1;
    const avgTimeout = preset.timeout || 60000;
    const providers = preset.providers?.length || 1;
    const variants = preset.variants?.length || 1;

    const totalTests = tasksCount * providers * variants * runs;
    const estimatedTimeMs = totalTests * (avgTimeout / 2); // Assume avg is half of timeout

    return {
      totalTests,
      estimatedTimeMs,
      estimatedTimeMinutes: (estimatedTimeMs / 1000 / 60).toFixed(1),
      breakdown: {
        tasks: tasksCount,
        providers,
        variants,
        runs
      }
    };
  }

  /**
   * Estimate cost (rough approximation)
   */
  static estimateCost(preset, tasksCount = 10) {
    // Rough token estimates
    const avgPromptTokens = 500;
    const avgCompletionTokens = 1000;

    const providerCosts = {
      'openai-gpt4': { input: 0.00003, output: 0.00006 },
      'openai-gpt35': { input: 0.000001, output: 0.000002 },
      'anthropic-claude': { input: 0.000015, output: 0.000075 },
      'google-gemini-pro': { input: 0.000001, output: 0.000002 }
    };

    let totalCost = 0;
    const providers = preset.providers || [];
    const runs = preset.runs || 1;
    const variants = preset.variants?.length || 1;

    for (const provider of providers) {
      const costs = providerCosts[provider] || providerCosts['openai-gpt35'];
      const testCount = tasksCount * variants * runs;
      const inputCost = testCount * avgPromptTokens * costs.input;
      const outputCost = testCount * avgCompletionTokens * costs.output;
      totalCost += inputCost + outputCost;
    }

    return {
      estimatedCost: totalCost.toFixed(2),
      currency: 'USD',
      assumptions: {
        avgPromptTokens,
        avgCompletionTokens
      }
    };
  }

  /**
   * Generate preset report
   */
  static generatePresetReport(presetName, tasksCount = 10) {
    const preset = this.getPreset(presetName);
    if (!preset) return null;

    const validation = this.validatePreset(preset);
    const runtime = this.estimateRuntime(preset, tasksCount);
    const cost = this.estimateCost(preset, tasksCount);

    return {
      preset: {
        name: preset.name,
        description: preset.description,
        key: presetName
      },
      validation,
      runtime,
      cost,
      configuration: {
        categories: preset.categories,
        providers: preset.providers,
        variants: preset.variants,
        runs: preset.runs,
        timeout: preset.timeout
      }
    };
  }
}
