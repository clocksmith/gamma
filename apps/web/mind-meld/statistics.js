/**
 * Statistics Tracking for Mind Meld system
 * Port of Python src/mind_meld/core/statistics.py
 *
 * Tracks per-token metrics, swaps, and model contributions
 */

import { MathUtils } from '../utils/math.js';

/**
 * Single token statistics
 */
export class TokenStats {
  constructor(data = {}) {
    this.tokenIndex = data.tokenIndex ?? 0;
    this.tokenId = data.tokenId ?? null;
    this.tokenText = data.tokenText ?? '';
    this.timestamp = data.timestamp ?? Date.now();

    // Model selection
    this.activeModelIndex = data.activeModelIndex ?? 0;
    this.wasSwap = data.wasSwap ?? false;
    this.swapReason = data.swapReason ?? null;
    this.previousModel = data.previousModel ?? null;

    // Confidence metrics
    this.confidence = data.confidence ?? 0;
    this.entropy = data.entropy ?? 0;
    this.perplexity = data.perplexity ?? 0;

    // Multi-model metrics
    this.allModelConfidences = data.allModelConfidences ?? [];
    this.agreementScore = data.agreementScore ?? 0;
    this.blendWeights = data.blendWeights ?? [];

    // Performance
    this.predictionTimeMs = data.predictionTimeMs ?? 0;
  }

  toJSON() {
    return {
      tokenIndex: this.tokenIndex,
      tokenId: this.tokenId,
      tokenText: this.tokenText,
      timestamp: this.timestamp,
      activeModelIndex: this.activeModelIndex,
      wasSwap: this.wasSwap,
      swapReason: this.swapReason,
      previousModel: this.previousModel,
      confidence: this.confidence,
      entropy: this.entropy,
      perplexity: this.perplexity,
      allModelConfidences: this.allModelConfidences,
      agreementScore: this.agreementScore,
      blendWeights: this.blendWeights,
      predictionTimeMs: this.predictionTimeMs
    };
  }
}

/**
 * Swap event record
 */
export class SwapEvent {
  constructor(data = {}) {
    this.tokenIndex = data.tokenIndex ?? 0;
    this.timestamp = data.timestamp ?? Date.now();
    this.fromModel = data.fromModel ?? 0;
    this.toModel = data.toModel ?? 0;
    this.reason = data.reason ?? '';
    this.fromConfidence = data.fromConfidence ?? 0;
    this.toConfidence = data.toConfidence ?? 0;
  }

  toJSON() {
    return { ...this };
  }
}

/**
 * Statistics Tracker - tracks all metrics during generation
 */
export class StatisticsTracker {
  constructor(options = {}) {
    this.verbose = options.verbose ?? false;
    this.modelCount = options.modelCount ?? 1;
    this.modelIds = options.modelIds ?? [];

    // Token-level history
    this.tokenHistory = [];

    // Swap tracking
    this.swapEvents = [];

    // Aggregated stats
    this._stats = {
      totalTokens: 0,
      totalSwaps: 0,
      swapsPerModel: new Array(this.modelCount).fill(0),
      tokensPerModel: new Array(this.modelCount).fill(0),
      avgConfidencePerModel: new Array(this.modelCount).fill(0),
      totalConfidencePerModel: new Array(this.modelCount).fill(0),
      avgEntropy: 0,
      totalEntropy: 0,
      avgPerplexity: 0,
      totalPerplexity: 0,
      avgAgreement: 0,
      totalAgreement: 0,
      startTime: Date.now(),
      endTime: null,
      totalPredictionTimeMs: 0
    };

    // Per-model swap reasons
    this.swapReasons = new Map();
  }

  /**
   * Record a token generation
   */
  recordToken(data) {
    const tokenStats = new TokenStats({
      tokenIndex: this._stats.totalTokens,
      ...data
    });

    this.tokenHistory.push(tokenStats);

    // Update aggregates
    this._stats.totalTokens++;
    this._stats.tokensPerModel[data.activeModelIndex]++;
    this._stats.totalConfidencePerModel[data.activeModelIndex] += data.confidence || 0;
    this._stats.totalEntropy += data.entropy || 0;
    this._stats.totalPerplexity += data.perplexity || 0;
    this._stats.totalAgreement += data.agreementScore || 0;
    this._stats.totalPredictionTimeMs += data.predictionTimeMs || 0;

    // Track swap
    if (data.wasSwap) {
      this.recordSwap({
        tokenIndex: this._stats.totalTokens - 1,
        fromModel: data.previousModel,
        toModel: data.activeModelIndex,
        reason: data.swapReason,
        fromConfidence: this.tokenHistory.length > 1
          ? this.tokenHistory[this.tokenHistory.length - 2].confidence
          : 0,
        toConfidence: data.confidence
      });
    }

    return tokenStats;
  }

