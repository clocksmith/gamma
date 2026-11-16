/**
 * Model Compatibility Validator for Mind Meld system
 * Port of Python src/mind_meld/core/compatibility.py
 *
 * Pre-validates models before ensemble operations
 */

import { getModelArchitecture, ModelArchitecture } from './kv-cache-handler.js';

/**
 * Compatibility check results
 */
export class CompatibilityReport {
  constructor() {
    this.compatible = true;
    this.score = 1.0;
    this.warnings = [];
    this.errors = [];
    this.details = {};
  }

  addWarning(message) {
    this.warnings.push(message);
    this.score = Math.max(0, this.score - 0.1);
  }

  addError(message) {
    this.errors.push(message);
    this.compatible = false;
    this.score = 0;
  }

  get isCompatible() {
    return this.compatible && this.errors.length === 0;
  }

  get qualityLevel() {
    if (!this.compatible) return 'incompatible';
    if (this.score >= 0.9) return 'excellent';
    if (this.score >= 0.7) return 'good';
    if (this.score >= 0.5) return 'fair';
    return 'poor';
  }

  toJSON() {
    return {
      compatible: this.compatible,
      score: this.score,
      qualityLevel: this.qualityLevel,
      warnings: this.warnings,
      errors: this.errors,
      details: this.details
    };
  }
}

/**
 * Model Compatibility Validator
 * Pre-validates model ensemble feasibility
 */
export class ModelCompatibilityValidator {
  constructor(options = {}) {
    this.verbose = options.verbose ?? false;
    this.minVocabOverlap = options.minVocabOverlap ?? 0.3;
    this.maxLayerDiffRatio = options.maxLayerDiffRatio ?? 0.5;
  }

  /**
   * Validate compatibility between two models
   */
  async validatePair(engine1, engine2, vocabMapping = null) {
    const report = new CompatibilityReport();

    // Get model configs
    const config1 = this._getModelConfig(engine1);
    const config2 = this._getModelConfig(engine2);

    report.details.model1 = {
      id: engine1.modelId,
      architecture: getModelArchitecture(config1),
      config: this._summarizeConfig(config1)
    };

    report.details.model2 = {
      id: engine2.modelId,
      architecture: getModelArchitecture(config2),
      config: this._summarizeConfig(config2)
    };

    // Check architecture compatibility
    this._checkArchitecture(config1, config2, report);

    // Check vocabulary compatibility
    await this._checkVocabulary(engine1, engine2, vocabMapping, report);

    // Check layer compatibility
    this._checkLayers(config1, config2, report);

    // Check dimension compatibility
    this._checkDimensions(config1, config2, report);

    // Check context length compatibility
    this._checkContextLength(config1, config2, report);

    if (this.verbose) {
      console.log('Compatibility Report:', report.toJSON());
    }

    return report;
  }

  /**
   * Validate compatibility across multiple models
   */
  async validateEnsemble(engines, vocabMappings = null) {
    const reports = [];

    for (let i = 0; i < engines.length; i++) {
      for (let j = i + 1; j < engines.length; j++) {
        const mapping = vocabMappings?.[`${i}-${j}`] ?? null;
        const report = await this.validatePair(engines[i], engines[j], mapping);
        reports.push({
          pair: [i, j],
          modelIds: [engines[i].modelId, engines[j].modelId],
          report
        });
      }
    }

    // Aggregate results
    const aggregateReport = new CompatibilityReport();
    aggregateReport.details.pairReports = reports;

    const allCompatible = reports.every(r => r.report.isCompatible);
    const avgScore = reports.reduce((sum, r) => sum + r.report.score, 0) / reports.length;

    aggregateReport.compatible = allCompatible;
    aggregateReport.score = avgScore;

    // Collect all warnings and errors
    for (const r of reports) {
      for (const w of r.report.warnings) {
        aggregateReport.warnings.push(`[${r.modelIds.join(' <-> ')}] ${w}`);
      }
      for (const e of r.report.errors) {
        aggregateReport.errors.push(`[${r.modelIds.join(' <-> ')}] ${e}`);
      }
    }

    return aggregateReport;
  }

