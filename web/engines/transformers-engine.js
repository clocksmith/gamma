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
      this.tokenizer = await AutoTokenizer.from_pretrained(this.modelId, {
        progress_callback: (data) => this._emitProgress('tokenizer', data)
      });

      this.model = await AutoModelForCausalLM.from_pretrained(this.modelId, {
        dtype: this.config.dtype || 'q4',
        device: this.device,
        progress_callback: (data) => this._emitProgress('model', data)
      });

      this.ready = true;
      console.log(`Engine loaded: ${this.modelId}`);
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

  _emitProgress(type, data) {
    EventBus.emit('model:progress', { type, ...data });
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
      position_ids: positionIds
    });

    // Get logits from the last position
    const logits = output.logits;
    const vocabSize = logits.dims[logits.dims.length - 1];
    const seqLen = logits.dims[1];

    // Extract logits for the last token position
    const startIdx = (seqLen - 1) * vocabSize;
    const logitsRaw = logits.data.slice(startIdx, startIdx + vocabSize);
    const attentionData = null;

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

  _processAttention(attentions) {
    if (!attentions || !attentions[0] || attentions[0].length === 0) return null;
    const lastLayer = attentions[0][attentions[0].length - 1];
    if (!lastLayer || !lastLayer.dims) return null;

    const numHeads = lastLayer.dims[1];
    const seqLen = lastLayer.dims[2];
    const data = lastLayer.data;
    
    const averagedAttention = new Float32Array(seqLen);
    
    for (let s = 0; s < seqLen; s++) {
      let sum = 0;
      for (let h = 0; h < numHeads; h++) {
        const idx = (h * seqLen * seqLen) + ((seqLen - 1) * seqLen) + s;
        sum += data[idx];
      }
      averagedAttention[s] = sum / numHeads;
    }

    return averagedAttention;
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