  /**
   * Record a swap event
   */
  recordSwap(data) {
    const swapEvent = new SwapEvent(data);
    this.swapEvents.push(swapEvent);

    this._stats.totalSwaps++;
    if (data.toModel !== undefined) {
      this._stats.swapsPerModel[data.toModel]++;
    }

    // Track reasons
    const reason = data.reason || 'unknown';
    this.swapReasons.set(reason, (this.swapReasons.get(reason) || 0) + 1);

    return swapEvent;
  }

  /**
   * Get computed statistics
   */
  getStats() {
    const stats = { ...this._stats };

    // Compute averages
    if (stats.totalTokens > 0) {
      stats.avgEntropy = stats.totalEntropy / stats.totalTokens;
      stats.avgPerplexity = stats.totalPerplexity / stats.totalTokens;
      stats.avgAgreement = stats.totalAgreement / stats.totalTokens;
      stats.avgPredictionTimeMs = stats.totalPredictionTimeMs / stats.totalTokens;

      // Per-model averages
      stats.avgConfidencePerModel = stats.tokensPerModel.map((count, i) =>
        count > 0 ? stats.totalConfidencePerModel[i] / count : 0
      );
    }

    // Model usage percentages
    stats.modelUsagePercent = stats.tokensPerModel.map(count =>
      stats.totalTokens > 0 ? (count / stats.totalTokens) * 100 : 0
    );

    // Swap rate
    stats.swapRate = stats.totalTokens > 1
      ? stats.totalSwaps / (stats.totalTokens - 1)
      : 0;

    // Duration
    stats.endTime = Date.now();
    stats.durationMs = stats.endTime - stats.startTime;
    stats.tokensPerSecond = stats.durationMs > 0
      ? (stats.totalTokens / stats.durationMs) * 1000
      : 0;

    // Swap reasons breakdown
    stats.swapReasonBreakdown = Object.fromEntries(this.swapReasons);

    return stats;
  }

  /**
   * Get recent token history
   */
  getRecentHistory(count = 10) {
    return this.tokenHistory.slice(-count);
  }

  /**
   * Get swap events
   */
  getSwapEvents() {
    return [...this.swapEvents];
  }

  /**
   * Get confidence trend
   */
  getConfidenceTrend(windowSize = 10) {
    if (this.tokenHistory.length === 0) return [];

    const trend = [];
    for (let i = 0; i < this.tokenHistory.length; i++) {
      const start = Math.max(0, i - windowSize + 1);
      const window = this.tokenHistory.slice(start, i + 1);
      const avgConf = window.reduce((sum, t) => sum + t.confidence, 0) / window.length;
      trend.push({
        tokenIndex: i,
        confidence: this.tokenHistory[i].confidence,
        movingAverage: avgConf
      });
    }
    return trend;
  }

  /**
   * Get perplexity trend
   */
  getPerplexityTrend(windowSize = 10) {
    if (this.tokenHistory.length === 0) return [];

    const trend = [];
    for (let i = 0; i < this.tokenHistory.length; i++) {
      const start = Math.max(0, i - windowSize + 1);
      const window = this.tokenHistory.slice(start, i + 1);
      const avgPerp = window.reduce((sum, t) => sum + t.perplexity, 0) / window.length;
      trend.push({
        tokenIndex: i,
        perplexity: this.tokenHistory[i].perplexity,
        movingAverage: avgPerp
      });
    }
    return trend;
  }

  /**
   * Get model contribution summary
   */
  getModelContributions() {
    const stats = this.getStats();
    return this.modelIds.map((id, i) => ({
      modelId: id,
      modelIndex: i,
      tokensGenerated: stats.tokensPerModel[i],
      usagePercent: stats.modelUsagePercent[i],
      avgConfidence: stats.avgConfidencePerModel[i],
      swapsTo: stats.swapsPerModel[i]
    }));
  }