  /**
   * Get model configuration
   */
  _getModelConfig(engine) {
    // Try various ways to get config
    if (engine.config) return engine.config;
    if (engine.model?.config) return engine.model.config;
    if (engine.modelConfig) return engine.modelConfig;

    // Create minimal config from available info
    return {
      hidden_size: engine.hiddenSize || 0,
      num_hidden_layers: engine.numLayers || 0,
      num_attention_heads: engine.numHeads || 0,
      vocab_size: engine.getVocabularySize?.() || 0,
      max_position_embeddings: engine.maxContextLength || 2048
    };
  }

  /**
   * Summarize config for reporting
   */
  _summarizeConfig(config) {
    return {
      hiddenSize: config.hidden_size || config.hiddenSize || 0,
      numLayers: config.num_hidden_layers || config.numHiddenLayers || 0,
      numHeads: config.num_attention_heads || config.numAttentionHeads || 0,
      vocabSize: config.vocab_size || config.vocabSize || 0,
      maxContext: config.max_position_embeddings || config.maxPositionEmbeddings || 2048
    };
  }

  /**
   * Check architecture compatibility
   */
  _checkArchitecture(config1, config2, report) {
    const arch1 = getModelArchitecture(config1);
    const arch2 = getModelArchitecture(config2);

    report.details.architectures = { model1: arch1, model2: arch2 };

    if (arch1 === ModelArchitecture.UNKNOWN || arch2 === ModelArchitecture.UNKNOWN) {
      report.addWarning('One or more models have unknown architecture');
      return;
    }

    if (arch1 !== arch2) {
      report.addWarning(`Different architectures: ${arch1} vs ${arch2}. KV cache bridging may be lossy.`);
    }
  }

  /**
   * Check vocabulary compatibility
   */
  async _checkVocabulary(engine1, engine2, vocabMapping, report) {
    const vocabSize1 = engine1.getVocabularySize?.() || 0;
    const vocabSize2 = engine2.getVocabularySize?.() || 0;

    report.details.vocabulary = {
      size1: vocabSize1,
      size2: vocabSize2,
      sizeRatio: vocabSize1 > 0 && vocabSize2 > 0
        ? Math.min(vocabSize1, vocabSize2) / Math.max(vocabSize1, vocabSize2)
        : 0
    };

    if (vocabSize1 === 0 || vocabSize2 === 0) {
      report.addWarning('Could not determine vocabulary sizes');
      return;
    }

    // Check if we have a pre-computed mapping
    if (vocabMapping) {
      const overlap = vocabMapping.overlapRatio || vocabMapping.overlap || 0;
      report.details.vocabulary.overlapRatio = overlap;

      if (overlap < this.minVocabOverlap) {
        report.addError(`Vocabulary overlap (${(overlap * 100).toFixed(1)}%) below minimum threshold (${(this.minVocabOverlap * 100).toFixed(1)}%)`);
      } else if (overlap < 0.5) {
        report.addWarning(`Low vocabulary overlap: ${(overlap * 100).toFixed(1)}%`);
      }
    } else {
      // Estimate overlap from vocab sizes
      const sizeRatio = report.details.vocabulary.sizeRatio;
      if (sizeRatio < 0.5) {
        report.addWarning(`Large vocabulary size difference: ${vocabSize1} vs ${vocabSize2}`);
      }
    }
  }

