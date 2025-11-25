/**
 * Mind Meld Engine for Web
 * Multi-model orchestration system
 *
 * Port of Python src/mind_meld/core/meld_engine.py
 */

import { MathUtils } from '../utils/math.js';
import { EventBus } from '../utils/event-bus.js';
import { MeldConfig, SwapStrategy, BlendMethod } from './config.js';
import { VocabularyAligner } from './vocabulary-translator.js';
import { LogitBlender, ContrastiveBlender, BlendingStrategy } from './logit-blender.js';
import { ABEEnsemble } from './abe-ensemble.js';
import { KVCache, KVCacheTranslator } from './kv-cache-handler.js';
import { ModelCompatibilityValidator } from './compatibility.js';
import { StatisticsTracker, computeAgreementScore, computeTokenMetrics } from './statistics.js';
import {
  createStrategy,
  FixedIntervalStrategy,
  ConfidenceBasedStrategy,
  PerplexityBasedStrategy
} from './swap-strategies.js';

/**
 * Mind Meld Engine - orchestrates multiple models for generation
 */
export class MeldEngine {
  constructor(engines, config = {}) {
    this.engines = engines;
    this.config = config instanceof MeldConfig ? config : new MeldConfig(config);

    // Active model tracking
    this.activeIndex = 0;
    this.tokenHistory = [];

    // Initialize components
    this.vocabAligner = new VocabularyAligner({ verbose: this.config.verbose });
    this.vocabMappings = new Map();

    // Blending
    this.blender = new LogitBlender({
      strategy: this.config.swapConfig.blendMethod,
      topK: this.config.topK
    });

    // ABE ensemble for agreement detection
    this.abeEnsemble = new ABEEnsemble();

    // Swap strategy
    this.swapStrategy = createStrategy(this.config.swapConfig);

    // KV cache handling
    this.kvCacheTranslator = new KVCacheTranslator(this.config.verbose);
    this.kvCaches = new Map();

    // Compatibility validation
    this.compatibilityValidator = new ModelCompatibilityValidator({
      verbose: this.config.verbose
    });

    // Statistics tracking
    this.statistics = new StatisticsTracker({
      verbose: this.config.verbose,
      modelCount: engines.length,
      modelIds: engines.map(e => e.modelId)
    });

    // State
    this._initialized = false;
    this._lastPredictions = null;
  }

  /**
   * Initialize the engine (validate compatibility, build vocab mappings)
   */
  async initialize() {
    if (this._initialized) return;

    if (this.config.verbose) {
      console.log('Initializing Mind Meld Engine...');
      console.log(`Models: ${this.engines.map(e => e.modelId).join(', ')}`);
    }

    // Validate model compatibility
    if (this.engines.length > 1) {
      const report = await this.compatibilityValidator.validateEnsemble(this.engines);

      if (!report.isCompatible) {
        console.warn('Model compatibility issues detected:', report.errors);
        if (!this.config.fallbackOnError) {
          throw new Error('Models are not compatible for ensemble');
        }
      }

      if (report.warnings.length > 0 && this.config.verbose) {
        console.warn('Compatibility warnings:', report.warnings);
      }

      // Build vocabulary mappings for each pair
      for (let i = 0; i < this.engines.length; i++) {
        for (let j = i + 1; j < this.engines.length; j++) {
          const mapping = await this.vocabAligner.createMapping(
            this.engines[i].tokenizer || this.engines[i],
            this.engines[j].tokenizer || this.engines[j],
            this.engines[i].modelId,
            this.engines[j].modelId
          );
          this.vocabMappings.set(`${i}-${j}`, mapping);
          this.vocabMappings.set(`${j}-${i}`, mapping);
        }
      }
    }

    this._initialized = true;

    if (this.config.verbose) {
      console.log('Mind Meld Engine initialized');
    }
  }

