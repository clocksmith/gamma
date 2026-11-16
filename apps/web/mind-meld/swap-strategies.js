/**
 * Swap Strategies for Mind Meld system
 * Expanded strategies ported from Python src/mind_meld/strategies/
 */

import { MathUtils } from '../utils/math.js';
import { SwapStrategy } from './config.js';

/**
 * Base class for swap strategies
 */
export class SwapStrategyBase {
  constructor(options = {}) {
    this.lastReason = '';
    this.verbose = options.verbose ?? false;
  }

  shouldSwap(lastToken, predictions, activeIndex) {
    throw new Error('Abstract method');
  }

  selectNext(predictions, currentIndex) {
    throw new Error('Abstract method');
  }
}

/**
 * Fixed interval strategy - swap every N tokens
 */
export class FixedIntervalStrategy extends SwapStrategyBase {
  constructor(options = {}) {
    super(options);
    this.interval = options.interval ?? 5;
    this.counter = 0;
  }

  shouldSwap(lastToken, predictions, activeIndex) {
    this.counter++;
    if (this.counter >= this.interval) {
      this.counter = 0;
      this.lastReason = `Fixed interval (${this.interval} tokens)`;
      return true;
    }
    return false;
  }

  selectNext(predictions, currentIndex) {
    return (currentIndex + 1) % predictions.length;
  }

  reset() {
    this.counter = 0;
  }
}

/**
 * Round robin strategy - strict turn-taking
 */
export class RoundRobinStrategy extends SwapStrategyBase {
  constructor(options = {}) {
    super(options);
  }

  shouldSwap(lastToken, predictions, activeIndex) {
    this.lastReason = 'Round robin';
    return true;
  }

  selectNext(predictions, currentIndex) {
    return (currentIndex + 1) % predictions.length;
  }
}

/**
 * Confidence-based strategy - swap when model is uncertain
 */
export class ConfidenceBasedStrategy extends SwapStrategyBase {
  constructor(options = {}) {
    super(options);
    this.threshold = options.threshold ?? 0.3;
    this.useEntropy = options.useEntropy ?? false;
  }

  shouldSwap(lastToken, predictions, activeIndex) {
    const activePred = predictions[activeIndex];
    const probs = MathUtils.softmax(activePred.logitsProcessed || activePred.logits || []);

    if (this.useEntropy) {
      const entropy = MathUtils.calculateEntropy(probs);
      const maxEntropy = Math.log(probs.length);
      const normalizedEntropy = entropy / maxEntropy;

      if (normalizedEntropy > (1 - this.threshold)) {
        this.lastReason = `High entropy: ${(normalizedEntropy * 100).toFixed(1)}%`;
        return true;
      }
    } else {
      const topProb = Math.max(...probs);
      if (topProb < this.threshold) {
        this.lastReason = `Low confidence: ${(topProb * 100).toFixed(1)}%`;
        return true;
      }
    }

    return false;
  }

  selectNext(predictions, currentIndex) {
    let maxConf = 0;
    let bestIdx = currentIndex;

    predictions.forEach((pred, idx) => {
      const probs = MathUtils.softmax(pred.logitsProcessed || pred.logits || []);
      const conf = Math.max(...probs);
      if (conf > maxConf) {
        maxConf = conf;
        bestIdx = idx;
      }
    });

    return bestIdx;
  }
}

/**
 * Perplexity-based strategy - swap on perplexity spikes
 */
export class PerplexityBasedStrategy extends SwapStrategyBase {
  constructor(options = {}) {
    super(options);
    this.threshold = options.threshold ?? 50.0;
    this.windowSize = options.windowSize ?? 10;
    this.spikeMultiplier = options.spikeMultiplier ?? 2.0;
    this._perplexityHistory = [];
  }

  shouldSwap(lastToken, predictions, activeIndex) {
    const activePred = predictions[activeIndex];
    const logits = activePred.logitsProcessed || activePred.logits || [];
    const probs = MathUtils.softmax(logits);

    // Calculate cross-entropy (log perplexity)
    const entropy = MathUtils.calculateEntropy(probs);
    const perplexity = Math.exp(entropy);

    // Add to history
    this._perplexityHistory.push(perplexity);
    if (this._perplexityHistory.length > this.windowSize) {
      this._perplexityHistory.shift();
    }

    // Check absolute threshold
    if (perplexity > this.threshold) {
      this.lastReason = `High perplexity: ${perplexity.toFixed(1)} > ${this.threshold}`;
      return true;
    }

    // Check for spike relative to recent history
    if (this._perplexityHistory.length >= 3) {
      const recentAvg = this._perplexityHistory.slice(0, -1)
        .reduce((a, b) => a + b, 0) / (this._perplexityHistory.length - 1);

      if (perplexity > recentAvg * this.spikeMultiplier) {
        this.lastReason = `Perplexity spike: ${perplexity.toFixed(1)} (${this.spikeMultiplier}x avg)`;
        return true;
      }
    }

    return false;
  }

