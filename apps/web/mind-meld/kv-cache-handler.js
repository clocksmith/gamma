/**
 * KV Cache Handler for Mind Meld system
 * Port of Python src/mind_meld/bridges/kv_cache_handler.py
 *
 * Handles KV cache translation between different model architectures
 */

/**
 * Model architecture detection
 */
export const ModelArchitecture = Object.freeze({
  GEMMA: 'gemma',
  LLAMA: 'llama',
  QWEN: 'qwen',
  SMOLLM: 'smollm',
  UNKNOWN: 'unknown'
});

/**
 * Detect model architecture from config
 */
export function getModelArchitecture(config) {
  if (!config) return ModelArchitecture.UNKNOWN;

  // Check model name/type if available
  const modelType = config.model_type || config.modelType || '';
  const modelName = (config.name || config._name_or_path || '').toLowerCase();

  if (modelName.includes('gemma') || modelType === 'gemma') {
    return ModelArchitecture.GEMMA;
  }
  if (modelName.includes('llama') || modelType === 'llama') {
    return ModelArchitecture.LLAMA;
  }
  if (modelName.includes('qwen') || modelType === 'qwen2') {
    return ModelArchitecture.QWEN;
  }
  if (modelName.includes('smollm') || modelType === 'llama') {
    return ModelArchitecture.SMOLLM;
  }

  // Check for architecture-specific config properties
  if (config.sliding_window !== undefined) {
    return ModelArchitecture.GEMMA;
  }
  if (config.attention_bias !== undefined && config.group_query_attention !== undefined) {
    return ModelArchitecture.LLAMA;
  }

  return ModelArchitecture.UNKNOWN;
}

/**
 * Standardized KV Cache representation
 * Abstracts away model-specific cache formats
 */
export class KVCache {
  constructor(cache, modelConfig) {
    this.modelArch = getModelArchitecture(modelConfig);
    this.numLayers = modelConfig.num_hidden_layers || modelConfig.numHiddenLayers || 0;
    this.numHeads = modelConfig.num_attention_heads || modelConfig.numAttentionHeads || 0;
    const hiddenSize = modelConfig.hidden_size || modelConfig.hiddenSize || 0;
    this.headDim = hiddenSize > 0 && this.numHeads > 0 ? Math.floor(hiddenSize / this.numHeads) : 0;

    this._cacheMetadata = {};

    // Convert to standard format
    const { keys, values } = this._toStandardFormat(cache);
    this.keys = keys;
    this.values = values;

    // Calculate sequence length from shape
    this.sequenceLength = this.keys.length > 0 && this.keys[0].length > 2
      ? this.keys[0][0]?.length || 0
      : 0;
  }

  /**
   * Check if this cache can be reused for a target model
   * Similar to Ollama's CanResume
   */
  canResume(targetConfig, requiredLength) {
    const targetArch = getModelArchitecture(targetConfig);

    // Check architecture compatibility
    if (targetArch !== this.modelArch &&
        targetArch !== ModelArchitecture.UNKNOWN &&
        this.modelArch !== ModelArchitecture.UNKNOWN) {
      return false;
    }

    // Check dimensions
    const targetLayers = targetConfig.num_hidden_layers || targetConfig.numHiddenLayers;
    if (targetLayers !== this.numLayers) {
      return false;
    }

    const targetHeads = targetConfig.num_attention_heads || targetConfig.numAttentionHeads;
    if (targetHeads !== this.numHeads) {
      return false;
    }

    const targetHiddenSize = targetConfig.hidden_size || targetConfig.hiddenSize;
    const targetHeadDim = Math.floor(targetHiddenSize / targetHeads);
    if (targetHeadDim !== this.headDim) {
      return false;
    }

    // Check sequence length
    if (this.sequenceLength < requiredLength) {
      return false;
    }

    return true;
  }