  /**
   * Generate a single token
   */
  async generateToken(context, options = {}) {
    if (!this._initialized) {
      await this.initialize();
    }

    const startTime = performance.now();

    // Get predictions from all models
    const predictions = await this._getPredictions(context, options);
    this._lastPredictions = predictions;

    // Determine final logits based on strategy
    let finalLogits;
    let wasSwap = false;
    let swapReason = null;
    let previousModel = this.activeIndex;

    const useBlending = this.config.swapConfig.strategy === SwapStrategy.WEIGHTED_BLEND ||
                        options.blend === true;

    if (useBlending && predictions.length > 1) {
      // Blend all model predictions
      const logitsList = predictions.map(p => p.logitsProcessed || p.logits);
      finalLogits = this.blender.blend(logitsList, { predictions });
    } else {
      // Use active model with potential swapping
      finalLogits = predictions[this.activeIndex].logitsProcessed ||
                   predictions[this.activeIndex].logits;

      const lastToken = this.tokenHistory[this.tokenHistory.length - 1]?.text || '';

      if (this.swapStrategy.shouldSwap(lastToken, predictions, this.activeIndex)) {
        previousModel = this.activeIndex;
        const newIndex = this.swapStrategy.selectNext(predictions, this.activeIndex);

        if (newIndex !== this.activeIndex) {
          wasSwap = true;
          swapReason = this.swapStrategy.lastReason;

          // Emit swap event
          EventBus.emit('meld:swap', {
            from: this.activeIndex,
            to: newIndex,
            reason: swapReason,
            tokenIndex: this.tokenHistory.length
          });

          // Handle KV cache bridging if enabled
          if (this.config.swapConfig.swapComponents.includes('kv_cache')) {
            await this._bridgeKVCache(this.activeIndex, newIndex);
          }

          this.activeIndex = newIndex;
          finalLogits = predictions[this.activeIndex].logitsProcessed ||
                       predictions[this.activeIndex].logits;
        }
      }
    }

    // Apply temperature
    if (this.config.temperature !== 1.0) {
      finalLogits = finalLogits.map(l => l / this.config.temperature);
    }

    // Sample token
    const probs = MathUtils.softmax(finalLogits);
    const tokenId = this._sampleToken(probs, options);
    const tokenText = this.engines[this.activeIndex].getTokenText(tokenId);

    // Calculate metrics
    const metrics = computeTokenMetrics(predictions[this.activeIndex], this.activeIndex);
    const agreementScore = predictions.length > 1 ? computeAgreementScore(predictions) : 1.0;

    // Record to history and statistics
    const tokenEntry = {
      id: tokenId,
      text: tokenText,
      activeModel: this.activeIndex,
      timestamp: Date.now()
    };
    this.tokenHistory.push(tokenEntry);

    const predictionTimeMs = performance.now() - startTime;

    this.statistics.recordToken({
      tokenId,
      tokenText,
      activeModelIndex: this.activeIndex,
      wasSwap,
      swapReason,
      previousModel: wasSwap ? previousModel : null,
      confidence: metrics.confidence,
      entropy: metrics.entropy,
      perplexity: metrics.perplexity,
      allModelConfidences: predictions.map(p => {
        const probs = MathUtils.softmax(p.logitsProcessed || p.logits || []);
        return Math.max(...probs);
      }),
      agreementScore,
      blendWeights: this.blender.getLastWeights(),
      predictionTimeMs
    });

    // Emit token event
    EventBus.emit('meld:token', {
      tokenId,
      tokenText,
      activeModel: this.activeIndex,
      modelId: this.engines[this.activeIndex].modelId,
      wasSwap,
      swapReason,
      metrics
    });

    return {
      tokenId,
      tokenText,
      activeModel: this.activeIndex,
      modelId: this.engines[this.activeIndex].modelId,
      wasSwap,
      swapReason,
      metrics,
      agreementScore,
      predictions
    };
  }

  /**
   * Generate multiple tokens
   */
  async generate(context, maxTokens = null, options = {}) {
    const numTokens = maxTokens ?? this.config.maxTokens;
    const tokens = [];
    let currentContext = context;

    for (let i = 0; i < numTokens; i++) {
      const result = await this.generateToken(currentContext, options);
      tokens.push(result);
      currentContext += result.tokenText;

      // Check for EOS
      if (this._isEOS(result.tokenId)) {
        break;
      }

      // Emit progress
      EventBus.emit('meld:progress', {
        tokensGenerated: i + 1,
        maxTokens: numTokens,
        currentText: currentContext
      });
    }

    return {
      tokens,
      text: currentContext,
      statistics: this.statistics.getStats()
    };
  }

  /**
   * Get predictions from all models
   */
  async _getPredictions(context, options = {}) {
    const samplingConfig = {
      temperature: options.temperature ?? this.config.temperature,
      topK: options.topK ?? this.config.topK,
      topP: options.topP ?? this.config.topP
    };

    // Run predictions in parallel
    const predictions = await Promise.all(
      this.engines.map(async (engine, idx) => {
        try {
          const inputIds = engine.encode(context);
          const prediction = await engine.predictNext(inputIds, samplingConfig);
          return {
            ...prediction,
            modelIndex: idx,
            modelId: engine.modelId
          };
        } catch (error) {
          console.error(`Prediction error from model ${idx}:`, error);
          return {
            logits: new Float32Array(engine.getVocabularySize()).fill(-Infinity),
            logitsProcessed: new Float32Array(engine.getVocabularySize()).fill(-Infinity),
            modelIndex: idx,
            modelId: engine.modelId,
            error: error.message
          };
        }
      })
    );

    return predictions;
  }

