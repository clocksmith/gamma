/**
 * Benchmark Query Interface
 *
 * Transforms raw benchmark data into actionable recommendations.
 * Answers questions like "Which model should I use for Python coding?"
 *
 * Based on Penteract principles: Make insights accessible and actionable.
 */

import fs from 'fs';
import path from 'path';

/**
 * Intent types that can be extracted from natural language questions
 */
const IntentType = {
  BEST_FOR_TASK: 'best_for_task',
  COST_PERFORMANCE: 'cost_performance',
  COMPARISON: 'comparison',
  SPEED_FOCUS: 'speed_focus',
  QUALITY_FOCUS: 'quality_focus',
  GENERAL: 'general'
};

/**
 * Model capabilities and metadata
 */
const MODEL_METADATA = {
  'openai-gpt4': {
    cost_per_1k_tokens: 0.03,
    speed_tier: 'medium',
    strengths: ['reasoning', 'complex_tasks', 'code_review'],
    weaknesses: ['cost', 'speed']
  },
  'anthropic-claude': {
    cost_per_1k_tokens: 0.024,
    speed_tier: 'fast',
    strengths: ['code_generation', 'creative_writing', 'analysis'],
    weaknesses: ['cost']
  },
  'google-gemini-pro': {
    cost_per_1k_tokens: 0.0005,
    speed_tier: 'very_fast',
    strengths: ['multimodal', 'cost_effective', 'speed'],
    weaknesses: ['complex_reasoning']
  },
  'ollama-llama3': {
    cost_per_1k_tokens: 0.0,
    speed_tier: 'fast',
    strengths: ['local', 'privacy', 'cost'],
    weaknesses: ['accuracy_on_complex_tasks']
  },
  'ollama-codellama': {
    cost_per_1k_tokens: 0.0,
    speed_tier: 'medium',
    strengths: ['code_specific', 'local', 'cost'],
    weaknesses: ['general_tasks']
  }
};

/**
 * Task categories and their requirements
 */
const TASK_REQUIREMENTS = {
  'python_coding': {
    primary_metrics: ['accuracy', 'completeness'],
    nice_to_have: ['speed'],
    acceptable_cost: 0.01
  },
  'creative_writing': {
    primary_metrics: ['creativity', 'quality'],
    nice_to_have: ['cost'],
    acceptable_cost: 0.05
  },
  'chat_assistant': {
    primary_metrics: ['speed', 'quality'],
    nice_to_have: ['cost'],
    acceptable_cost: 0.005
  },
  'code_review': {
    primary_metrics: ['accuracy', 'quality'],
    nice_to_have: ['completeness'],
    acceptable_cost: 0.02
  },
  'quick_prototyping': {
    primary_metrics: ['speed', 'cost'],
    nice_to_have: ['quality'],
    acceptable_cost: 0.001
  }
};

class BenchmarkQueryEngine {
  constructor(resultsDirectory) {
    this.resultsDirectory = resultsDirectory;
    this.results = this.loadResults();
  }

  /**
   * Load all benchmark results from the results directory
   */
  loadResults() {
    const resultsPath = path.join(this.resultsDirectory, 'latest.json');

    if (!fs.existsSync(resultsPath)) {
      throw new Error(`Results file not found: ${resultsPath}`);
    }

    return JSON.parse(fs.readFileSync(resultsPath, 'utf-8'));
  }

  /**
   * Answer a natural language question about model performance
   */
  async answerQuestion(question) {
    const intent = this.parseIntent(question);

    switch (intent.type) {
      case IntentType.BEST_FOR_TASK:
        return this.findBestModelForTask(intent.task);

      case IntentType.COST_PERFORMANCE:
        return this.optimizeCostPerformance(intent.constraints);

      case IntentType.COMPARISON:
        return this.compareModels(intent.models, intent.dimensions);

      case IntentType.SPEED_FOCUS:
        return this.findFastestModel(intent.quality_threshold);

      case IntentType.QUALITY_FOCUS:
        return this.findHighestQuality(intent.cost_limit);

      default:
        return this.generalQuery(question);
    }
  }