  /**
   * Copy only the first N tokens from the cache
   * Similar to Ollama's CopyPrefix
   */
  copyPrefix(prefixLength) {
    if (prefixLength <= 0 || prefixLength > this.sequenceLength) {
      throw new Error(`Invalid prefixLength: ${prefixLength}`);
    }

    const newCache = new KVCache.__create();
    newCache.modelArch = this.modelArch;
    newCache.numLayers = this.numLayers;
    newCache.numHeads = this.numHeads;
    newCache.headDim = this.headDim;
    newCache._cacheMetadata = { ...this._cacheMetadata };

    // Truncate keys and values to prefix length
    newCache.keys = this.keys.map(layerKeys =>
      layerKeys.map(batch =>
        batch.slice(0, prefixLength)
      )
    );
    newCache.values = this.values.map(layerValues =>
      layerValues.map(batch =>
        batch.slice(0, prefixLength)
      )
    );
    newCache.sequenceLength = prefixLength;

    return newCache;
  }

  /**
   * Transfer only specific layers of the cache
   */
  selectiveLayers(layerIndices) {
    if (!layerIndices || layerIndices.length === 0) {
      throw new Error('Invalid layerIndices');
    }
    if (Math.max(...layerIndices) >= this.numLayers) {
      throw new Error(`Layer index out of bounds: max ${this.numLayers - 1}`);
    }

    const newCache = new KVCache.__create();
    newCache.modelArch = this.modelArch;
    newCache.numLayers = layerIndices.length;
    newCache.numHeads = this.numHeads;
    newCache.headDim = this.headDim;
    newCache._cacheMetadata = { ...this._cacheMetadata };

    // Select only specified layers
    newCache.keys = layerIndices.map(idx => this.keys[idx]);
    newCache.values = layerIndices.map(idx => this.values[idx]);
    newCache.sequenceLength = this.sequenceLength;

    return newCache;
  }

  /**
   * Convert model-specific cache to standard format
   * Standard format: [numLayers][batch][seqLen][numHeads][headDim]
   */
  _toStandardFormat(cache) {
    if (!cache) {
      return { keys: [], values: [] };
    }

    // Handle Transformers.js cache format
    if (cache.past_key_values || cache.pastKeyValues) {
      const pkv = cache.past_key_values || cache.pastKeyValues;
      return this._fromTransformersJSFormat(pkv);
    }

    // Handle array of [key, value] tuples (PyTorch-like)
    if (Array.isArray(cache) && cache.length > 0) {
      if (Array.isArray(cache[0]) && cache[0].length === 2) {
        return this._fromTupleFormat(cache);
      }
    }

    // Handle object with keys/values
    if (cache.keys && cache.values) {
      return {
        keys: this._ensureArray(cache.keys),
        values: this._ensureArray(cache.values)
      };
    }

    console.warn('Unknown cache format, returning empty');
    return { keys: [], values: [] };
  }

  /**
   * Convert from Transformers.js past_key_values format
   */
  _fromTransformersJSFormat(pkv) {
    const keys = [];
    const values = [];

    for (const layer of pkv) {
      if (layer.key && layer.value) {
        // ONNX tensor format
        keys.push(this._tensorToArray(layer.key));
        values.push(this._tensorToArray(layer.value));
      } else if (Array.isArray(layer) && layer.length === 2) {
        // Tuple format
        keys.push(this._tensorToArray(layer[0]));
        values.push(this._tensorToArray(layer[1]));
      }
    }

    return { keys, values };
  }

  /**
   * Convert from tuple format [[k, v], [k, v], ...]
   */
  _fromTupleFormat(cache) {
    const keys = [];
    const values = [];

    for (const [k, v] of cache) {
      keys.push(this._tensorToArray(k));
      values.push(this._tensorToArray(v));
    }

    return { keys, values };
  }

  /**
   * Convert tensor (ONNX/TypedArray) to nested array
   */
  _tensorToArray(tensor) {
    if (!tensor) return [];

    // Handle ONNX tensor
    if (tensor.data && tensor.dims) {
      return this._reshapeFlat(tensor.data, tensor.dims);
    }

    // Handle TypedArray
    if (ArrayBuffer.isView(tensor)) {
      return Array.from(tensor);
    }

    // Already an array
    if (Array.isArray(tensor)) {
      return tensor;
    }

    return [];
  }

  /**
   * Reshape flat array to nested array based on dimensions
   */
  _reshapeFlat(flat, dims) {
    if (dims.length === 1) {
      return Array.from(flat);
    }

    const result = [];
    const stride = dims.slice(1).reduce((a, b) => a * b, 1);

    for (let i = 0; i < dims[0]; i++) {
      const start = i * stride;
      const end = start + stride;
      const slice = flat.slice(start, end);
      result.push(this._reshapeFlat(slice, dims.slice(1)));
    }

    return result;
  }

