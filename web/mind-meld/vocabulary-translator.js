/**
 * Vocabulary Translator for Mind Meld system
 * Port of Python src/mind_meld/translators/vocabulary_aligner.py
 *
 * Handles vocabulary alignment and logit translation between models
 */

import { MathUtils } from '../utils/math.js';
import { Storage } from '../utils/storage.js';

/**
 * Quality metrics for vocabulary mapping
 */
export class MappingQuality {
  constructor(options = {}) {
    this.overlapRatio = options.overlapRatio ?? 0;
    this.commonTokenCount = options.commonTokenCount ?? 0;
    this.sourceCoverage = options.sourceCoverage ?? 0;
    this.targetCoverage = options.targetCoverage ?? 0;
    this.specialTokenOverlap = options.specialTokenOverlap ?? 0;
    this.subwordRatio = options.subwordRatio ?? 0;
  }

  /**
   * Compute overall quality score (0-1)
   */
  get overallScore() {
    return (
      this.overlapRatio * 0.3 +
      this.sourceCoverage * 0.25 +
      this.targetCoverage * 0.25 +
      this.specialTokenOverlap * 0.1 +
      Math.min(this.subwordRatio, 0.5) * 0.2
    );
  }

  /**
   * Get human-readable quality level
   */
  get qualityLevel() {
    const score = this.overallScore;
    if (score >= 0.8) return 'excellent';
    if (score >= 0.6) return 'good';
    if (score >= 0.4) return 'fair';
    if (score >= 0.2) return 'poor';
    return 'incompatible';
  }

  toJSON() {
    return {
      overlapRatio: this.overlapRatio,
      commonTokenCount: this.commonTokenCount,
      sourceCoverage: this.sourceCoverage,
      targetCoverage: this.targetCoverage,
      specialTokenOverlap: this.specialTokenOverlap,
      subwordRatio: this.subwordRatio
    };
  }

  static fromJSON(data) {
    return new MappingQuality(data);
  }
}

/**
 * Mapping between vocabularies of different models
 */
export class VocabularyMapping {
  constructor(options = {}) {
    this.sourceToTarget = options.sourceToTarget ?? new Map();
    this.targetToSource = options.targetToSource ?? new Map();
    this.commonTokens = options.commonTokens ?? new Set();
    this.sourceOnly = options.sourceOnly ?? new Set();
    this.targetOnly = options.targetOnly ?? new Set();
    this.overlapRatio = options.overlapRatio ?? 0;
    this.quality = options.quality ?? null;
  }

  /**
   * Check if vocabularies are sufficiently compatible
   */
  isCompatible(minOverlap = 0.5) {
    return this.overlapRatio >= minOverlap;
  }

  /**
   * Get overall quality score if available
   */
  getQualityScore() {
    if (this.quality) {
      return this.quality.overallScore;
    }
    return this.overlapRatio;
  }

  toJSON() {
    return {
      sourceToTarget: Object.fromEntries(this.sourceToTarget),
      targetToSource: Object.fromEntries(this.targetToSource),
      commonTokens: Array.from(this.commonTokens),
      sourceOnly: Array.from(this.sourceOnly),
      targetOnly: Array.from(this.targetOnly),
      overlapRatio: this.overlapRatio,
      quality: this.quality?.toJSON() ?? null
    };
  }

  static fromJSON(data) {
    return new VocabularyMapping({
      sourceToTarget: new Map(Object.entries(data.sourceToTarget).map(([k, v]) => [parseInt(k), v])),
      targetToSource: new Map(Object.entries(data.targetToSource).map(([k, v]) => [parseInt(k), v])),
      commonTokens: new Set(data.commonTokens),
      sourceOnly: new Set(data.sourceOnly),
      targetOnly: new Set(data.targetOnly),
      overlapRatio: data.overlapRatio,
      quality: data.quality ? MappingQuality.fromJSON(data.quality) : null
    });
  }
}

/**
 * Vocabulary Aligner - handles vocabulary alignment between models
 */
