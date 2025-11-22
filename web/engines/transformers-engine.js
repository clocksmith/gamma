import { AutoTokenizer, AutoModelForCausalLM, env } from '@huggingface/transformers';
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

    const output = await this.model.generate(inputIds, {
      max_new_tokens: 1,
      return_dict_in_generate: true,
      output_scores: true,
      output_attentions: true,
      do_sample: false
    });

    const lastTokenScores = output.scores[0]; 
    const logitsRaw = lastTokenScores.data;
    const attentionData = this._processAttention(output.attentions);

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
    if (!attentions) return null;
    const lastLayer = attentions[0][attentions[0].length - 1];
    
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