  selectNext(predictions, currentIndex) {
    // Select model with lowest perplexity
    let minPerp = Infinity;
    let bestIdx = currentIndex;

    predictions.forEach((pred, idx) => {
      const probs = MathUtils.softmax(pred.logitsProcessed || pred.logits || []);
      const entropy = MathUtils.calculateEntropy(probs);
      const perplexity = Math.exp(entropy);

      if (perplexity < minPerp) {
        minPerp = perplexity;
        bestIdx = idx;
      }
    });

    return bestIdx;
  }

  getPerplexityHistory() {
    return [...this._perplexityHistory];
  }

  reset() {
    this._perplexityHistory = [];
  }
}

/**
 * Pattern-based strategy - swap on specific token patterns
 */
export class PatternBasedStrategy extends SwapStrategyBase {
  constructor(options = {}) {
    super(options);
    this.patterns = options.patterns ?? ['punctuation', 'newline'];
    this.lookahead = options.lookahead ?? 1;
    this._punctuationRegex = /[.!?,;:]/;
    this._newlineRegex = /[\n\r]/;
    this._sentenceEndRegex = /[.!?]$/;
  }

  shouldSwap(lastToken, predictions, activeIndex) {
    if (!lastToken) return false;

    for (const pattern of this.patterns) {
      if (this._matchesPattern(lastToken, pattern)) {
        this.lastReason = `Pattern match: ${pattern}`;
        return true;
      }
    }

    return false;
  }

  _matchesPattern(token, pattern) {
    switch (pattern) {
      case 'punctuation':
        return this._punctuationRegex.test(token);
      case 'newline':
        return this._newlineRegex.test(token);
      case 'sentence_end':
        return this._sentenceEndRegex.test(token);
      case 'space':
        return token.trim() === '' && token.length > 0;
      default:
        // Custom regex pattern
        try {
          return new RegExp(pattern).test(token);
        } catch {
          return false;
        }
    }
  }

  selectNext(predictions, currentIndex) {
    return (currentIndex + 1) % predictions.length;
  }
}

/**
 * Random strategy - occasional random swaps
 */
export class RandomStrategy extends SwapStrategyBase {
  constructor(options = {}) {
    super(options);
    this.probability = options.probability ?? 0.1;
  }

  shouldSwap(lastToken, predictions, activeIndex) {
    if (Math.random() < this.probability) {
      this.lastReason = `Random swap (p=${this.probability})`;
      return true;
    }
    return false;
  }

  selectNext(predictions, currentIndex) {
    // Random selection, excluding current
    const others = predictions.map((_, i) => i).filter(i => i !== currentIndex);
    if (others.length === 0) return currentIndex;
    return others[Math.floor(Math.random() * others.length)];
  }
}

/**
 * Attention-guided strategy - swap based on attention patterns
 */
export class AttentionGuidedStrategy extends SwapStrategyBase {
  constructor(options = {}) {
    super(options);
    this.threshold = options.threshold ?? 0.8;
    this.focusWindow = options.focusWindow ?? 5;
  }

  shouldSwap(lastToken, predictions, activeIndex) {
    const activePred = predictions[activeIndex];
    const attention = activePred.attention || activePred.attentionWeights;

    if (!attention) {
      return false;
    }

    // Get last layer attention
    const lastLayerAttn = Array.isArray(attention)
      ? attention[attention.length - 1]
      : attention;

    if (!lastLayerAttn || lastLayerAttn.length === 0) {
      return false;
    }

    // Check attention concentration
    const recentAttn = lastLayerAttn.slice(-this.focusWindow);
    const avgRecent = recentAttn.reduce((a, b) => a + b, 0) / recentAttn.length;

    // If attention is too diffuse, swap
    if (avgRecent < this.threshold) {
      this.lastReason = `Low attention focus: ${(avgRecent * 100).toFixed(1)}%`;
      return true;
    }

    return false;
  }