  /**
   * Check layer compatibility
   */
  _checkLayers(config1, config2, report) {
    const layers1 = config1.num_hidden_layers || config1.numHiddenLayers || 0;
    const layers2 = config2.num_hidden_layers || config2.numHiddenLayers || 0;

    report.details.layers = { model1: layers1, model2: layers2 };

    if (layers1 === 0 || layers2 === 0) {
      report.addWarning('Could not determine layer counts');
      return;
    }

    const layerDiff = Math.abs(layers1 - layers2);
    const maxLayers = Math.max(layers1, layers2);
    const diffRatio = layerDiff / maxLayers;

    if (diffRatio > this.maxLayerDiffRatio) {
      report.addWarning(`Significant layer count difference: ${layers1} vs ${layers2}. State bridging may be lossy.`);
    }
  }

  /**
   * Check dimension compatibility
   */
  _checkDimensions(config1, config2, report) {
    const hidden1 = config1.hidden_size || config1.hiddenSize || 0;
    const hidden2 = config2.hidden_size || config2.hiddenSize || 0;
    const heads1 = config1.num_attention_heads || config1.numAttentionHeads || 0;
    const heads2 = config2.num_attention_heads || config2.numAttentionHeads || 0;

    report.details.dimensions = {
      hiddenSize: { model1: hidden1, model2: hidden2 },
      numHeads: { model1: heads1, model2: heads2 }
    };

    if (hidden1 > 0 && hidden2 > 0 && hidden1 !== hidden2) {
      report.addWarning(`Different hidden sizes: ${hidden1} vs ${hidden2}. Projection will be applied.`);
    }

    if (heads1 > 0 && heads2 > 0 && heads1 !== heads2) {
      report.addWarning(`Different attention head counts: ${heads1} vs ${heads2}. Head interpolation will be applied.`);
    }

    // Check head dimension
    if (hidden1 > 0 && heads1 > 0 && hidden2 > 0 && heads2 > 0) {
      const headDim1 = Math.floor(hidden1 / heads1);
      const headDim2 = Math.floor(hidden2 / heads2);

      if (headDim1 !== headDim2) {
        report.addWarning(`Different head dimensions: ${headDim1} vs ${headDim2}`);
      }

      report.details.dimensions.headDim = { model1: headDim1, model2: headDim2 };
    }
  }

  /**
   * Check context length compatibility
   */
  _checkContextLength(config1, config2, report) {
    const ctx1 = config1.max_position_embeddings || config1.maxPositionEmbeddings || 0;
    const ctx2 = config2.max_position_embeddings || config2.maxPositionEmbeddings || 0;

    report.details.contextLength = { model1: ctx1, model2: ctx2 };

    if (ctx1 > 0 && ctx2 > 0 && ctx1 !== ctx2) {
      const minCtx = Math.min(ctx1, ctx2);
      report.addWarning(`Different max context lengths: ${ctx1} vs ${ctx2}. Will be limited to ${minCtx}.`);
    }
  }

  /**
   * Quick compatibility check (returns boolean)
   */
  async quickCheck(engine1, engine2) {
    const report = await this.validatePair(engine1, engine2);
    return report.isCompatible;
  }

  /**
   * Get recommended configuration for model pair
   */
  async getRecommendedConfig(engine1, engine2, vocabMapping = null) {
    const report = await this.validatePair(engine1, engine2, vocabMapping);

    const config1 = this._getModelConfig(engine1);
    const config2 = this._getModelConfig(engine2);

    const ctx1 = config1.max_position_embeddings || config1.maxPositionEmbeddings || 2048;
    const ctx2 = config2.max_position_embeddings || config2.maxPositionEmbeddings || 2048;

    return {
      compatible: report.isCompatible,
      qualityLevel: report.qualityLevel,
      recommendations: {
        maxContextLength: Math.min(ctx1, ctx2),
        useKVCacheBridging: report.score >= 0.7,
        vocabularyStrategy: vocabMapping?.overlapRatio >= 0.6 ? 'projection' : 'intersection',
        blendingStrategy: report.score >= 0.8 ? 'confidence_weighted' : 'weighted_average',
        swapStrategy: report.score >= 0.7 ? 'confidence' : 'fixed_interval'
      },
      report
    };
  }
}