export class VocabularyAligner {
  constructor(options = {}) {
    this.verbose = options.verbose ?? false;
    this.useDiskCache = options.useDiskCache ?? true;
    this.mappingsCache = new Map();
    this.intersectionCache = new Map();
  }

  /**
   * Generate cache key for model pair
   */
  _getCacheKey(sourceName, targetName) {
    const combined = `${sourceName}::${targetName}`;
    // Simple hash function
    let hash = 0;
    for (let i = 0; i < combined.length; i++) {
      const char = combined.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash;
    }
    return `vocab_${Math.abs(hash).toString(16)}`;
  }

  /**
   * Load cached mapping from IndexedDB
   */
  async _loadCachedMapping(sourceName, targetName) {
    if (!this.useDiskCache) return null;

    try {
      const cacheKey = this._getCacheKey(sourceName, targetName);
      const data = await Storage.getSetting(`vocab_mapping_${cacheKey}`);
      if (data) {
        return VocabularyMapping.fromJSON(data);
      }
    } catch (e) {
      console.warn('Failed to load cached mapping:', e);
    }
    return null;
  }

  /**
   * Save mapping to IndexedDB cache
   */
  async _saveMappingToCache(sourceName, targetName, mapping) {
    if (!this.useDiskCache) return;

    try {
      const cacheKey = this._getCacheKey(sourceName, targetName);
      await Storage.setSetting(`vocab_mapping_${cacheKey}`, mapping.toJSON());
    } catch (e) {
      console.warn('Failed to cache vocabulary mapping:', e);
    }
  }

  /**
   * Create mapping between two tokenizers' vocabularies
   */
  async createMapping(sourceTokenizer, targetTokenizer, sourceName = 'source', targetName = 'target') {
    const cacheKey = `${sourceName}::${targetName}`;

    // Check in-memory cache
    if (this.mappingsCache.has(cacheKey)) {
      return this.mappingsCache.get(cacheKey);
    }

    // Check disk cache
    const diskCached = await this._loadCachedMapping(sourceName, targetName);
    if (diskCached) {
      this.mappingsCache.set(cacheKey, diskCached);
      if (this.verbose) {
        console.log(`Loaded vocabulary mapping from cache: ${sourceName} -> ${targetName}`);
      }
      return diskCached;
    }

    if (this.verbose) {
      console.log(`Creating vocabulary mapping: ${sourceName} -> ${targetName}`);
    }

    // Extract vocabularies
    const sourceVocab = this._extractVocabulary(sourceTokenizer);
    const targetVocab = this._extractVocabulary(targetTokenizer);

    // Find common tokens
    const commonTokensStr = new Set();
    for (const token of sourceVocab.keys()) {
      if (targetVocab.has(token)) {
        commonTokensStr.add(token);
      }
    }

    // Create bidirectional mappings
    const sourceToTarget = new Map();
    const targetToSource = new Map();
    const commonTokenIds = new Set();

    for (const tokenStr of commonTokensStr) {
      const sourceId = sourceVocab.get(tokenStr);
      const targetId = targetVocab.get(tokenStr);
      sourceToTarget.set(sourceId, targetId);
      targetToSource.set(targetId, sourceId);
      commonTokenIds.add(sourceId);
    }

    // Find unique tokens
    const sourceOnly = new Set();
    const targetOnly = new Set();

    for (const id of sourceVocab.values()) {
      if (!sourceToTarget.has(id)) {
        sourceOnly.add(id);
      }
    }

    for (const id of targetVocab.values()) {
      if (!targetToSource.has(id)) {
        targetOnly.add(id);
      }
    }

    // Compute quality metrics
    const quality = this._computeQualityMetrics(sourceVocab, targetVocab, commonTokensStr);

    const mapping = new VocabularyMapping({
      sourceToTarget,
      targetToSource,
      commonTokens: commonTokenIds,
      sourceOnly,
      targetOnly,
      overlapRatio: quality.overlapRatio,
      quality
    });

    // Cache mapping
    this.mappingsCache.set(cacheKey, mapping);
    await this._saveMappingToCache(sourceName, targetName, mapping);

    if (this.verbose) {
      console.log(`  Common tokens: ${quality.commonTokenCount}`);
      console.log(`  Source-only tokens: ${sourceOnly.size}`);
      console.log(`  Target-only tokens: ${targetOnly.size}`);
      console.log(`  Overlap ratio: ${(quality.overlapRatio * 100).toFixed(1)}%`);
      console.log(`  Quality: ${quality.qualityLevel} (${quality.overallScore.toFixed(2)})`);
    }

    return mapping;
  }