  /**
   * Export full statistics
   */
  export() {
    return {
      stats: this.getStats(),
      tokenHistory: this.tokenHistory.map(t => t.toJSON()),
      swapEvents: this.swapEvents.map(e => e.toJSON()),
      modelContributions: this.getModelContributions(),
      confidenceTrend: this.getConfidenceTrend(),
      perplexityTrend: this.getPerplexityTrend()
    };
  }

  /**
   * Reset all statistics
   */
  reset() {
    this.tokenHistory = [];
    this.swapEvents = [];
    this.swapReasons.clear();

    this._stats = {
      totalTokens: 0,
      totalSwaps: 0,
      swapsPerModel: new Array(this.modelCount).fill(0),
      tokensPerModel: new Array(this.modelCount).fill(0),
      avgConfidencePerModel: new Array(this.modelCount).fill(0),
      totalConfidencePerModel: new Array(this.modelCount).fill(0),
      avgEntropy: 0,
      totalEntropy: 0,
      avgPerplexity: 0,
      totalPerplexity: 0,
      avgAgreement: 0,
      totalAgreement: 0,
      startTime: Date.now(),
      endTime: null,
      totalPredictionTimeMs: 0
    };
  }

  /**
   * Generate summary string
   */
  getSummaryString() {
    const stats = this.getStats();
    const lines = [
      `=== Mind Meld Statistics ===`,
      `Total Tokens: ${stats.totalTokens}`,
      `Duration: ${(stats.durationMs / 1000).toFixed(2)}s`,
      `Speed: ${stats.tokensPerSecond.toFixed(1)} tok/s`,
      ``,
      `--- Model Usage ---`
    ];

    this.modelIds.forEach((id, i) => {
      lines.push(`  ${id}: ${stats.tokensPerModel[i]} tokens (${stats.modelUsagePercent[i].toFixed(1)}%)`);
    });

    lines.push(``);
    lines.push(`--- Swaps ---`);
    lines.push(`Total Swaps: ${stats.totalSwaps}`);
    lines.push(`Swap Rate: ${(stats.swapRate * 100).toFixed(1)}%`);

    if (this.swapReasons.size > 0) {
      lines.push(`Swap Reasons:`);
      for (const [reason, count] of this.swapReasons) {
        lines.push(`  ${reason}: ${count}`);
      }
    }

    lines.push(``);
    lines.push(`--- Quality ---`);
    lines.push(`Avg Entropy: ${stats.avgEntropy.toFixed(3)}`);
    lines.push(`Avg Perplexity: ${stats.avgPerplexity.toFixed(2)}`);
    lines.push(`Avg Agreement: ${(stats.avgAgreement * 100).toFixed(1)}%`);

    return lines.join('\n');
  }
}

/**
 * Compute agreement score between predictions
 */
export function computeAgreementScore(predictions, topK = 5) {
  if (predictions.length < 2) return 1.0;

  // Get top-k tokens for each prediction
  const topTokenSets = predictions.map(pred => {
    const probs = MathUtils.softmax(pred.logitsProcessed || pred.logits || []);
    const indexed = Array.from(probs).map((p, i) => ({ p, i }));
    indexed.sort((a, b) => b.p - a.p);
    return new Set(indexed.slice(0, topK).map(x => x.i));
  });

  // Compute pairwise intersection
  let totalIntersection = 0;
  let pairCount = 0;

  for (let i = 0; i < topTokenSets.length; i++) {
    for (let j = i + 1; j < topTokenSets.length; j++) {
      const intersection = [...topTokenSets[i]].filter(x => topTokenSets[j].has(x));
      totalIntersection += intersection.length / topK;
      pairCount++;
    }
  }

  return pairCount > 0 ? totalIntersection / pairCount : 0;
}

/**
 * Compute per-token metrics
 */
export function computeTokenMetrics(prediction, activeModelIndex = 0) {
  const logits = prediction.logitsProcessed || prediction.logits || [];
  const probs = MathUtils.softmax(logits);

  const entropy = MathUtils.calculateEntropy(probs);
  const perplexity = Math.exp(entropy);
  const confidence = Math.max(...probs);

  return {
    confidence,
    entropy,
    perplexity,
    activeModelIndex
  };
}
