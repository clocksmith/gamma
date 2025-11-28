import { AutoTokenizer, AutoModelForCausalLM, env, Tensor } from '@huggingface/transformers';
import { EngineInterface } from '../core/engine-interface.js';
import { SamplingUtils } from '../core/sampling-utils.js';
import { EventBus } from '../utils/event-bus.js';

env.allowLocalModels = false;
env.useBrowserCache = true;

export class TransformersEngine extends EngineInterface {
  constructor(modelId, config) {
    super(modelId, config);
    this.tokenizer = null;
    this.model = null;
    this.device = 'webgpu';
  }

  async load() {
    try {
      // Check WebGPU availability first
      if (this.device === 'webgpu') {
        const webgpuAvailable = await this._checkWebGPUAvailability();
        if (!webgpuAvailable) {
          console.warn('WebGPU not available, using WASM instead');
          this.device = 'wasm';
        } else {
          console.log('WebGPU is available and will be used for acceleration');
        }
      }

      this.tokenizer = await AutoTokenizer.from_pretrained(this.modelId, {
        progress_callback: (data) => this._emitProgress('tokenizer', data)
      });

      this.model = await AutoModelForCausalLM.from_pretrained(this.modelId, {
        dtype: this.config.dtype || 'q4',
        device: this.device,
        progress_callback: (data) => this._emitProgress('model', data)
      });

      this.ready = true;
      console.log(`Engine loaded: ${this.modelId} on ${this.device}`);
    } catch (err) {
      console.error('Failed to load model:', err);
      if (this.device === 'webgpu') {
        console.warn('WebGPU failed, falling back to WASM...');
        this.device = 'wasm';
        await this.load();
      } else {
        throw err;
      }
    }
  }

  async _checkWebGPUAvailability() {
    if (!navigator.gpu) {
      console.log('WebGPU API not available in this browser');
      return false;
    }

    try {
      const adapter = await navigator.gpu.requestAdapter();
      if (!adapter) {
        console.log('No WebGPU adapter found');
        return false;
      }

      // Log GPU info
      const info = await adapter.requestAdapterInfo();
      console.log('WebGPU Adapter:', {
        vendor: info.vendor || 'unknown',
        architecture: info.architecture || 'unknown',
        device: info.device || 'unknown',
        description: info.description || 'unknown'
      });

      return true;
    } catch (err) {
      console.error('WebGPU check failed:', err);
      return false;
    }
  }

  _emitProgress(type, data) {
    // Enhanced progress reporting with stages
    const stage = this._getLoadingStage(type, data);
    EventBus.emit('model:progress', {
      type,
      stage,
      stageLabel: this._getStageLabel(stage),
      ...data
    });
  }

  _getLoadingStage(type, data) {
    if (type === 'tokenizer') {
      if (data.status === 'initiate') return 'tokenizer_download';
      if (data.status === 'progress') return 'tokenizer_download';
      if (data.status === 'done') return 'tokenizer_ready';
    }
    if (type === 'model') {
      if (data.status === 'initiate') return 'model_download';
      if (data.status === 'progress') return 'model_download';
      if (data.status === 'done') return 'model_compile';
    }
    return 'unknown';
  }

  _getStageLabel(stage) {
    const labels = {
      'tokenizer_download': 'Downloading tokenizer...',
      'tokenizer_ready': 'Tokenizer ready',
      'model_download': 'Downloading model weights...',
      'model_compile': 'Compiling model for WebGPU/WASM...',
      'ready': 'Model ready!',
      'unknown': 'Loading...'
    };
    return labels[stage] || labels['unknown'];
  }

  encode(text) {
    if (!this.tokenizer) throw new Error('Tokenizer not loaded');
    return this.tokenizer(text, { return_tensor: false }).input_ids;
  }

  decode(tokenIds) {
    if (!this.tokenizer) throw new Error('Tokenizer not loaded');
    return this.tokenizer.decode(tokenIds, { skip_special_tokens: true });
  }

  async predictNext(inputIds, { temperature, topK, topP }) {
    if (!this.model) throw new Error('Model not loaded');

    // Use forward pass to get logits directly instead of generate()
    // This avoids issues with output_scores in some model configurations

    // Convert inputIds to tensor if needed
    let inputArray = Array.isArray(inputIds) ? inputIds : Array.from(inputIds);
    const seqLength = inputArray.length;

    const inputTensor = new Tensor('int64', BigInt64Array.from(inputArray.map(BigInt)), [1, seqLength]);

    // Create attention mask (all 1s for unmasked)
    const attentionMask = new Tensor('int64', BigInt64Array.from(Array(seqLength).fill(1n)), [1, seqLength]);

    // Create position ids (0, 1, 2, ...)
    const positionIds = new Tensor('int64', BigInt64Array.from(Array.from({length: seqLength}, (_, i) => BigInt(i))), [1, seqLength]);

    const output = await this.model({
      input_ids: inputTensor,
      attention_mask: attentionMask,
      position_ids: positionIds,
      output_attentions: true
    });

    // Get logits from the last position
    const logits = output.logits;
    const vocabSize = logits.dims[logits.dims.length - 1];
    const seqLen = logits.dims[1];

    // Extract logits for the last token position
    const startIdx = (seqLen - 1) * vocabSize;
    const logitsRaw = logits.data.slice(startIdx, startIdx + vocabSize);

    // Process attention weights if available
    console.log('output.attentions:', output.attentions);
    const attentionData = this._processAttention(output.attentions, seqLen);
    console.log('attentionData:', attentionData);

    const pipelineResult = SamplingUtils.processLogitsPipeline(logitsRaw, {
      temperature, topK, topP
    });

    const topTokens = this._getTopTokens(pipelineResult.probs, 10);

    return {
      logitsRaw,
      probabilities: pipelineResult.probs,
      stages: pipelineResult.stages,
      topTokens,
      attention: attentionData
    };
  }

  _processAttention(attentions, seqLen) {
    if (!attentions || attentions.length === 0) return null;

    // Get the last layer's attention
    const lastLayer = attentions[attentions.length - 1];
    if (!lastLayer || !lastLayer.dims) return null;

    // Attention shape: [batch, num_heads, seq_len, seq_len]
    const numHeads = lastLayer.dims[1];
    const data = lastLayer.data;

    const averagedAttention = new Float32Array(seqLen);

    // Average attention across all heads for the last token position
    for (let s = 0; s < seqLen; s++) {
      let sum = 0;
      for (let h = 0; h < numHeads; h++) {
        // Index into [batch=0, head=h, query=last, key=s]
        const idx = (h * seqLen * seqLen) + ((seqLen - 1) * seqLen) + s;
        sum += data[idx];
      }
      averagedAttention[s] = sum / numHeads;
    }

    return Array.from(averagedAttention);
  }

  _getTopTokens(probs, k) {
    const indexed = [];
    for (let i = 0; i < probs.length; i++) {
      indexed.push({ prob: probs[i], id: i });
    }
    indexed.sort((a, b) => b.prob - a.prob);
    
    return indexed.slice(0, k).map(item => ({
      id: item.id,
      prob: item.prob,
      text: this.tokenizer.decode([item.id])
    }));
  }

  getVocabularySize() {
    return this.model ? this.model.config.vocab_size : 0;
  }

  getTokenText(tokenId) {
    return this.tokenizer ? this.tokenizer.decode([tokenId]) : '';
  }

  isSpecialToken(tokenId) {
    if (!this.tokenizer) return false;
    return false; 
  }
}