  /**
   * Translate logits from source to target vocabulary
   */
  translateLogits(logits, mapping, options = {}) {
    const {
      strategy = 'intersection',
      temperature = 1.0,
      topK = null,
      topP = null
    } = options;

    if (strategy === 'intersection') {
      return this._translateIntersection(logits, mapping, temperature, topK, topP);
    } else if (strategy === 'projection') {
      return this._translateProjection(logits, mapping, temperature);
    } else {
      return logits;
    }
  }

  /**
   * Translate using only intersection of vocabularies
   */
  _translateIntersection(logits, mapping, temperature, topK, topP) {
    // Apply temperature
    let scaledLogits = logits;
    if (temperature !== 1.0) {
      scaledLogits = logits.map(l => l / temperature);
    }

    // Convert to probabilities
    let probs = MathUtils.softmax(scaledLogits);

    // Filter to common tokens only
    const filteredProbs = new Float32Array(probs.length).fill(0);
    for (const sourceId of mapping.commonTokens) {
      if (sourceId < probs.length) {
        filteredProbs[sourceId] = probs[sourceId];
      }
    }

    // Apply top-k filtering
    if (topK !== null && topK > 0) {
      this._applyTopKFiltering(filteredProbs, topK);
    }

    // Apply top-p filtering
    if (topP !== null && topP > 0 && topP < 1) {
      this._applyTopPFiltering(filteredProbs, topP);
    }

    // Renormalize
    const sum = filteredProbs.reduce((a, b) => a + b, 0);
    if (sum > 0) {
      for (let i = 0; i < filteredProbs.length; i++) {
        filteredProbs[i] /= sum;
      }
    }

    // Map to target vocabulary
    let targetSize = 0;
    for (const targetId of mapping.targetToSource.keys()) {
      targetSize = Math.max(targetSize, targetId + 1);
    }
    if (targetSize === 0) targetSize = probs.length;

    const targetProbs = new Float32Array(targetSize).fill(0);

    for (const [sourceId, targetId] of mapping.sourceToTarget) {
      if (sourceId < filteredProbs.length && targetId < targetSize) {
        targetProbs[targetId] = filteredProbs[sourceId];
      }
    }

    // Convert back to logits
    const targetLogits = new Float32Array(targetSize);
    for (let i = 0; i < targetSize; i++) {
      targetLogits[i] = Math.log(targetProbs[i] + 1e-10);
    }

    return targetLogits;
  }

  /**
   * Translate using projection
   */
  _translateProjection(logits, mapping, temperature) {
    // Apply temperature
    let scaledLogits = logits;
    if (temperature !== 1.0) {
      scaledLogits = logits.map(l => l / temperature);
    }

    // Convert to probabilities
    const probs = MathUtils.softmax(scaledLogits);

    // Determine target size
    let targetSize = 0;
    for (const targetId of mapping.targetToSource.keys()) {
      targetSize = Math.max(targetSize, targetId + 1);
    }
    if (targetSize === 0) targetSize = probs.length;

    const targetProbs = new Float32Array(targetSize).fill(0);

    // Direct mappings
    for (const [sourceId, targetId] of mapping.sourceToTarget) {
      if (sourceId < probs.length && targetId < targetSize) {
        targetProbs[targetId] = probs[sourceId];
      }
    }

    // For unmapped source tokens, distribute to random unmapped target tokens
    const unmappedSourceList = Array.from(mapping.sourceOnly);
    const unmappedTargetList = Array.from(mapping.targetOnly);

    if (unmappedSourceList.length > 0 && unmappedTargetList.length > 0) {
      for (const sourceId of unmappedSourceList) {
        if (sourceId < probs.length && probs[sourceId] > 0.001) {
          // Distribute to up to 3 random target tokens
          const numTargets = Math.min(3, unmappedTargetList.length);
          for (let i = 0; i < numTargets; i++) {
            const targetId = unmappedTargetList[Math.floor(Math.random() * unmappedTargetList.length)];
            if (targetId < targetSize) {
              targetProbs[targetId] += probs[sourceId] / numTargets * 0.1;
            }
          }
        }
      }
    }

    // Normalize
    const sum = targetProbs.reduce((a, b) => a + b, 0);
    if (sum > 0) {
      for (let i = 0; i < targetProbs.length; i++) {
        targetProbs[i] /= sum;
      }
    }

    // Convert back to logits
    const targetLogits = new Float32Array(targetSize);
    for (let i = 0; i < targetSize; i++) {
      targetLogits[i] = Math.log(targetProbs[i] + 1e-10);
    }

    return targetLogits;
  }

