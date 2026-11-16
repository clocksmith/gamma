/**
 * Configuration classes for Mind Meld system
 * Port of Python src/mind_meld/core/config.py
 */

// Swap strategy enumeration
export const SwapStrategy = Object.freeze({
  FIXED_INTERVAL: 'fixed_interval',
  PATTERN_BASED: 'pattern',
  CONFIDENCE_BASED: 'confidence',
  ROUND_ROBIN: 'round_robin',
  WEIGHTED_BLEND: 'weighted',
  RANDOM: 'random',
  ATTENTION_GUIDED: 'attention',
  PERPLEXITY_BASED: 'perplexity',
  SEMANTIC_SIMILARITY: 'semantic'
});

// Translation mode enumeration
export const TranslationMode = Object.freeze({
  DIRECT: 'direct',
  PROJECTION: 'projection',
  INTERSECTION: 'intersection',
  EMBEDDING_BRIDGE: 'embedding',
  LATENT_ALIGN: 'latent'
});

// Vocabulary strategy enumeration
export const VocabularyStrategy = Object.freeze({
  RESTRICT_TO_INTERSECTION: 'intersection',
  PROJECT_TO_TARGET: 'project',
  SEMANTIC_MAPPING: 'semantic',
  SUBWORD_DECOMPOSITION: 'subword',
  FALLBACK_TO_UNK: 'unk'
});

// Blending methods
export const BlendMethod = Object.freeze({
  WEIGHTED_AVERAGE: 'weighted_average',
  CONFIDENCE_WEIGHTED: 'confidence_weighted',
  ATTENTION_WEIGHTED: 'attention_weighted',
  DYNAMIC_WEIGHTED: 'dynamic_weighted',
  ENSEMBLE_VOTING: 'ensemble_voting',
  LEARNED: 'learned'
});

/**
 * Configuration for state translation between models
 */
export class TranslationConfig {
  constructor(options = {}) {
    this.mode = options.mode ?? TranslationMode.INTERSECTION;
    this.vocabularyStrategy = options.vocabularyStrategy ?? VocabularyStrategy.RESTRICT_TO_INTERSECTION;

    // Vocabulary handling
    this.useVocabularyCache = options.useVocabularyCache ?? true;
    this.minVocabOverlap = options.minVocabOverlap ?? 0.5;

    // Projection settings
    this.projectionDim = options.projectionDim ?? null;
    this.useLearnedProjections = options.useLearnedProjections ?? false;

    // Filtering and constraints
    this.preFilterTopK = options.preFilterTopK ?? null;
    this.postFilterTopK = options.postFilterTopK ?? 50;
    this.temperatureAdjustment = options.temperatureAdjustment ?? 1.0;

    // Cache management
    this.cacheTranslationMatrices = options.cacheTranslationMatrices ?? true;
    this.maxCacheSizeMB = options.maxCacheSizeMB ?? 512;
  }

  toJSON() {
    return {
      mode: this.mode,
      vocabularyStrategy: this.vocabularyStrategy,
      useVocabularyCache: this.useVocabularyCache,
      minVocabOverlap: this.minVocabOverlap,
      projectionDim: this.projectionDim,
      useLearnedProjections: this.useLearnedProjections,
      preFilterTopK: this.preFilterTopK,
      postFilterTopK: this.postFilterTopK,
      temperatureAdjustment: this.temperatureAdjustment,
      cacheTranslationMatrices: this.cacheTranslationMatrices,
      maxCacheSizeMB: this.maxCacheSizeMB
    };
  }

  static fromJSON(data) {
    return new TranslationConfig(data);
  }
}

/**
 * Configuration for state swapping
 */