  /**
   * Parse user intent from natural language
   */
  parseIntent(question) {
    const lower = question.toLowerCase();

    // Best for task
    if (lower.includes('which') && (lower.includes('for') || lower.includes('should i use'))) {
      const task = this.extractTask(lower);
      return { type: IntentType.BEST_FOR_TASK, task };
    }

    // Cost/performance optimization
    if (lower.includes('cheap') || lower.includes('cost') || lower.includes('affordable')) {
      return { type: IntentType.COST_PERFORMANCE, constraints: this.extractConstraints(lower) };
    }

    // Speed focus
    if (lower.includes('fast') || lower.includes('quick') || lower.includes('speed')) {
      return { type: IntentType.SPEED_FOCUS, quality_threshold: 0.7 };
    }

    // Quality focus
    if (lower.includes('best quality') || lower.includes('most accurate')) {
      return { type: IntentType.QUALITY_FOCUS, cost_limit: null };
    }

    // Comparison
    if (lower.includes('compare') || lower.includes('vs') || lower.includes('versus')) {
      const models = this.extractModels(lower);
      return { type: IntentType.COMPARISON, models, dimensions: ['quality', 'speed', 'cost'] };
    }

    return { type: IntentType.GENERAL, question };
  }

  /**
   * Find the best model for a specific task
   */
  findBestModelForTask(taskHint) {
    // Map task hint to formal task category
    const taskCategory = this.mapToTaskCategory(taskHint);
    const requirements = TASK_REQUIREMENTS[taskCategory] || TASK_REQUIREMENTS['python_coding'];

    // Score each model based on task requirements
    const scored = Object.entries(this.results.by_model || {}).map(([model, data]) => {
      let score = 0;

      // Primary metrics (weight: 0.7)
      requirements.primary_metrics.forEach(metric => {
        score += (data.avg_scores?.[metric] || 0) * 0.7;
      });

      // Nice-to-have metrics (weight: 0.3)
      requirements.nice_to_have.forEach(metric => {
        score += (data.avg_scores?.[metric] || 0) * 0.3;
      });

      // Cost penalty if over acceptable cost
      const metadata = MODEL_METADATA[model] || { cost_per_1k_tokens: 0.01 };
      if (metadata.cost_per_1k_tokens > requirements.acceptable_cost) {
        score *= 0.9;
      }

      return {
        model,
        score,
        data,
        metadata
      };
    });

    // Sort by score
    scored.sort((a, b) => b.score - a.score);

    const best = scored[0];

    return {
      recommendation: best.model,
      confidence: this.calculateConfidence(best, scored),
      reasoning: this.generateReasoning(best, taskCategory, requirements),
      alternatives: scored.slice(1, 3).map(m => ({
        model: m.model,
        reason: this.whyAlternative(m, best)
      })),
      stats: {
        quality_score: best.data.avg_scores?.quality || 0,
        speed: best.data.avg_duration_ms || 0,
        cost_per_1k: best.metadata.cost_per_1k_tokens
      }
    };
  }

  /**
   * Optimize for cost/performance balance
   */
  optimizeCostPerformance(constraints) {
    const minQuality = constraints.min_quality || 0.7;
    const maxCost = constraints.max_cost_per_1k || 0.01;

    const viable = Object.entries(this.results.by_model || {})
      .map(([model, data]) => {
        const metadata = MODEL_METADATA[model] || { cost_per_1k_tokens: 0.01 };
        const quality = data.avg_scores?.quality || 0;
        const cost = metadata.cost_per_1k_tokens;

        // Quality/cost ratio (higher is better)
        const ratio = cost > 0 ? quality / cost : quality * 1000;

        return {
          model,
          quality,
          cost,
          ratio,
          data,
          metadata
        };
      })
      .filter(m => m.quality >= minQuality && m.cost <= maxCost)
      .sort((a, b) => b.ratio - a.ratio);

    if (viable.length === 0) {
      return {
        error: 'No models meet your constraints',
        suggestion: 'Try relaxing quality requirements or increasing cost limit',
        best_quality: this.findHighestQuality(maxCost),
        cheapest: this.findCheapestViable(minQuality)
      };
    }

    const best = viable[0];

    return {
      recommendation: best.model,
      reasoning: `Best quality/cost ratio: ${best.ratio.toFixed(1)}x`,
      stats: {
        quality: best.quality,
        cost_per_1k: best.cost,
        quality_cost_ratio: best.ratio
      },
      savings: this.calculateSavings(best, viable),
      alternatives: viable.slice(1, 3)
    };
  }

