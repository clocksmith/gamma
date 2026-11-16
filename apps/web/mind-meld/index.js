/**
 * Mind Meld - Multi-Model Orchestration System for Web
 *
 * This module provides the web implementation of the Mind Meld system,
 * enabling ensemble generation with multiple language models.
 */

// Core engine
export { MeldEngine, MeldConfig, createStrategy } from './meld-engine.js';

// Configuration
export {
  SwapStrategy,
  TranslationMode,
  VocabularyStrategy,
  BlendMethod,
  TranslationConfig,
  SwapConfig,
  BridgeConfig,
  MeldPresets
} from './config.js';

// Swap strategies
export {
  SwapStrategyBase,
  FixedIntervalStrategy,
  RoundRobinStrategy,
  ConfidenceBasedStrategy,
  PerplexityBasedStrategy,
  PatternBasedStrategy,
  RandomStrategy,
  AttentionGuidedStrategy,
  CompositeStrategy
} from './swap-strategies.js';

// Blending
export {
  LogitBlender,
  ContrastiveBlender,
  BlendingStrategy
} from './logit-blender.js';

// Vocabulary handling
export {
  VocabularyAligner,
  VocabularyTranslator,
  VocabularyMapping,
  MappingQuality
} from './vocabulary-translator.js';

// KV Cache
export {
  KVCache,
  KVCacheTranslator,
  ModelArchitecture,
  getModelArchitecture
} from './kv-cache-handler.js';

// Model compatibility
export {
  ModelCompatibilityValidator,
  CompatibilityReport
} from './compatibility.js';

// ABE Ensemble
export {
  ABEEnsemble,
  AgreementCandidate
} from './abe-ensemble.js';

// Statistics
export {
  StatisticsTracker,
  TokenStats,
  SwapEvent,
  computeAgreementScore,
  computeTokenMetrics
} from './statistics.js';