  /**
   * Restrict logits to only allowed tokens
   */
  restrictVocabulary(logits, allowedTokens, maskValue = -1e9) {
    const result = new Float32Array(logits.length).fill(maskValue);
    for (const tokenId of allowedTokens) {
      if (tokenId < logits.length) {
        result[tokenId] = logits[tokenId];
      }
    }
    return result;
  }

  /**
   * Get intersection of tokens across multiple tokenizers
   */
  getIntersectionTokens(tokenizers, names = null) {
    if (!names) {
      names = tokenizers.map((_, i) => `model_${i}`);
    }

    const cacheKey = names.join('::');
    if (this.intersectionCache.has(cacheKey)) {
      return this.intersectionCache.get(cacheKey);
    }

    const vocabularies = tokenizers.map(t => this._extractVocabulary(t));

    // Find intersection
    let intersection = new Set(vocabularies[0].keys());
    for (let i = 1; i < vocabularies.length; i++) {
      const current = new Set();
      for (const token of intersection) {
        if (vocabularies[i].has(token)) {
          current.add(token);
        }
      }
      intersection = current;
    }

    this.intersectionCache.set(cacheKey, intersection);

    if (this.verbose) {
      console.log(`Vocabulary intersection across ${tokenizers.length} models: ${intersection.size} tokens`);
    }

    return intersection;
  }

  /**
   * Extract vocabulary from tokenizer
   */
  _extractVocabulary(tokenizer) {
    const vocab = new Map();

    // Method 1: getVocab() - Standard method
    if (typeof tokenizer.getVocab === 'function') {
      try {
        const v = tokenizer.getVocab();
        if (v && typeof v === 'object') {
          for (const [token, id] of Object.entries(v)) {
            vocab.set(token, id);
          }
          if (vocab.size > 0) return vocab;
        }
      } catch (e) { /* continue */ }
    }

    // Method 2: model.vocab property (Transformers.js)
    if (tokenizer.model?.vocab) {
      try {
        const v = tokenizer.model.vocab;
        if (v && typeof v === 'object') {
          for (const [token, id] of Object.entries(v)) {
            vocab.set(token, id);
          }
          if (vocab.size > 0) return vocab;
        }
      } catch (e) { /* continue */ }
    }

    // Method 3: vocabulary property
    if (tokenizer.vocabulary) {
      try {
        for (const [token, id] of Object.entries(tokenizer.vocabulary)) {
          vocab.set(token, id);
        }
        if (vocab.size > 0) return vocab;
      } catch (e) { /* continue */ }
    }

    // Method 4: Iterate through decode
    if (typeof tokenizer.decode === 'function') {
      try {
        const vocabSize = tokenizer.vocab_size || tokenizer.vocabSize || 50000;
        for (let i = 0; i < Math.min(vocabSize, 100000); i++) {
          try {
            const token = tokenizer.decode([i], { skip_special_tokens: false });
            if (token && token.length > 0) {
              vocab.set(token, i);
            }
          } catch (e) {
            break;
          }
        }
        if (vocab.size > 0) return vocab;
      } catch (e) { /* continue */ }
    }

    console.warn('Could not extract vocabulary from tokenizer');
    return vocab;
  }