  /**
   * Bridge KV cache between models during swap
   */
  async _bridgeKVCache(fromIndex, toIndex) {
    // Get KV cache from source model if available
    const fromEngine = this.engines[fromIndex];
    const toEngine = this.engines[toIndex];

    if (!fromEngine.getKVCache || !toEngine.setKVCache) {
      return; // KV cache not supported
    }

    try {
      const sourceCache = await fromEngine.getKVCache();
      if (!sourceCache) return;

      // Check if we can directly share
      const fromConfig = fromEngine.config || fromEngine.model?.config;
      const toConfig = toEngine.config || toEngine.model?.config;

      if (fromConfig && toConfig) {
        const kvCache = new KVCache(sourceCache, fromConfig);

        if (kvCache.canResume(toConfig, this.tokenHistory.length)) {
          // Direct transfer
          const translated = this.kvCacheTranslator.translate(kvCache, toConfig);
          if (translated) {
            await toEngine.setKVCache(translated.toModelFormat());
          }
        } else if (this.config.verbose) {
          console.log('KV cache incompatible, starting fresh');
        }
      }
    } catch (error) {
      if (this.config.verbose) {
        console.warn('KV cache bridging failed:', error.message);
      }
    }
  }

  /**
   * Sample a token from probability distribution
   */
  _sampleToken(probs, options = {}) {
    const topK = options.topK ?? this.config.topK;
    const topP = options.topP ?? this.config.topP;

    // Apply top-k filtering
    let filteredProbs = [...probs];
    if (topK > 0 && topK < probs.length) {
      const indexed = filteredProbs.map((p, i) => ({ p, i }));
      indexed.sort((a, b) => b.p - a.p);
      const threshold = indexed[topK - 1].p;
      filteredProbs = filteredProbs.map(p => p >= threshold ? p : 0);
    }

    // Apply top-p filtering
    if (topP > 0 && topP < 1) {
      const indexed = filteredProbs.map((p, i) => ({ p, i }));
      indexed.sort((a, b) => b.p - a.p);
      let cumSum = 0;
      for (const { p, i } of indexed) {
        cumSum += p;
        if (cumSum > topP) {
          filteredProbs[i] = 0;
        }
      }
    }

    // Renormalize
    const sum = filteredProbs.reduce((a, b) => a + b, 0);
    if (sum > 0) {
      filteredProbs = filteredProbs.map(p => p / sum);
    }

    // Sample
    const r = Math.random();
    let cumulative = 0;
    for (let i = 0; i < filteredProbs.length; i++) {
      cumulative += filteredProbs[i];
      if (r < cumulative) {
        return i;
      }
    }

    // Fallback to argmax
    return MathUtils.argmax(probs);
  }

  /**
   * Check if token is EOS
   */
  _isEOS(tokenId) {
    const engine = this.engines[this.activeIndex];
    return engine.isSpecialToken?.(tokenId) ||
           engine.tokenizer?.eos_token_id === tokenId;
  }

  /**
   * Find agreement using ABE ensemble
   */
  findAgreement() {
    if (!this._lastPredictions || this._lastPredictions.length < 2) {
      return null;
    }
    return this.abeEnsemble.findAgreement(this._lastPredictions);
  }

  /**
   * Get current statistics
   */
  getStatistics() {
    return this.statistics.getStats();
  }

  /**
   * Get detailed statistics export
   */
  exportStatistics() {
    return this.statistics.export();
  }

  /**
   * Reset state for new generation
   */
  reset() {
    this.activeIndex = 0;
    this.tokenHistory = [];
    this._lastPredictions = null;
    this.kvCaches.clear();
    this.statistics.reset();
    this.blender.reset();

    if (typeof this.swapStrategy.reset === 'function') {
      this.swapStrategy.reset();
    }
  }

  /**
   * Set active model manually
   */
  setActiveModel(index) {
    if (index >= 0 && index < this.engines.length) {
      const previous = this.activeIndex;
      this.activeIndex = index;

      EventBus.emit('meld:swap', {
        from: previous,
        to: index,
        reason: 'Manual selection',
        tokenIndex: this.tokenHistory.length
      });
    }
  }

  /**
   * Get model information
   */
  getModelInfo() {
    return this.engines.map((engine, idx) => ({
      index: idx,
      modelId: engine.modelId,
      isActive: idx === this.activeIndex,
      vocabSize: engine.getVocabularySize?.() || 0
    }));
  }
}

// Export for convenience
export { MeldConfig, createStrategy };