  /**
   * Ensure value is an array
   */
  _ensureArray(val) {
    if (Array.isArray(val)) return val;
    if (ArrayBuffer.isView(val)) return Array.from(val);
    return [];
  }

  /**
   * Convert back to model-specific format
   */
  toModelFormat(targetArch = null) {
    const arch = targetArch || this.modelArch;

    // Default: return as Transformers.js compatible format
    return {
      past_key_values: this.keys.map((layerKeys, idx) => ({
        key: this._toFloat32Array(layerKeys),
        value: this._toFloat32Array(this.values[idx])
      }))
    };
  }

  /**
   * Convert nested array to Float32Array
   */
  _toFloat32Array(nested) {
    const flat = this._flatten(nested);
    return new Float32Array(flat);
  }

  /**
   * Flatten nested array
   */
  _flatten(arr) {
    if (!Array.isArray(arr)) return [arr];
    return arr.reduce((acc, val) => acc.concat(this._flatten(val)), []);
  }

  /**
   * Create empty cache instance (for internal use)
   */
  static __create() {
    const cache = Object.create(KVCache.prototype);
    cache.keys = [];
    cache.values = [];
    cache._cacheMetadata = {};
    return cache;
  }
}

/**
 * Abstract translation strategy
 */
class TranslationStrategy {
  translate(sourceCache, targetConfig) {
    throw new Error('Abstract method');
  }
}

/**
 * Direct translation for compatible architectures
 */
class DirectTranslation extends TranslationStrategy {
  translate(sourceCache, targetConfig) {
    // Same architecture, no transformation needed
    return sourceCache;
  }
}

/**
 * Projection-based translation for incompatible architectures
 */
class ProjectionTranslation extends TranslationStrategy {
  constructor() {
    super();
    this._projectionCache = new Map();
  }

  translate(sourceCache, targetConfig) {
    const targetHeads = targetConfig.num_attention_heads || targetConfig.numAttentionHeads;
    const targetHiddenSize = targetConfig.hidden_size || targetConfig.hiddenSize;
    const targetHeadDim = Math.floor(targetHiddenSize / targetHeads);
    const targetLayers = targetConfig.num_hidden_layers || targetConfig.numHiddenLayers;

    // Check layer compatibility
    if (sourceCache.numLayers !== targetLayers) {
      return this._handleLayerMismatch(sourceCache, targetConfig);
    }

    // Check if projection is needed
    if (sourceCache.headDim === targetHeadDim && sourceCache.numHeads === targetHeads) {
      return sourceCache;
    }

    // Project head dimensions
    if (sourceCache.headDim !== targetHeadDim) {
      const projection = this._getProjectionMatrix(sourceCache.headDim, targetHeadDim);
      sourceCache.keys = this._projectTensor(sourceCache.keys, projection);
      sourceCache.values = this._projectTensor(sourceCache.values, projection);
      sourceCache.headDim = targetHeadDim;
    }

    // Interpolate attention heads
    if (sourceCache.numHeads !== targetHeads) {
      sourceCache.keys = this._interpolateHeads(sourceCache.keys, sourceCache.numHeads, targetHeads);
      sourceCache.values = this._interpolateHeads(sourceCache.values, sourceCache.numHeads, targetHeads);
      sourceCache.numHeads = targetHeads;
    }

    return sourceCache;
  }

  _getProjectionMatrix(sourceDim, targetDim) {
    const cacheKey = `${sourceDim}->${targetDim}`;
    if (this._projectionCache.has(cacheKey)) {
      return this._projectionCache.get(cacheKey);
    }

    // Create orthogonal projection matrix
    let projection;
    if (sourceDim > targetDim) {
      // Dimensionality reduction
      projection = this._createOrthogonalMatrix(sourceDim, targetDim);
    } else {
      // Dimensionality expansion
      projection = this._createOrthogonalMatrix(targetDim, sourceDim);
      projection = this._transpose(projection);
    }

    this._projectionCache.set(cacheKey, projection);
    return projection;
  }