export class SwapConfig {
  constructor(options = {}) {
    this.strategy = options.strategy ?? SwapStrategy.FIXED_INTERVAL;

    // Strategy-specific parameters
    this.interval = options.interval ?? 2;
    this.minConfidence = options.minConfidence ?? 0.7;
    this.perplexityThreshold = options.perplexityThreshold ?? 50.0;
    this.attentionThreshold = options.attentionThreshold ?? 0.8;

    // Blending configuration
    this.blendWeights = options.blendWeights ?? [];
    this.blendMethod = options.blendMethod ?? BlendMethod.WEIGHTED_AVERAGE;

    // Component selection
    this.swapComponents = options.swapComponents ?? ['kv_cache'];
    this.preserveAttentionPatterns = options.preserveAttentionPatterns ?? true;

    // Swap patterns
    this.pattern = options.pattern ?? 'punctuation';
    this.patternLookahead = options.patternLookahead ?? 1;
  }

  toJSON() {
    return {
      strategy: this.strategy,
      interval: this.interval,
      minConfidence: this.minConfidence,
      perplexityThreshold: this.perplexityThreshold,
      attentionThreshold: this.attentionThreshold,
      blendWeights: this.blendWeights,
      blendMethod: this.blendMethod,
      swapComponents: this.swapComponents,
      preserveAttentionPatterns: this.preserveAttentionPatterns,
      pattern: this.pattern,
      patternLookahead: this.patternLookahead
    };
  }

  static fromJSON(data) {
    return new SwapConfig(data);
  }
}

/**
 * Configuration for bridging between model states
 */
export class BridgeConfig {
  constructor(options = {}) {
    // Context bridging
    this.contextWindowAlignment = options.contextWindowAlignment ?? 'truncate';
    this.maxContextLength = options.maxContextLength ?? null;

    // Attention bridging
    this.attentionHeadMapping = options.attentionHeadMapping ?? 'average';
    this.preserveCausalMask = options.preserveCausalMask ?? true;

    // KV cache bridging
    this.kvProjectionMethod = options.kvProjectionMethod ?? 'linear';
    this.kvDimensionMatching = options.kvDimensionMatching ?? 'projection';

    // Hidden state bridging
    this.hiddenProjectionLayers = options.hiddenProjectionLayers ?? 1;
    this.hiddenActivation = options.hiddenActivation ?? 'gelu';
    this.useResidualConnections = options.useResidualConnections ?? true;
  }

  toJSON() {
    return {
      contextWindowAlignment: this.contextWindowAlignment,
      maxContextLength: this.maxContextLength,
      attentionHeadMapping: this.attentionHeadMapping,
      preserveCausalMask: this.preserveCausalMask,
      kvProjectionMethod: this.kvProjectionMethod,
      kvDimensionMatching: this.kvDimensionMatching,
      hiddenProjectionLayers: this.hiddenProjectionLayers,
      hiddenActivation: this.hiddenActivation,
      useResidualConnections: this.useResidualConnections
    };
  }

  static fromJSON(data) {
    return new BridgeConfig(data);
  }
}

/**
 * Main configuration for Mind Meld system
 */
export class MeldConfig {
  constructor(options = {}) {
    // Core configurations
    this.swapConfig = options.swapConfig instanceof SwapConfig
      ? options.swapConfig
      : new SwapConfig(options.swapConfig);
    this.translationConfig = options.translationConfig instanceof TranslationConfig
      ? options.translationConfig
      : new TranslationConfig(options.translationConfig);
    this.bridgeConfig = options.bridgeConfig instanceof BridgeConfig
      ? options.bridgeConfig
      : new BridgeConfig(options.bridgeConfig);

    // Model settings
    this.modelConfigs = options.modelConfigs ?? [];
    this.requireSameArchitecture = options.requireSameArchitecture ?? false;

    // Generation parameters
    this.maxTokens = options.maxTokens ?? 100;
    this.temperature = options.temperature ?? 1.0;
    this.topK = options.topK ?? 50;
    this.topP = options.topP ?? 0.95;
    this.repetitionPenalty = options.repetitionPenalty ?? 1.0;

    // Performance settings
    this.useGPU = options.useGPU ?? true;
    this.batchSize = options.batchSize ?? 1;
    this.prefetchSteps = options.prefetchSteps ?? 2;

    // Monitoring and debugging
    this.verbose = options.verbose ?? false;
    this.logSwaps = options.logSwaps ?? true;
    this.trackMetrics = options.trackMetrics ?? true;
    this.saveSnapshots = options.saveSnapshots ?? false;

    // Safety and validation
    this.validateOutputs = options.validateOutputs ?? true;
    this.maxRetries = options.maxRetries ?? 3;
    this.fallbackOnError = options.fallbackOnError ?? true;
    this.temperatureSync = options.temperatureSync ?? true;
  }

