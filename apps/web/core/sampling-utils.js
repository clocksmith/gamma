import { MathUtils } from '../utils/math.js';

export const SamplingUtils = {
  processLogitsPipeline(logits, { temperature, topK, topP }) {
    let currentLogits = Float32Array.from(logits);
    const stages = {};

    // 1. Temperature
    if (temperature > 0 && Math.abs(temperature - 1.0) > 1e-6) {
      currentLogits = this.applyTemperature(currentLogits, temperature);
    }
    stages.temperature = Float32Array.from(currentLogits);

    // 2. Top-K
    if (topK > 0 && topK < currentLogits.length) {
      currentLogits = this.applyTopK(currentLogits, topK);
    }
    stages.topK = Float32Array.from(currentLogits);

    // 3. Top-P
    if (topP > 0 && topP < 1.0) {
      currentLogits = this.applyTopP(currentLogits, topP);
    }
    stages.topP = Float32Array.from(currentLogits);

    // 4. Softmax
    const probs = MathUtils.softmax(currentLogits);

    return { probs, stages, finalLogits: currentLogits };
  },

  applyTemperature(logits, temperature) {
    const temp = Math.max(temperature, 1e-6);
    return logits.map(l => l / temp);
  },

  applyTopK(logits, k) {
    const sorted = [...logits].sort((a, b) => b - a);
    const threshold = sorted[k - 1];
    return logits.map(l => l >= threshold ? l : -Infinity);
  },

  applyTopP(logits, p) {
    const probs = MathUtils.softmax(logits);
    const indices = [...probs.keys()].sort((a, b) => probs[b] - probs[a]);
    
    let cumSum = 0;
    const keepIndices = new Set();
    
    for (const idx of indices) {
      keepIndices.add(idx);
      cumSum += probs[idx];
      if (cumSum >= p) break;
    }

    if (keepIndices.size === 0 && indices.length > 0) {
      keepIndices.add(indices[0]);
    }

    return logits.map((l, i) => keepIndices.has(i) ? l : -Infinity);
  }
};