  /**
   * Check if token is a special token
   */
  _isSpecialToken(token) {
    const specialPatterns = ['<', '>', '[', ']', '<|', '|>'];
    const specialNames = ['bos', 'eos', 'pad', 'unk', 'cls', 'sep', 'mask', 'endoftext'];

    const tokenLower = token.toLowerCase().trim();

    for (const pattern of specialPatterns) {
      if (token.startsWith(pattern) || token.endsWith(pattern.replace('<', '>'))) {
        return true;
      }
    }

    for (const name of specialNames) {
      if (tokenLower.includes(name)) {
        return true;
      }
    }

    return false;
  }

  /**
   * Check if token is a subword token
   */
  _isSubwordToken(token) {
    const subwordMarkers = ['##', '\u2581', '\u0120', '@@', '\u2582'];
    return subwordMarkers.some(marker => token.includes(marker));
  }

  /**
   * Compute quality metrics for vocabulary mapping
   */
  _computeQualityMetrics(sourceVocab, targetVocab, commonTokensStr) {
    // Basic overlap
    const allTokens = new Set([...sourceVocab.keys(), ...targetVocab.keys()]);
    const overlapRatio = allTokens.size > 0 ? commonTokensStr.size / allTokens.size : 0;

    // Coverage metrics
    const sourceCoverage = sourceVocab.size > 0 ? commonTokensStr.size / sourceVocab.size : 0;
    const targetCoverage = targetVocab.size > 0 ? commonTokensStr.size / targetVocab.size : 0;

    // Special token overlap
    const sourceSpecial = new Set([...sourceVocab.keys()].filter(t => this._isSpecialToken(t)));
    const targetSpecial = new Set([...targetVocab.keys()].filter(t => this._isSpecialToken(t)));
    const commonSpecial = new Set([...sourceSpecial].filter(t => targetSpecial.has(t)));
    const allSpecial = new Set([...sourceSpecial, ...targetSpecial]);
    const specialOverlap = allSpecial.size > 0 ? commonSpecial.size / allSpecial.size : 1.0;

    // Subword ratio
    const subwordCount = [...commonTokensStr].filter(t => this._isSubwordToken(t)).length;
    const subwordRatio = commonTokensStr.size > 0 ? subwordCount / commonTokensStr.size : 0;

    return new MappingQuality({
      overlapRatio,
      commonTokenCount: commonTokensStr.size,
      sourceCoverage,
      targetCoverage,
      specialTokenOverlap: specialOverlap,
      subwordRatio
    });
  }

  /**
   * Apply top-k filtering in-place
   */
  _applyTopKFiltering(probs, k) {
    if (k <= 0) return;

    // Find top-k indices
    const indexed = Array.from(probs).map((p, i) => ({ p, i }));
    indexed.sort((a, b) => b.p - a.p);
    const topKIndices = new Set(indexed.slice(0, k).map(x => x.i));

    // Zero out everything else
    for (let i = 0; i < probs.length; i++) {
      if (!topKIndices.has(i)) {
        probs[i] = 0;
      }
    }
  }

  /**
   * Apply top-p (nucleus) filtering in-place
   */
  _applyTopPFiltering(probs, p) {
    if (p <= 0 || p >= 1) return;

    // Sort by probability
    const indexed = Array.from(probs).map((prob, i) => ({ prob, i }));
    indexed.sort((a, b) => b.prob - a.prob);

    // Find cutoff
    let cumSum = 0;
    const keptIndices = new Set();
    for (const { prob, i } of indexed) {
      cumSum += prob;
      keptIndices.add(i);
      if (cumSum >= p) break;
    }

    // Zero out everything else
    for (let i = 0; i < probs.length; i++) {
      if (!keptIndices.has(i)) {
        probs[i] = 0;
      }
    }
  }
}

// Re-export for backwards compatibility
export { VocabularyAligner as VocabularyTranslator };