  selectNext(predictions, currentIndex) {
    // Select model with highest attention concentration
    let maxFocus = 0;
    let bestIdx = currentIndex;

    predictions.forEach((pred, idx) => {
      const attention = pred.attention || pred.attentionWeights;
      if (!attention) return;

      const lastLayerAttn = Array.isArray(attention)
        ? attention[attention.length - 1]
        : attention;

      if (lastLayerAttn && lastLayerAttn.length > 0) {
        const recentAttn = lastLayerAttn.slice(-this.focusWindow);
        const avgRecent = recentAttn.reduce((a, b) => a + b, 0) / recentAttn.length;

        if (avgRecent > maxFocus) {
          maxFocus = avgRecent;
          bestIdx = idx;
        }
      }
    });

    return bestIdx;
  }
}

/**
 * Composite strategy - combines multiple strategies
 */
export class CompositeStrategy extends SwapStrategyBase {
  constructor(options = {}) {
    super(options);
    this.strategies = options.strategies ?? [];
    this.mode = options.mode ?? 'any'; // 'any' or 'all'
  }

  addStrategy(strategy) {
    this.strategies.push(strategy);
  }

  shouldSwap(lastToken, predictions, activeIndex) {
    const results = this.strategies.map(s =>
      s.shouldSwap(lastToken, predictions, activeIndex)
    );

    const shouldSwap = this.mode === 'any'
      ? results.some(r => r)
      : results.every(r => r);

    if (shouldSwap) {
      const reasons = this.strategies
        .filter((_, i) => results[i])
        .map(s => s.lastReason)
        .filter(r => r);
      this.lastReason = reasons.join('; ');
    }

    return shouldSwap;
  }

  selectNext(predictions, currentIndex) {
    // Use first strategy that triggered swap, or first strategy
    for (const strategy of this.strategies) {
      if (strategy.lastReason) {
        return strategy.selectNext(predictions, currentIndex);
      }
    }
    return this.strategies[0]?.selectNext(predictions, currentIndex) ?? currentIndex;
  }

  reset() {
    for (const strategy of this.strategies) {
      if (typeof strategy.reset === 'function') {
        strategy.reset();
      }
    }
  }
}

/**
 * Factory function to create strategy from config
 */
export function createStrategy(config) {
  const strategyType = config.strategy || config.type || SwapStrategy.FIXED_INTERVAL;

  switch (strategyType) {
    case SwapStrategy.FIXED_INTERVAL:
    case 'fixed_interval':
      return new FixedIntervalStrategy({
        interval: config.interval ?? 5
      });

    case SwapStrategy.ROUND_ROBIN:
    case 'round_robin':
      return new RoundRobinStrategy();

    case SwapStrategy.CONFIDENCE_BASED:
    case 'confidence':
      return new ConfidenceBasedStrategy({
        threshold: config.minConfidence ?? config.threshold ?? 0.3,
        useEntropy: config.useEntropy ?? false
      });

    case SwapStrategy.PERPLEXITY_BASED:
    case 'perplexity':
      return new PerplexityBasedStrategy({
        threshold: config.perplexityThreshold ?? config.threshold ?? 50.0,
        windowSize: config.windowSize ?? 10,
        spikeMultiplier: config.spikeMultiplier ?? 2.0
      });

    case SwapStrategy.PATTERN_BASED:
    case 'pattern':
      return new PatternBasedStrategy({
        patterns: config.patterns ?? ['punctuation'],
        lookahead: config.patternLookahead ?? 1
      });

    case SwapStrategy.RANDOM:
    case 'random':
      return new RandomStrategy({
        probability: config.probability ?? 0.1
      });

    case SwapStrategy.ATTENTION_GUIDED:
    case 'attention':
      return new AttentionGuidedStrategy({
        threshold: config.attentionThreshold ?? 0.8,
        focusWindow: config.focusWindow ?? 5
      });

    default:
      console.warn(`Unknown strategy: ${strategyType}, falling back to fixed interval`);
      return new FixedIntervalStrategy();
  }
}

// Export all strategies
export {
  FixedIntervalStrategy,
  RoundRobinStrategy,
  ConfidenceBasedStrategy,
  PerplexityBasedStrategy,
  PatternBasedStrategy,
  RandomStrategy,
  AttentionGuidedStrategy,
  CompositeStrategy
};