  /**
   * Validate configuration and return list of warnings
   */
  validate() {
    const warnings = [];

    if (this.translationConfig.minVocabOverlap < 0.3) {
      warnings.push('Very low vocabulary overlap threshold may cause issues');
    }

    if (this.swapConfig.strategy === SwapStrategy.WEIGHTED_BLEND) {
      if (!this.swapConfig.blendWeights || this.swapConfig.blendWeights.length === 0) {
        warnings.push('Weighted blend strategy requires blendWeights');
      }
    }

    if (this.translationConfig.mode === TranslationMode.PROJECTION) {
      if (!this.translationConfig.projectionDim) {
        warnings.push('Projection mode requires projectionDim to be set');
      }
    }

    return warnings;
  }

  toJSON() {
    return {
      swapConfig: this.swapConfig.toJSON(),
      translationConfig: this.translationConfig.toJSON(),
      bridgeConfig: this.bridgeConfig.toJSON(),
      modelConfigs: this.modelConfigs,
      requireSameArchitecture: this.requireSameArchitecture,
      maxTokens: this.maxTokens,
      temperature: this.temperature,
      topK: this.topK,
      topP: this.topP,
      repetitionPenalty: this.repetitionPenalty,
      useGPU: this.useGPU,
      batchSize: this.batchSize,
      prefetchSteps: this.prefetchSteps,
      verbose: this.verbose,
      logSwaps: this.logSwaps,
      trackMetrics: this.trackMetrics,
      saveSnapshots: this.saveSnapshots,
      validateOutputs: this.validateOutputs,
      maxRetries: this.maxRetries,
      fallbackOnError: this.fallbackOnError,
      temperatureSync: this.temperatureSync
    };
  }

  static fromJSON(data) {
    return new MeldConfig({
      ...data,
      swapConfig: SwapConfig.fromJSON(data.swapConfig || {}),
      translationConfig: TranslationConfig.fromJSON(data.translationConfig || {}),
      bridgeConfig: BridgeConfig.fromJSON(data.bridgeConfig || {})
    });
  }
}

// Preset configurations for common use cases
export const MeldPresets = {
  /**
   * Simple round-robin for similar models
   */
  roundRobin: () => new MeldConfig({
    swapConfig: new SwapConfig({
      strategy: SwapStrategy.ROUND_ROBIN,
      interval: 1
    })
  }),

  /**
   * Confidence-based swapping for diverse models
   */
  confidenceSwap: () => new MeldConfig({
    swapConfig: new SwapConfig({
      strategy: SwapStrategy.CONFIDENCE_BASED,
      minConfidence: 0.3
    })
  }),

  /**
   * Weighted blending for ensemble
   */
  ensemble: (weights = null) => new MeldConfig({
    swapConfig: new SwapConfig({
      strategy: SwapStrategy.WEIGHTED_BLEND,
      blendMethod: BlendMethod.CONFIDENCE_WEIGHTED,
      blendWeights: weights || []
    })
  }),

  /**
   * Perplexity-based for adaptive generation
   */
  perplexityAdaptive: () => new MeldConfig({
    swapConfig: new SwapConfig({
      strategy: SwapStrategy.PERPLEXITY_BASED,
      perplexityThreshold: 50.0
    })
  }),

  /**
   * Conservative settings for different vocabularies
   */
  crossVocabulary: () => new MeldConfig({
    translationConfig: new TranslationConfig({
      mode: TranslationMode.INTERSECTION,
      vocabularyStrategy: VocabularyStrategy.RESTRICT_TO_INTERSECTION,
      minVocabOverlap: 0.3,
      postFilterTopK: 100
    }),
    swapConfig: new SwapConfig({
      strategy: SwapStrategy.CONFIDENCE_BASED,
      minConfidence: 0.4
    })
  })
};