  /**
   * Compare multiple models across dimensions
   */
  compareModels(modelNames, dimensions) {
    if (!modelNames || modelNames.length < 2) {
      modelNames = Object.keys(this.results.by_model || {}).slice(0, 3);
    }

    const comparison = {
      models: modelNames,
      dimensions: {},
      winner_by_dimension: {},
      overall_winner: null
    };

    // Compare across each dimension
    dimensions.forEach(dim => {
      comparison.dimensions[dim] = {};
      let bestModel = null;
      let bestValue = -Infinity;

      modelNames.forEach(model => {
        const data = this.results.by_model?.[model];
        if (!data) return;

        let value;
        if (dim === 'quality') {
          value = data.avg_scores?.quality || 0;
        } else if (dim === 'speed') {
          value = 1000 / (data.avg_duration_ms || 1000); // Invert: faster is better
        } else if (dim === 'cost') {
          const metadata = MODEL_METADATA[model];
          value = 1 / (metadata?.cost_per_1k_tokens || 0.01); // Invert: cheaper is better
        } else {
          value = data.avg_scores?.[dim] || 0;
        }

        comparison.dimensions[dim][model] = value;

        if (value > bestValue) {
          bestValue = value;
          bestModel = model;
        }
      });

      comparison.winner_by_dimension[dim] = bestModel;
    });

    // Determine overall winner (simple scoring)
    const overallScores = {};
    modelNames.forEach(model => {
      overallScores[model] = Object.values(comparison.dimensions)
        .reduce((sum, dimScores) => sum + (dimScores[model] || 0), 0);
    });

    comparison.overall_winner = Object.entries(overallScores)
      .sort(([, a], [, b]) => b - a)[0][0];

    return comparison;
  }

  /**
   * Find the fastest model above a quality threshold
   */
  findFastestModel(qualityThreshold = 0.7) {
    const viable = Object.entries(this.results.by_model || {})
      .filter(([, data]) => (data.avg_scores?.quality || 0) >= qualityThreshold)
      .map(([model, data]) => ({
        model,
        speed: data.avg_duration_ms || Infinity,
        quality: data.avg_scores?.quality || 0,
        data
      }))
      .sort((a, b) => a.speed - b.speed);

    if (viable.length === 0) {
      return { error: 'No models meet quality threshold' };
    }

    return {
      recommendation: viable[0].model,
      speed_ms: viable[0].speed,
      quality: viable[0].quality,
      speed_advantage: viable.length > 1
        ? `${((viable[1].speed / viable[0].speed - 1) * 100).toFixed(0)}% faster than next best`
        : 'Fastest available'
    };
  }

  /**
   * Find highest quality model within cost limit
   */
  findHighestQuality(costLimit = null) {
    let viable = Object.entries(this.results.by_model || {}).map(([model, data]) => {
      const metadata = MODEL_METADATA[model] || { cost_per_1k_tokens: 0.01 };
      return {
        model,
        quality: data.avg_scores?.quality || 0,
        cost: metadata.cost_per_1k_tokens,
        data,
        metadata
      };
    });

    if (costLimit !== null) {
      viable = viable.filter(m => m.cost <= costLimit);
    }

    viable.sort((a, b) => b.quality - a.quality);

    if (viable.length === 0) {
      return { error: 'No models within cost limit' };
    }

    return {
      recommendation: viable[0].model,
      quality: viable[0].quality,
      cost_per_1k: viable[0].cost,
      quality_advantage: viable.length > 1
        ? `${((viable[0].quality - viable[1].quality) * 100).toFixed(1)}% better than next`
        : 'Highest quality available'
    };
  }

