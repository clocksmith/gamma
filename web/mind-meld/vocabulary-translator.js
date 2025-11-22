export class VocabularyTranslator {
  constructor() {
    this.cache = new Map();
  }

  translateLogits(sourceLogits, sourceEngine, targetEngine) {
    const cacheKey = `${sourceEngine.modelId}→${targetEngine.modelId}`;
    if (!this.cache.has(cacheKey)) {
      this.cache.set(cacheKey, this.buildMapping(sourceEngine, targetEngine));
    }

    const mapping = this.cache.get(cacheKey);
    const targetLogits = new Float32Array(targetEngine.getVocabularySize()).fill(-Infinity);

    for (const [sourceId, targetIds] of mapping) {
      const sourceLogit = sourceLogits[sourceId];
      for (const targetId of targetIds) {
        targetLogits[targetId] = Math.max(targetLogits[targetId], sourceLogit);
      }
    }
    return targetLogits;
  }

  buildMapping(sourceEngine, targetEngine) {
    const mapping = new Map();
    const sourceVocabSize = sourceEngine.getVocabularySize();
    for (let sourceId = 0; sourceId < sourceVocabSize; sourceId++) {
      const text = sourceEngine.getTokenText(sourceId);
      const targetIds = targetEngine.encode(text);
      mapping.set(sourceId, targetIds);
    }
    return mapping;
  }
}