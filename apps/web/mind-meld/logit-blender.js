/**
 * Logit Blender for Mind Meld system
 * Expanded blending strategies ported from Python src/mind_meld/core/blending.py
 */

import { MathUtils } from '../utils/math.js';

/**
 * Blending strategy enumeration
 */
export const BlendingStrategy = Object.freeze({
  WEIGHTED_AVERAGE: 'weighted_average',
  CONFIDENCE_WEIGHTED: 'confidence_weighted',
  ATTENTION_WEIGHTED: 'attention_weighted',
  DYNAMIC_WEIGHTED: 'dynamic_weighted',
  ENSEMBLE_VOTING: 'ensemble_voting',
  GEOMETRIC_MEAN: 'geometric_mean',
  HARMONIC_MEAN: 'harmonic_mean',
  MAX_POOLING: 'max_pooling',
  MIN_ENTROPY: 'min_entropy'
});

/**
 * Logit Blender - merges logits from multiple models
 */
export class LogitBlender {
  constructor(options = {}) {
    this.strategy = options.strategy ?? BlendingStrategy.WEIGHTED_AVERAGE;
    this.weights = options.weights ?? null;
    this.learningRate = options.learningRate ?? 0.1;
    this.temperature = options.temperature ?? 1.0;
    this.topK = options.topK ?? null;

    // For dynamic weighting
    this._dynamicWeights = null;
    this._performanceHistory = [];
    this._historyMaxLen = options.historyMaxLen ?? 50;
  }

  /**
   * Blend logits from multiple models
   */
  blend(logitsList, options = {}) {
    const strategy = options.strategy ?? this.strategy;
    const predictions = options.predictions ?? null;

    switch (strategy) {
      case BlendingStrategy.WEIGHTED_AVERAGE:
        return this.weightedAverage(logitsList);

      case BlendingStrategy.CONFIDENCE_WEIGHTED:
        return this.confidenceWeighted(logitsList);

      case BlendingStrategy.ATTENTION_WEIGHTED:
        return this.attentionWeighted(logitsList, predictions);

      case BlendingStrategy.DYNAMIC_WEIGHTED:
        return this.dynamicWeighted(logitsList, predictions);

      case BlendingStrategy.ENSEMBLE_VOTING:
        return this.ensembleVoting(logitsList);

      case BlendingStrategy.GEOMETRIC_MEAN:
        return this.geometricMean(logitsList);

      case BlendingStrategy.HARMONIC_MEAN:
        return this.harmonicMean(logitsList);

      case BlendingStrategy.MAX_POOLING:
        return this.maxPooling(logitsList);

      case BlendingStrategy.MIN_ENTROPY:
        return this.minEntropy(logitsList);

      default:
        return this.weightedAverage(logitsList);
    }
  }

  /**
   * Simple weighted average of logits
   */
  weightedAverage(logitsList) {
    const weights = this.weights ?? logitsList.map(() => 1 / logitsList.length);
    const result = new Float32Array(logitsList[0].length).fill(0);

    for (let i = 0; i < result.length; i++) {
      for (let m = 0; m < logitsList.length; m++) {
        result[i] += logitsList[m][i] * weights[m];
      }
    }

    return result;
  }

  /**
   * Weight by inverse entropy (confidence)
   * Models with lower entropy (more confident) get higher weights
   */
  confidenceWeighted(logitsList) {
    const confidences = logitsList.map(logits => {
      const probs = MathUtils.softmax(logits);
      const entropy = MathUtils.calculateEntropy(probs);
      // Inverse entropy as confidence, with smoothing
      return 1 / (entropy + 0.1);
    });

    const sum = confidences.reduce((a, b) => a + b, 0);
    const weights = confidences.map(c => c / sum);

    // Store for later inspection
    this._lastWeights = weights;

    return this._applyWeights(logitsList, weights);
  }