  /**
   * Generate natural language reasoning for recommendation
   */
  generateReasoning(model, taskCategory, requirements) {
    const metadata = model.metadata;
    const reasons = [];

    // Quality reasoning
    if (model.data.avg_scores?.quality > 0.85) {
      reasons.push(`Excels at ${taskCategory} (${(model.data.avg_scores.quality * 100).toFixed(0)}th percentile)`);
    }

    // Speed reasoning
    if (metadata.speed_tier === 'very_fast' || metadata.speed_tier === 'fast') {
      reasons.push(`${metadata.speed_tier} response times`);
    }

    // Cost reasoning
    if (metadata.cost_per_1k_tokens === 0) {
      reasons.push('Free (local model)');
    } else if (metadata.cost_per_1k_tokens < 0.001) {
      reasons.push('Very cost-effective');
    }

    // Strengths
    const relevantStrengths = metadata.strengths.filter(s =>
      taskCategory.includes(s) || requirements.primary_metrics.includes(s)
    );
    if (relevantStrengths.length > 0) {
      reasons.push(`Strong at: ${relevantStrengths.join(', ')}`);
    }

    return reasons.join('. ') + '.';
  }

  /**
   * Calculate confidence in recommendation (0-1)
   */
  calculateConfidence(best, all) {
    if (all.length < 2) return 1.0;

    const gap = best.score - all[1].score;
    const maxGap = best.score;

    // Higher confidence if clear winner
    return Math.min(0.95, 0.5 + (gap / maxGap));
  }

  /**
   * Explain why a model is an alternative
   */
  whyAlternative(alternative, best) {
    if (alternative.metadata.cost_per_1k_tokens < best.metadata.cost_per_1k_tokens) {
      return 'More cost-effective';
    }
    if (alternative.metadata.speed_tier === 'very_fast') {
      return 'Faster response times';
    }
    if (alternative.metadata.cost_per_1k_tokens === 0) {
      return 'Local/private (no API cost)';
    }
    return 'Good balance of quality and cost';
  }

  /**
   * Map task hint to formal category
   */
  mapToTaskCategory(hint) {
    const lower = hint.toLowerCase();

    if (lower.includes('python') || lower.includes('coding') || lower.includes('programming')) {
      return 'python_coding';
    }
    if (lower.includes('creative') || lower.includes('writing') || lower.includes('story')) {
      return 'creative_writing';
    }
    if (lower.includes('chat') || lower.includes('conversation')) {
      return 'chat_assistant';
    }
    if (lower.includes('review') || lower.includes('audit')) {
      return 'code_review';
    }
    if (lower.includes('prototype') || lower.includes('quick') || lower.includes('draft')) {
      return 'quick_prototyping';
    }

    return 'python_coding'; // Default
  }

  /**
   * Extract task from question
   */
  extractTask(question) {
    // Simple extraction - can be improved with NLP
    const patterns = [
      /for ([\w\s]+)/,
      /use for ([\w\s]+)/,
      /good at ([\w\s]+)/
    ];

    for (const pattern of patterns) {
      const match = question.match(pattern);
      if (match) {
        return match[1].trim();
      }
    }

    return 'general tasks';
  }

  /**
   * Extract constraints from question
   */
  extractConstraints(question) {
    return {
      min_quality: 0.7,
      max_cost_per_1k: 0.01
    };
  }

  /**
   * Extract model names from question
   */
  extractModels(question) {
    const allModels = Object.keys(this.results.by_model || {});
    return allModels.filter(model =>
      question.toLowerCase().includes(model.toLowerCase())
    );
  }

  /**
   * Calculate potential savings
   */
  calculateSavings(chosen, alternatives) {
    const expensive = alternatives[alternatives.length - 1];
    if (!expensive || expensive.cost <= chosen.cost) {
      return null;
    }

    const savingsPercent = ((expensive.cost - chosen.cost) / expensive.cost * 100);
    return {
      vs_most_expensive: `${savingsPercent.toFixed(0)}% cost reduction`,
      annual_savings_per_million_tokens: ((expensive.cost - chosen.cost) * 1000).toFixed(2)
    };
  }

  /**
   * Find cheapest viable model above quality threshold
   */
  findCheapestViable(minQuality) {
    const viable = Object.entries(this.results.by_model || {})
      .filter(([, data]) => (data.avg_scores?.quality || 0) >= minQuality)
      .map(([model, data]) => ({
        model,
        cost: MODEL_METADATA[model]?.cost_per_1k_tokens || 0.01,
        quality: data.avg_scores?.quality || 0
      }))
      .sort((a, b) => a.cost - b.cost);

    return viable[0];
  }
}

export {
  BenchmarkQueryEngine,
  IntentType,
  MODEL_METADATA,
  TASK_REQUIREMENTS
};