  _createOrthogonalMatrix(rows, cols) {
    // Simple random orthogonal-ish matrix
    const matrix = [];
    for (let i = 0; i < rows; i++) {
      const row = [];
      for (let j = 0; j < cols; j++) {
        row.push((Math.random() - 0.5) * 2 / Math.sqrt(rows));
      }
      matrix.push(row);
    }
    return matrix;
  }

  _transpose(matrix) {
    if (!matrix.length) return [];
    return matrix[0].map((_, i) => matrix.map(row => row[i]));
  }

  _projectTensor(tensor, projection) {
    // Apply projection to last dimension of each element
    return tensor.map(layer =>
      layer.map(batch =>
        batch.map(seq =>
          this._matmul(seq, projection)
        )
      )
    );
  }

  _matmul(vec, matrix) {
    // Vector-matrix multiplication
    return matrix[0].map((_, j) =>
      vec.reduce((sum, v, i) => sum + v * (matrix[i]?.[j] || 0), 0)
    );
  }

  _interpolateHeads(tensor, sourceHeads, targetHeads) {
    return tensor.map(layer =>
      layer.map(batch =>
        batch.map(seq => {
          if (sourceHeads > targetHeads) {
            // Reduce heads by averaging groups
            const ratio = Math.floor(sourceHeads / targetHeads);
            const result = [];
            for (let i = 0; i < targetHeads; i++) {
              const start = i * ratio;
              const end = Math.min(start + ratio, sourceHeads);
              const avg = seq.slice(start, end).reduce((a, b) => a + b, 0) / (end - start);
              result.push(avg);
            }
            return result;
          } else {
            // Expand heads by interpolation
            const result = [];
            for (let i = 0; i < targetHeads; i++) {
              const srcIdx = (i / targetHeads) * sourceHeads;
              const low = Math.floor(srcIdx);
              const high = Math.min(low + 1, sourceHeads - 1);
              const t = srcIdx - low;
              const interp = seq[low] * (1 - t) + seq[high] * t;
              result.push(interp);
            }
            return result;
          }
        })
      )
    );
  }

  _handleLayerMismatch(sourceCache, targetConfig) {
    const targetLayers = targetConfig.num_hidden_layers || targetConfig.numHiddenLayers;

    if (sourceCache.numLayers < targetLayers) {
      // Cannot expand layers
      return null;
    }

    // Select evenly-spaced layers
    const indices = [];
    for (let i = 0; i < targetLayers; i++) {
      indices.push(Math.floor((i / targetLayers) * sourceCache.numLayers));
    }

    return sourceCache.selectiveLayers(indices);
  }
}

/**
 * KV Cache Translator - manages translation between model caches
 */
export class KVCacheTranslator {
  constructor(verbose = false) {
    this.verbose = verbose;
    this._strategies = {
      direct: new DirectTranslation(),
      projection: new ProjectionTranslation()
    };
  }

  /**
   * Translate cache from source to target architecture
   */
  translate(sourceCache, targetConfig) {
    if (!(sourceCache instanceof KVCache)) {
      console.warn('Source cache must be a KVCache instance');
      return null;
    }

    const targetArch = getModelArchitecture(targetConfig);

    // Select strategy
    let strategy;
    if (sourceCache.modelArch === targetArch ||
        sourceCache.modelArch === ModelArchitecture.UNKNOWN ||
        targetArch === ModelArchitecture.UNKNOWN) {
      strategy = this._strategies.direct;
    } else {
      strategy = this._strategies.projection;
    }

    if (this.verbose) {
      console.log(`KV Cache translation: ${sourceCache.modelArch} -> ${targetArch}`);
      console.log(`Using strategy: ${strategy.constructor.name}`);
    }

    return strategy.translate(sourceCache, targetConfig);
  }

  /**
   * Check if cache can be shared between models
   */
  canShare(sourceCache, targetConfig, requiredLength = 0) {
    if (!(sourceCache instanceof KVCache)) {
      return false;
    }
    return sourceCache.canResume(targetConfig, requiredLength);
  }

  /**
   * Create a shareable prefix from cache
   */
  createSharedPrefix(sourceCache, prefixLength) {
    if (!(sourceCache instanceof KVCache)) {
      return null;
    }
    try {
      return sourceCache.copyPrefix(prefixLength);
    } catch (e) {
      console.warn('Failed to create shared prefix:', e.message);
      return null;
    }
  }
}