  /**
   * Weight by attention patterns
   * Models that attend more strongly to recent context get higher weights
   */
  attentionWeighted(logitsList, predictions) {
    if (!predictions || predictions.length !== logitsList.length) {
      // Fallback to confidence weighting
      return this.confidenceWeighted(logitsList);
    }

    const attentionWeights = predictions.map(pred => {
      const attention = pred.attention || pred.attentionWeights;
      if (!attention) return 0.5;

      // Calculate attention concentration on recent tokens
      // Higher concentration = higher weight
      const lastLayerAttn = Array.isArray(attention)
        ? attention[attention.length - 1]
        : attention;

      if (!lastLayerAttn || lastLayerAttn.length === 0) return 0.5;

      // Get attention to last 5 positions
      const recentAttn = lastLayerAttn.slice(-5);
      const avgRecent = recentAttn.reduce((a, b) => a + b, 0) / recentAttn.length;

      return avgRecent;
    });

    const sum = attentionWeights.reduce((a, b) => a + b, 0);
    const weights = sum > 0
      ? attentionWeights.map(w => w / sum)
      : logitsList.map(() => 1 / logitsList.length);

    this._lastWeights = weights;
    return this._applyWeights(logitsList, weights);
  }

  /**
   * Dynamic weighting that learns from prediction accuracy
   */
  dynamicWeighted(logitsList, predictions) {
    // Initialize dynamic weights if needed
    if (!this._dynamicWeights || this._dynamicWeights.length !== logitsList.length) {
      this._dynamicWeights = logitsList.map(() => 1 / logitsList.length);
    }

    // Update weights based on recent performance
    if (predictions && this._performanceHistory.length > 0) {
      this._updateDynamicWeights(predictions);
    }

    const weights = [...this._dynamicWeights];
    this._lastWeights = weights;

    return this._applyWeights(logitsList, weights);
  }

  /**
   * Update dynamic weights based on performance
   */
  _updateDynamicWeights(predictions) {
    // Get the last recorded correct answer
    const lastEntry = this._performanceHistory[this._performanceHistory.length - 1];
    if (!lastEntry) return;

    const correctTokenId = lastEntry.correctTokenId;

    // Update weights based on each model's prediction
    for (let i = 0; i < predictions.length && i < this._dynamicWeights.length; i++) {
      const pred = predictions[i];
      const probs = MathUtils.softmax(pred.logitsProcessed || pred.logits || []);

      if (correctTokenId < probs.length) {
        const correctProb = probs[correctTokenId];
        // Increase weight for models that assigned high probability to correct token
        const update = (correctProb - this._dynamicWeights[i]) * this.learningRate;
        this._dynamicWeights[i] = Math.max(0.01, Math.min(0.99, this._dynamicWeights[i] + update));
      }
    }

    // Normalize weights
    const sum = this._dynamicWeights.reduce((a, b) => a + b, 0);
    for (let i = 0; i < this._dynamicWeights.length; i++) {
      this._dynamicWeights[i] /= sum;
    }
  }

  /**
   * Record a result for dynamic weight learning
   */
  recordResult(correctTokenId) {
    this._performanceHistory.push({ correctTokenId, timestamp: Date.now() });

    // Trim history
    if (this._performanceHistory.length > this._historyMaxLen) {
      this._performanceHistory = this._performanceHistory.slice(-this._historyMaxLen);
    }
  }

  /**
   * Ensemble voting - each model votes for top-k tokens
   */
  ensembleVoting(logitsList) {
    const k = this.topK || 10;
    const votes = new Map();

    for (const logits of logitsList) {
      const probs = MathUtils.softmax(logits);

      // Get top-k tokens
      const indexed = Array.from(probs).map((p, i) => ({ p, i }));
      indexed.sort((a, b) => b.p - a.p);
      const topK = indexed.slice(0, k);

      // Vote with probability as weight
      for (const { p, i } of topK) {
        votes.set(i, (votes.get(i) || 0) + p);
      }
    }

    // Convert votes back to logits
    const result = new Float32Array(logitsList[0].length).fill(-Infinity);
    for (const [tokenId, voteWeight] of votes) {
      result[tokenId] = Math.log(voteWeight / logitsList.length + 1e-10);
    }

    return result;
  }

