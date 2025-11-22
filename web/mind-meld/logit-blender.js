import { MathUtils } from '../utils/math.js';

export class LogitBlender {
  constructor(strategy = 'weighted_average') {
    this.strategy = strategy;
    this.weights = null;
  }

  blend(logitsList) {
    if (this.strategy === 'confidence_weighted') {
      return this.confidenceWeighted(logitsList);
    }
    return this.weightedAverage(logitsList);
  }

  weightedAverage(logitsList) {
    const weights = this.weights || logitsList.map(() => 1 / logitsList.length);
    const result = new Float32Array(logitsList[0].length);
    for (let i = 0; i < result.length; i++) {
      result[i] = logitsList.reduce((sum, logits, idx) => sum + logits[i] * weights[idx], 0);
    }
    return result;
  }

  confidenceWeighted(logitsList) {
    const weights = logitsList.map(logits => {
      const probs = MathUtils.softmax(logits);
      const entropy = MathUtils.calculateEntropy(probs);
      return 1 / (entropy + 1e-6);
    });
    const sum = weights.reduce((a, b) => a + b, 0);
    this.weights = weights.map(w => w / sum);
    return this.weightedAverage(logitsList);
  }
}