  /**
   * Geometric mean of probabilities
   */
  geometricMean(logitsList) {
    const result = new Float32Array(logitsList[0].length).fill(0);

    // Geometric mean is equivalent to arithmetic mean of log probabilities
    for (let i = 0; i < result.length; i++) {
      let logSum = 0;
      for (const logits of logitsList) {
        // Add small epsilon for numerical stability
        const logProb = logits[i] - Math.log(
          logitsList.reduce((s, l) => s + Math.exp(l[i]), 0) + 1e-10
        );
        logSum += logProb;
      }
      result[i] = logSum / logitsList.length;
    }

    return result;
  }

  /**
   * Harmonic mean of probabilities (emphasizes agreement)
   */
  harmonicMean(logitsList) {
    const allProbs = logitsList.map(l => MathUtils.softmax(l));
    const result = new Float32Array(logitsList[0].length).fill(0);

    for (let i = 0; i < result.length; i++) {
      let recipSum = 0;
      for (const probs of allProbs) {
        recipSum += 1 / (probs[i] + 1e-10);
      }
      const harmonicProb = allProbs.length / recipSum;
      result[i] = Math.log(harmonicProb + 1e-10);
    }

    return result;
  }

  /**
   * Max pooling - take the maximum logit for each token
   */
  maxPooling(logitsList) {
    const result = new Float32Array(logitsList[0].length);

    for (let i = 0; i < result.length; i++) {
      result[i] = Math.max(...logitsList.map(l => l[i]));
    }

    return result;
  }

  /**
   * Select distribution with minimum entropy
   */
  minEntropy(logitsList) {
    let minEntropy = Infinity;
    let bestLogits = logitsList[0];

    for (const logits of logitsList) {
      const probs = MathUtils.softmax(logits);
      const entropy = MathUtils.calculateEntropy(probs);

      if (entropy < minEntropy) {
        minEntropy = entropy;
        bestLogits = logits;
      }
    }

    return bestLogits;
  }

  /**
   * Apply weights to logits
   */
  _applyWeights(logitsList, weights) {
    const result = new Float32Array(logitsList[0].length).fill(0);

    for (let i = 0; i < result.length; i++) {
      for (let m = 0; m < logitsList.length; m++) {
        result[i] += logitsList[m][i] * weights[m];
      }
    }

    return result;
  }

  /**
   * Get the weights used in the last blend operation
   */
  getLastWeights() {
    return this._lastWeights || this.weights || [];
  }

  /**
   * Set explicit weights
   */
  setWeights(weights) {
    const sum = weights.reduce((a, b) => a + b, 0);
    this.weights = weights.map(w => w / sum);
  }

  /**
   * Reset dynamic learning state
   */
  reset() {
    this._dynamicWeights = null;
    this._performanceHistory = [];
    this._lastWeights = null;
  }
}

/**
 * Contrastive Decoding Blender
 * Uses expert model to steer, subtracts amateur models
 */
export class ContrastiveBlender {
  constructor(options = {}) {
    this.expertIndex = options.expertIndex ?? 0;
    this.alpha = options.alpha ?? 0.5; // Subtraction strength
    this.temperature = options.temperature ?? 1.0;
  }

  blend(logitsList) {
    if (logitsList.length < 2) {
      return logitsList[0];
    }

    const expertLogits = logitsList[this.expertIndex];

    // Average amateur logits
    const amateurLogits = new Float32Array(expertLogits.length).fill(0);
    let amateurCount = 0;

    for (let i = 0; i < logitsList.length; i++) {
      if (i !== this.expertIndex) {
        for (let j = 0; j < amateurLogits.length; j++) {
          amateurLogits[j] += logitsList[i][j];
        }
        amateurCount++;
      }
    }

    if (amateurCount > 0) {
      for (let j = 0; j < amateurLogits.length; j++) {
        amateurLogits[j] /= amateurCount;
      }
    }

    // Contrastive: expert - alpha * amateur
    const result = new Float32Array(expertLogits.length);
    for (let i = 0; i < result.length; i++) {
      result[i] = expertLogits[i] - this.alpha * amateurLogits[i];
    }

    // Apply temperature
    if (this.temperature !== 1.0) {
      for (let i = 0; i < result.length; i++) {
        result[i] /= this.temperature;
      }
    }

    return result;
  }
}
