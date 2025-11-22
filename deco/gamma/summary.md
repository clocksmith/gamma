🐕 --- DOGS_START_FILE: web/package.json ---
{
  "name": "gamma-web",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "@huggingface/transformers": "^3.0.0"
  },
  "devDependencies": {
    "vite": "^5.2.0"
  }
}
🐕 --- DOGS_END_FILE: web/package.json ---

🐕 --- DOGS_START_FILE: web/vite.config.js ---
import { defineConfig } from 'vite';

export default defineConfig({
  base: './',
  build: {
    target: 'esnext',
    minify: false
  },
  worker: {
    format: 'es'
  }
});
🐕 --- DOGS_END_FILE: web/vite.config.js ---

🐕 --- DOGS_START_FILE: web/index.html ---
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>GAMMA - Token Prediction Game</title>
  <link rel="stylesheet" href="./styles/gamma-theme.css">
</head>
<body>
  <div id="gamma-root" class="gamma-container"></div>

  <script type="module">
    import { GammaApp } from './app.js';

    const app = new GammaApp(document.getElementById('gamma-root'));
    await app.init();
  </script>
</body>
</html>
🐕 --- DOGS_END_FILE: web/index.html ---

🐕 --- DOGS_START_FILE: web/styles/gamma-theme.css ---
:root {
  --primary: #00ffff;
  --secondary: #ff00ff;
  --success: #00ff00;
  --warning: #ffd700;
  --danger: #ff3333;
  
  --bg-dark: #0a0a0a;
  --bg-panel: #111111;
  --bg-element: #1a1a1a;
  --bg-hover: #2a2a2a;
  
  --border-default: #333;
  --border-subtle: #222;
  
  --text-primary: #e0e0e0;
  --text-secondary: #a0a0a0;
  --text-muted: #606060;
  
  --font-mono: 'Courier New', monospace;
  --space-sm: 8px;
  --space-md: 16px;
  --space-lg: 24px;
}

body {
  background-color: var(--bg-dark);
  color: var(--text-primary);
  font-family: var(--font-mono);
  margin: 0;
  padding: 20px;
}

.gamma-container {
  max-width: 1000px;
  margin: 0 auto;
}

.gamma-game-panel {
  background: var(--bg-panel);
  border: 1px solid var(--border-default);
  padding: var(--space-lg);
  border-radius: 4px;
  box-shadow: 0 0 20px rgba(0, 0, 0, 0.5);
}

.game-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: var(--space-md);
  border-bottom: 1px solid var(--border-subtle);
  margin-bottom: var(--space-lg);
}

.game-title {
  color: var(--primary);
  font-size: 24px;
  letter-spacing: 4px;
  text-shadow: 0 0 10px rgba(0, 255, 255, 0.3);
  margin: 0;
}

.round-indicator, .score-display {
  color: var(--text-secondary);
  font-size: 14px;
}

.score-display .score {
  color: var(--success);
  font-weight: bold;
}

.context-display {
  background: var(--bg-element);
  padding: var(--space-md);
  margin-bottom: var(--space-lg);
  border-left: 2px solid var(--primary);
  min-height: 60px;
}

.context-label {
  color: var(--text-muted);
  font-size: 11px;
  text-transform: uppercase;
  margin-bottom: var(--space-sm);
}

.context-text {
  color: var(--text-primary);
  line-height: 1.6;
  white-space: pre-wrap;
}

.context-text .token {
  padding: 2px 4px;
  border-radius: 2px;
  transition: background 0.2s ease;
  display: inline-block;
}

.context-text .token.attention-dim { background: rgba(255, 0, 255, 0.1); }
.context-text .token.attention-light { background: rgba(255, 0, 255, 0.25); }
.context-text .token.attention-medium { background: rgba(255, 0, 255, 0.4); }
.context-text .token.attention-bright { background: rgba(255, 0, 255, 0.6); }
.context-text .token.attention-intense { background: rgba(255, 0, 255, 0.8); color: #fff; }

.choices-container {
  margin-bottom: var(--space-lg);
}

.choices-label {
  color: var(--text-secondary);
  margin-bottom: var(--space-md);
}

.choices-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-md);
}

.choice-btn {
  background: var(--bg-element);
  border: 1px solid var(--border-default);
  padding: var(--space-md);
  text-align: left;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  flex-direction: column;
  gap: 4px;
  color: var(--text-primary);
}

.choice-btn:hover:not(:disabled) {
  border-color: var(--primary);
  background: var(--bg-hover);
  box-shadow: 0 0 10px rgba(0, 255, 255, 0.1);
}

.choice-btn.selected {
  border-color: var(--primary);
  background: rgba(0, 255, 255, 0.1);
}

.choice-btn.correct {
  border-color: var(--success);
  background: rgba(0, 255, 0, 0.1);
}

.choice-btn.incorrect {
  border-color: var(--danger);
  background: rgba(255, 51, 51, 0.1);
}

.choice-label {
  color: var(--primary);
  font-weight: bold;
  font-size: 12px;
}

.choice-text {
  font-size: 14px;
}

.choice-prob {
  color: var(--text-muted);
  font-size: 11px;
}

.probability-container {
  margin-bottom: var(--space-lg);
}

.prob-stages-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-md);
}

.prob-stage {
  background: var(--bg-element);
  border: 1px solid var(--border-subtle);
  padding: var(--space-sm);
}

.attention-container {
  margin-bottom: var(--space-lg);
  height: 60px;
  background: var(--bg-element);
  border: 1px solid var(--border-subtle);
  overflow: hidden;
}

.attention-canvas {
  width: 100%;
  height: 100%;
}

.model-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: var(--space-md);
  margin-bottom: var(--space-lg);
}

.model-card {
  background: var(--bg-element);
  border: 1px solid var(--border-default);
  padding: var(--space-md);
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
}

.model-card:hover {
  border-color: var(--primary);
}

.model-card.recommended::before {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  border: 8px solid transparent;
  border-top-color: var(--warning);
  border-right-color: var(--warning);
}

.model-name {
  color: var(--text-primary);
  font-weight: bold;
  margin-bottom: var(--space-sm);
}

.model-specs {
  color: var(--text-secondary);
  font-size: 11px;
  margin-bottom: var(--space-sm);
}

.cap-badge {
  display: inline-block;
  background: rgba(0, 255, 255, 0.1);
  color: var(--primary);
  padding: 2px 6px;
  font-size: 9px;
  margin-right: 4px;
  text-transform: uppercase;
  border: 1px solid rgba(0, 255, 255, 0.2);
}

.download-progress {
  margin-top: var(--space-sm);
}

.progress-bar {
  height: 4px;
  background: var(--bg-panel);
  position: relative;
  overflow: hidden;
  margin-bottom: 4px;
}

.progress-bar::after {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  width: var(--progress, 0%);
  background: linear-gradient(90deg, var(--primary), var(--secondary));
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 10px;
  color: var(--text-muted);
  text-align: right;
}

.result-display {
  text-align: center;
  padding: var(--space-lg);
  background: var(--bg-element);
  border: 1px solid var(--border-subtle);
  margin-top: var(--space-lg);
}

.result-display.correct { border-color: var(--success); }
.result-display.incorrect { border-color: var(--danger); }

.result-text {
  font-size: 18px;
  font-weight: bold;
}

.btn {
  background: transparent;
  border: 1px solid var(--primary);
  color: var(--primary);
  padding: 8px 16px;
  cursor: pointer;
  font-family: var(--font-mono);
  text-transform: uppercase;
  transition: all 0.2s ease;
}

.btn:hover {
  background: var(--primary);
  color: var(--bg-dark);
}

.hidden { display: none !important; }

.loading-screen {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 300px;
  color: var(--primary);
}
🐕 --- DOGS_END_FILE: web/styles/gamma-theme.css ---

🐕 --- DOGS_START_FILE: web/utils/math.js ---
export const MathUtils = {
  softmax(logits) {
    const maxLogit = Math.max(...logits);
    const exps = logits.map(l => Math.exp(l - maxLogit));
    const sumExps = exps.reduce((a, b) => a + b, 0);
    return exps.map(e => e / sumExps);
  },

  calculateEntropy(probs) {
    return -probs.reduce((sum, p) => {
      return p > 0 ? sum + (p * Math.log(p)) : sum;
    }, 0);
  },

  argmax(array) {
    return array.reduce((iMax, x, i, arr) => x > arr[iMax] ? i : iMax, 0);
  },

  shuffleArray(array) {
    for (let i = array.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [array[i], array[j]] = [array[j], array[i]];
    }
    return array;
  }
};
🐕 --- DOGS_END_FILE: web/utils/math.js ---

🐕 --- DOGS_START_FILE: web/utils/event-bus.js ---
export const EventBus = {
  events: {},

  on(event, callback) {
    if (!this.events[event]) this.events[event] = [];
    this.events[event].push(callback);
    return () => this.off(event, callback);
  },

  off(event, callback) {
    if (!this.events[event]) return;
    this.events[event] = this.events[event].filter(cb => cb !== callback);
  },

  emit(event, data) {
    if (!this.events[event]) return;
    this.events[event].forEach(cb => cb(data));
  }
};
🐕 --- DOGS_END_FILE: web/utils/event-bus.js ---

🐕 --- DOGS_START_FILE: web/utils/storage.js ---
const DB_NAME = 'gamma_db';
const DB_VERSION = 1;

export const Storage = {
  db: null,

  async init() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION);
      
      request.onupgradeneeded = (e) => {
        const db = e.target.result;
        if (!db.objectStoreNames.contains('sessions')) {
          db.createObjectStore('sessions', { keyPath: 'id', autoIncrement: true });
        }
        if (!db.objectStoreNames.contains('settings')) {
          db.createObjectStore('settings', { keyPath: 'key' });
        }
      };

      request.onsuccess = (e) => {
        this.db = e.target.result;
        resolve();
      };
      
      request.onerror = (e) => reject(e);
    });
  },

  async saveSession(sessionData) {
    return this._tx('sessions', 'readwrite', store => store.add(sessionData));
  },

  async getSessions() {
    return this._tx('sessions', 'readonly', store => store.getAll());
  },

  async saveSetting(key, value) {
    return this._tx('settings', 'readwrite', store => store.put({ key, value }));
  },

  async getSetting(key, defaultValue) {
    try {
      const result = await this._tx('settings', 'readonly', store => store.get(key));
      return result ? result.value : defaultValue;
    } catch {
      return defaultValue;
    }
  },

  _tx(storeName, mode, callback) {
    return new Promise((resolve, reject) => {
      const tx = this.db.transaction(storeName, mode);
      const store = tx.objectStore(storeName);
      const request = callback(store);
      
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }
};
🐕 --- DOGS_END_FILE: web/utils/storage.js ---

🐕 --- DOGS_START_FILE: web/core/config.js ---
export const DEFAULT_TEMPERATURE = 0.9;
export const DEFAULT_TOP_K = 64;
export const DEFAULT_TOP_P = 0.95;
export const DEFAULT_MAX_ROUNDS = 10;
export const DEFAULT_NUM_CHOICES = 4;
export const MIN_WORD_TOKEN_LENGTH = 2;

export const MAX_TOKENS_FOR_PROB_DISPLAY = 5;
export const MAX_PROB_STAGES_TO_SHOW = 4;

export const COLORS = {
  PRIMARY: '#00ffff',
  SECONDARY: '#ff00ff',
  SUCCESS: '#00ff00',
  WARNING: '#ffd700',
  DANGER: '#ff3333',
  BG_DARK: '#0a0a0a',
  BG_PANEL: '#111111',
  TEXT_PRIMARY: '#e0e0e0',
  TEXT_MUTED: '#808080'
};

export const ATTENTION_LEVELS = {
  DIM: 'rgba(255, 0, 255, 0.2)',
  LIGHT: 'rgba(255, 0, 255, 0.4)',
  MEDIUM: 'rgba(255, 0, 255, 0.6)',
  BRIGHT: 'rgba(255, 0, 255, 0.8)',
  INTENSE: 'rgba(255, 0, 255, 1.0)'
};
🐕 --- DOGS_END_FILE: web/core/config.js ---

🐕 --- DOGS_START_FILE: web/core/sampling-utils.js ---
import { MathUtils } from '../utils/math.js';

export const SamplingUtils = {
  processLogitsPipeline(logits, { temperature, topK, topP }) {
    let currentLogits = Float32Array.from(logits);
    const stages = {};

    // 1. Temperature
    if (temperature > 0 && Math.abs(temperature - 1.0) > 1e-6) {
      currentLogits = this.applyTemperature(currentLogits, temperature);
    }
    stages.temperature = Float32Array.from(currentLogits);

    // 2. Top-K
    if (topK > 0 && topK < currentLogits.length) {
      currentLogits = this.applyTopK(currentLogits, topK);
    }
    stages.topK = Float32Array.from(currentLogits);

    // 3. Top-P
    if (topP > 0 && topP < 1.0) {
      currentLogits = this.applyTopP(currentLogits, topP);
    }
    stages.topP = Float32Array.from(currentLogits);

    // 4. Softmax
    const probs = MathUtils.softmax(currentLogits);

    return { probs, stages, finalLogits: currentLogits };
  },

  applyTemperature(logits, temperature) {
    const temp = Math.max(temperature, 1e-6);
    return logits.map(l => l / temp);
  },

  applyTopK(logits, k) {
    const sorted = [...logits].sort((a, b) => b - a);
    const threshold = sorted[k - 1];
    return logits.map(l => l >= threshold ? l : -Infinity);
  },

  applyTopP(logits, p) {
    const probs = MathUtils.softmax(logits);
    const indices = [...probs.keys()].sort((a, b) => probs[b] - probs[a]);
    
    let cumSum = 0;
    const keepIndices = new Set();
    
    for (const idx of indices) {
      keepIndices.add(idx);
      cumSum += probs[idx];
      if (cumSum >= p) break;
    }

    if (keepIndices.size === 0 && indices.length > 0) {
      keepIndices.add(indices[0]);
    }

    return logits.map((l, i) => keepIndices.has(i) ? l : -Infinity);
  }
};
🐕 --- DOGS_END_FILE: web/core/sampling-utils.js ---

🐕 --- DOGS_START_FILE: web/core/model-registry.js ---
export const MODEL_CATALOG = {
  'Qwen/Qwen2.5-0.5B-Instruct': {
    id: 'Qwen/Qwen2.5-0.5B-Instruct',
    name: 'Qwen 2.5 0.5B',
    size: '500M',
    vram: '600MB',
    capabilities: ['fast', 'multilingual', 'reasoning'],
    recommended: true,
    engine: 'transformers'
  },
  'HuggingFaceTB/SmolLM2-135M-Instruct': {
    id: 'HuggingFaceTB/SmolLM2-135M-Instruct',
    name: 'SmolLM2 135M',
    size: '135M',
    vram: '200MB',
    capabilities: ['ultra-fast', 'lightweight'],
    recommended: false,
    engine: 'transformers'
  },
  'HuggingFaceTB/SmolLM2-360M-Instruct': {
    id: 'HuggingFaceTB/SmolLM2-360M-Instruct',
    name: 'SmolLM2 360M',
    size: '360M',
    vram: '400MB',
    capabilities: ['balanced'],
    recommended: true,
    engine: 'transformers'
  },
  'Xenova/gemma-2b-it': { 
    id: 'Xenova/gemma-2b-it',
    name: 'Gemma 2B IT',
    size: '2B',
    vram: '1.5GB',
    capabilities: ['quality', 'attention-viz'],
    recommended: false,
    engine: 'transformers'
  }
};

export const DEFAULT_MODEL = 'Qwen/Qwen2.5-0.5B-Instruct';
🐕 --- DOGS_END_FILE: web/core/model-registry.js ---

🐕 --- DOGS_START_FILE: web/core/engine-interface.js ---
export class EngineInterface {
  constructor(modelId, config = {}) {
    this.modelId = modelId;
    this.config = config;
    this.ready = false;
  }

  async load() { throw new Error('Not implemented'); }
  encode(text) { throw new Error('Not implemented'); }
  decode(tokenIds) { throw new Error('Not implemented'); }
  async predictNext(inputIds, samplingConfig) { throw new Error('Not implemented'); }
  getVocabularySize() { throw new Error('Not implemented'); }
  getTokenText(tokenId) { throw new Error('Not implemented'); }
  isSpecialToken(tokenId) { throw new Error('Not implemented'); }
}
🐕 --- DOGS_END_FILE: web/core/engine-interface.js ---

🐕 --- DOGS_START_FILE: web/engines/transformers-engine.js ---
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
        dtype: 'q4',
        device: this.device,
        use_external_data_format: true,
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
🐕 --- DOGS_END_FILE: web/engines/transformers-engine.js ---

🐕 --- DOGS_START_FILE: web/engines/webllm-engine.js ---
import { EngineInterface } from '../core/engine-interface.js';

export class WebLLMEngine extends EngineInterface {
  async load() {
    throw new Error('WebLLM support pending implementation');
  }
}
🐕 --- DOGS_END_FILE: web/engines/webllm-engine.js ---

🐕 --- DOGS_START_FILE: web/engines/engine-factory.js ---
import { TransformersEngine } from './transformers-engine.js';
import { MODEL_CATALOG } from '../core/model-registry.js';

export const EngineFactory = {
  getEngine(modelId) {
    const config = MODEL_CATALOG[modelId];
    if (!config) {
      throw new Error(`Model ${modelId} not found in registry`);
    }

    switch (config.engine) {
      case 'transformers':
        return new TransformersEngine(modelId, config);
      default:
        throw new Error(`Unknown engine type: ${config.engine}`);
    }
  }
};
🐕 --- DOGS_END_FILE: web/engines/engine-factory.js ---

🐕 --- DOGS_START_FILE: web/game/game-logic.js ---
import { MathUtils } from '../utils/math.js';

export function generateChoices(topTokens, engine, numChoices = 4) {
  const filtered = topTokens.filter(token => {
    const text = token.text;
    if (engine.isSpecialToken(token.id)) return false;
    if (/^[<>\[\]{}()=+*\/]/.test(text)) return false;
    if (!/\S/.test(text)) return false;
    return true;
  });

  if (filtered.length < numChoices) {
    return topTokens.slice(0, numChoices);
  }

  const correct = filtered[0];
  const distractors = filtered.slice(1, numChoices);

  const choices = [correct, ...distractors];
  MathUtils.shuffleArray(choices);

  return {
    choices,
    correctIndex: choices.indexOf(correct),
    correctToken: correct
  };
}
🐕 --- DOGS_END_FILE: web/game/game-logic.js ---

🐕 --- DOGS_START_FILE: web/game/game-session.js ---
import { Storage } from '../utils/storage.js';
import { EventBus } from '../utils/event-bus.js';

export class GameSession {
  constructor(config) {
    this.config = config;
    this.rounds = [];
    this.currentRound = 0;
    this.score = 0;
    this.streak = 0;
    this.maxStreak = 0;
    this.achievements = [];
    this.startTime = Date.now();
  }

  recordRound(result) {
    this.rounds.push({
      roundNum: this.currentRound,
      ...result,
      timestamp: Date.now()
    });

    if (result.isCorrect) {
      this.score++;
      this.streak++;
      this.maxStreak = Math.max(this.maxStreak, this.streak);
      this.checkAchievements();
    } else {
      this.streak = 0;
    }

    this.currentRound++;
  }

  checkAchievements() {
    if (this.streak === 3 && !this.achievements.includes('streak3')) {
      this.achievements.push('streak3');
      EventBus.emit('achievement', { 
        id: 'streak3', 
        name: 'Hot Streak', 
        desc: '3 correct in a row' 
      });
    }
  }

  async save() {
    await Storage.saveSession({
      timestamp: this.startTime,
      score: this.score,
      maxStreak: this.maxStreak,
      rounds: this.rounds
    });
  }
}
🐕 --- DOGS_END_FILE: web/game/game-session.js ---

🐕 --- DOGS_START_FILE: web/game/tutorial.js ---
export const Tutorial = {
  steps: [
    {
      title: "Welcome to GAMMA",
      text: "Predict the next token that the AI model will generate."
    },
    {
      title: "Context",
      text: "Read the text in the context box. The AI uses this to guess what comes next."
    },
    {
      title: "Probabilities",
      text: "See how the AI's confidence changes as it applies Temperature and Filtering."
    }
  ]
};
🐕 --- DOGS_END_FILE: web/game/tutorial.js ---

🐕 --- DOGS_START_FILE: web/game/game-controller.js ---
import { GameSession } from './game-session.js';
import { generateChoices } from './game-logic.js';
import { EventBus } from '../utils/event-bus.js';

export class GameController {
  constructor(engine, config) {
    this.engine = engine;
    this.config = config;
    this.session = new GameSession(config);
    this.context = config.initialPrompt || 'The artificial intelligence revolution began when';
    this.isRunning = false;
    this.resolveChoice = null;
  }

  async runRound() {
    const inputIds = this.engine.encode(this.context);

    const prediction = await this.engine.predictNext(inputIds, {
      temperature: this.config.temperature,
      topK: this.config.topK,
      topP: this.config.topP
    });

    const { choices, correctIndex, correctToken } = generateChoices(
      prediction.topTokens,
      this.engine,
      this.config.numChoices
    );

    EventBus.emit('round:start', {
      roundNum: this.session.currentRound + 1,
      maxRounds: this.config.maxRounds,
      context: this.context,
      choices,
      attention: prediction.attention,
      probStages: {
        raw: prediction.logitsRaw,
        temperature: prediction.stages.temperature,
        topK: prediction.stages.topK,
        topP: prediction.stages.topP,
        final: prediction.probabilities
      }
    });

    const playerChoice = await this.waitForPlayerChoice();

    const isCorrect = playerChoice === correctIndex;
    this.session.recordRound({
      context: this.context,
      choices,
      playerChoice,
      correctChoice: correctIndex,
      isCorrect,
      probabilities: prediction.probabilities
    });

    EventBus.emit('round:result', {
      isCorrect,
      correctToken,
      playerChoice,
      probabilities: prediction.topTokens
    });

    this.context += correctToken.text;
    return isCorrect;
  }

  async waitForPlayerChoice() {
    return new Promise(resolve => {
      this.resolveChoice = resolve;
    });
  }

  submitChoice(index) {
    if (this.resolveChoice) {
      this.resolveChoice(index);
      this.resolveChoice = null;
    }
  }

  async waitForContinue() {
    return new Promise(resolve => {
      this.resolveContinue = resolve;
    });
  }

  triggerContinue() {
    if (this.resolveContinue) {
      this.resolveContinue();
      this.resolveContinue = null;
    }
  }

  async runGame() {
    this.isRunning = true;
    EventBus.emit('game:start', { session: this.session });

    for (let i = 0; i < this.config.maxRounds && this.isRunning; i++) {
      await this.runRound();
      await this.waitForContinue();
    }

    EventBus.emit('game:end', {
      score: this.session.score,
      maxRounds: this.config.maxRounds,
      achievements: this.session.achievements
    });

    await this.session.save();
  }
}
🐕 --- DOGS_END_FILE: web/game/game-controller.js ---

🐕 --- DOGS_START_FILE: web/mind-meld/swap-strategies.js ---
import { MathUtils } from '../utils/math.js';

export class SwapStrategyBase {
  shouldSwap(lastToken, predictions, activeIndex) { throw new Error('Abstract'); }
  selectNext(predictions, currentIndex) { throw new Error('Abstract'); }
}

export class FixedIntervalStrategy extends SwapStrategyBase {
  constructor(interval = 5) {
    super();
    this.interval = interval;
    this.counter = 0;
  }

  shouldSwap() {
    this.counter++;
    if (this.counter >= this.interval) {
      this.counter = 0;
      this.lastReason = `Fixed interval (${this.interval} tokens)`;
      return true;
    }
    return false;
  }

  selectNext(predictions, currentIndex) {
    return (currentIndex + 1) % predictions.length;
  }
}

export class ConfidenceBasedStrategy extends SwapStrategyBase {
  constructor(threshold = 0.3) {
    super();
    this.threshold = threshold;
  }

  shouldSwap(lastToken, predictions, activeIndex) {
    const activePred = predictions[activeIndex];
    const topProb = Math.max(...MathUtils.softmax(activePred.logitsProcessed));

    if (topProb < this.threshold) {
      this.lastReason = `Low confidence: ${(topProb * 100).toFixed(1)}%`;
      return true;
    }
    return false;
  }

  selectNext(predictions, currentIndex) {
    let maxConf = 0;
    let bestIdx = currentIndex;
    predictions.forEach((pred, idx) => {
      const conf = Math.max(...MathUtils.softmax(pred.logitsProcessed));
      if (conf > maxConf) {
        maxConf = conf;
        bestIdx = idx;
      }
    });
    return bestIdx;
  }
}
🐕 --- DOGS_END_FILE: web/mind-meld/swap-strategies.js ---

🐕 --- DOGS_START_FILE: web/mind-meld/vocabulary-translator.js ---
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
🐕 --- DOGS_END_FILE: web/mind-meld/vocabulary-translator.js ---

🐕 --- DOGS_START_FILE: web/mind-meld/logit-blender.js ---
import { MathUtils } from '../utils/math.js';

export class LogitBlender {
  constructor(strategy = 'weighted_average') {
    this.strategy = strategy;
    this.weights = null;
  }

  blend(logitsList) {
    if (this.strategy === 'confidence_weighted') {
      return this.confidenceWeighted(logitsList);
    }
    return this.weightedAverage(logitsList);
  }

  weightedAverage(logitsList) {
    const weights = this.weights || logitsList.map(() => 1 / logitsList.length);
    const result = new Float32Array(logitsList[0].length);
    for (let i = 0; i < result.length; i++) {
      result[i] = logitsList.reduce((sum, logits, idx) => sum + logits[i] * weights[idx], 0);
    }
    return result;
  }

  confidenceWeighted(logitsList) {
    const weights = logitsList.map(logits => {
      const probs = MathUtils.softmax(logits);
      const entropy = MathUtils.calculateEntropy(probs);
      return 1 / (entropy + 1e-6);
    });
    const sum = weights.reduce((a, b) => a + b, 0);
    this.weights = weights.map(w => w / sum);
    return this.weightedAverage(logitsList);
  }
}
🐕 --- DOGS_END_FILE: web/mind-meld/logit-blender.js ---

🐕 --- DOGS_START_FILE: web/mind-meld/abe-ensemble.js ---
export class ABEEnsemble {
  findAgreement(predictions) {
    const topTokensByModel = predictions.map(pred => pred.topTokens.slice(0, 10));
    const candidates = [];

    for (const token of topTokensByModel[0]) {
      const text = token.text.toLowerCase().trim();
      const matches = topTokensByModel.slice(1).map(tokens =>
        tokens.find(t => t.text.toLowerCase().trim() === text)
      );

      if (matches.every(m => m)) {
        const combinedProb = [token, ...matches].reduce((sum, t) => sum + t.prob, 0) / predictions.length;
        candidates.push({ text, combinedProb, agreement: 1.0 });
      }
    }

    if (candidates.length === 0) return null;
    candidates.sort((a, b) => b.combinedProb - a.combinedProb);
    return candidates[0];
  }
}
🐕 --- DOGS_END_FILE: web/mind-meld/abe-ensemble.js ---

🐕 --- DOGS_START_FILE: web/mind-meld/meld-engine.js ---
import { MathUtils } from '../utils/math.js';
import { VocabularyTranslator } from './vocabulary-translator.js';
import { LogitBlender } from './logit-blender.js';
import { ABEEnsemble } from './abe-ensemble.js';
import { FixedIntervalStrategy, ConfidenceBasedStrategy } from './swap-strategies.js';
import { EventBus } from '../utils/event-bus.js';

export class MeldEngine {
  constructor(engines, config) {
    this.engines = engines;
    this.config = config;
    this.activeIndex = 0;
    this.vocabTranslator = new VocabularyTranslator();
    this.tokenHistory = [];
    
    this.swapStrategy = config.swapStrategy === 'confidence' 
      ? new ConfidenceBasedStrategy() 
      : new FixedIntervalStrategy();
      
    this.blender = config.useBlending ? new LogitBlender() : null;
    this.abeEnsemble = config.useABE ? new ABEEnsemble() : null;
  }

  async generateToken(context) {
    const predictions = await Promise.all(
      this.engines.map(engine => engine.predictNext(engine.encode(context), this.config))
    );

    let finalLogits;

    if (this.blender) {
      finalLogits = this.blender.blend(predictions.map(p => p.logitsProcessed));
    } else {
      finalLogits = predictions[this.activeIndex].logitsProcessed;
      const lastToken = this.tokenHistory[this.tokenHistory.length - 1] || '';
      
      if (this.swapStrategy.shouldSwap(lastToken, predictions, this.activeIndex)) {
        const newIndex = this.swapStrategy.selectNext(predictions, this.activeIndex);
        EventBus.emit('meld:swap', {
          from: this.activeIndex,
          to: newIndex,
          reason: this.swapStrategy.lastReason
        });
        this.activeIndex = newIndex;
        finalLogits = predictions[this.activeIndex].logitsProcessed;
      }
    }

    const probs = MathUtils.softmax(finalLogits);
    const tokenId = MathUtils.argmax(probs);
    const tokenText = this.engines[this.activeIndex].getTokenText(tokenId);

    this.tokenHistory.push(tokenText);

    return {
      tokenId,
      tokenText,
      activeModel: this.activeIndex
    };
  }
}
🐕 --- DOGS_END_FILE: web/mind-meld/meld-engine.js ---

🐕 --- DOGS_START_FILE: web/ui/toast.js ---
export const Toast = {
  container: null,

  init() {
    this.container = document.createElement('div');
    this.container.style.cssText = 'position: fixed; bottom: 20px; right: 20px; display: flex; flex-direction: column; gap: 10px; z-index: 1000;';
    document.body.appendChild(this.container);
  },

  show(message, type = 'info') {
    if (!this.container) this.init();
    
    const el = document.createElement('div');
    el.className = `achievement-toast ${type}`;
    el.innerHTML = `
      <div class="achievement-icon">🏆</div>
      <div>
        <div class="achievement-name">${message.name || 'Notification'}</div>
        <div class="achievement-desc">${message.desc || message}</div>
      </div>
    `;
    
    this.container.appendChild(el);
    setTimeout(() => {
      el.style.opacity = '0';
      setTimeout(() => el.remove(), 300);
    }, 4000);
  }
};
🐕 --- DOGS_END_FILE: web/ui/toast.js ---

🐕 --- DOGS_START_FILE: web/ui/progress-indicator.js ---
export class ProgressIndicator {
  constructor(container) {
    this.container = container;
  }

  update(modelId, percent) {
    const card = this.container.querySelector(`[data-model-id="${modelId}"]`);
    if (!card) return;
    
    const progressEl = card.querySelector('.download-progress');
    if (progressEl.classList.contains('hidden')) {
      progressEl.classList.remove('hidden');
    }

    const bar = progressEl.querySelector('.progress-bar div') || progressEl.querySelector('.progress-bar');
    if (bar.style) {
      bar.style.setProperty('--progress', `${percent}%`);
    }
    
    const text = progressEl.querySelector('.progress-text');
    text.textContent = `${Math.round(percent)}%`;
  }
}
🐕 --- DOGS_END_FILE: web/ui/progress-indicator.js ---

🐕 --- DOGS_START_FILE: web/ui/model-selector.js ---
import { MODEL_CATALOG } from '../core/model-registry.js';
import { EventBus } from '../utils/event-bus.js';

export class ModelSelector {
  constructor(container) {
    this.container = container;
  }

  render() {
    const models = Object.entries(MODEL_CATALOG);
    this.container.innerHTML = `
      <div class="model-selector">
        <h3>Select Model</h3>
        <div class="model-grid">
          ${models.map(([id, info]) => `
            <div class="model-card ${info.recommended ? 'recommended' : ''}" data-model-id="${id}">
              <div class="model-name">${info.name}</div>
              <div class="model-specs">${info.size} • ${info.vram}</div>
              <div class="model-caps">
                ${info.capabilities.map(c => `<span class="cap-badge">${c}</span>`).join('')}
              </div>
              <div class="download-progress hidden">
                <div class="progress-bar"></div>
                <div class="progress-text">0%</div>
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    `;

    this.container.querySelectorAll('.model-card').forEach(card => {
      card.addEventListener('click', () => {
        EventBus.emit('model:selected', card.dataset.modelId);
      });
    });
  }

  updateProgress(modelId, percent) {
    const card = this.container.querySelector(`[data-model-id="${modelId}"]`);
    if (!card) return;
    const progressEl = card.querySelector('.download-progress');
    progressEl.classList.remove('hidden');
    progressEl.querySelector('.progress-bar').style.setProperty('--progress', `${percent}%`);
    progressEl.querySelector('.progress-text').textContent = `${Math.round(percent)}%`;
  }
}
🐕 --- DOGS_END_FILE: web/ui/model-selector.js ---

🐕 --- DOGS_START_FILE: web/ui/attention-viz.js ---
export class AttentionViz {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
  }

  render(tokens, attentionWeights) {
    if (!attentionWeights || tokens.length === 0) return;

    const width = this.canvas.width = this.canvas.offsetWidth;
    const height = this.canvas.height = this.canvas.offsetHeight;
    
    const maxWeight = Math.max(...attentionWeights, 0.0001);
    const normalized = attentionWeights.map(w => w / maxWeight);

    this.ctx.clearRect(0, 0, width, height);
    const tokenWidth = Math.min(60, width / tokens.length);

    tokens.forEach((token, i) => {
      const x = i * tokenWidth;
      const intensity = normalized[i];
      const r = Math.floor(255 * intensity);
      const b = Math.floor(255 * intensity);
      
      this.ctx.fillStyle = `rgba(${r}, 0, ${b}, ${0.2 + intensity * 0.6})`;
      this.ctx.fillRect(x, 0, tokenWidth - 2, height);

      this.ctx.fillStyle = intensity > 0.5 ? '#ffffff' : '#a0a0a0';
      this.ctx.font = '10px Courier New';
      this.ctx.textAlign = 'center';
      
      this.ctx.save();
      this.ctx.translate(x + tokenWidth / 2, height - 5);
      this.ctx.rotate(-Math.PI / 4);
      this.ctx.fillText(token.length > 8 ? token.slice(0, 7) + '…' : token, 0, 0);
      this.ctx.restore();
    });
  }
}
🐕 --- DOGS_END_FILE: web/ui/attention-viz.js ---

🐕 --- DOGS_START_FILE: web/ui/probability-viz.js ---
export class ProbabilityViz {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
  }

  render(topTokens, stageName, maxTokens = 8) {
    const tokens = topTokens.slice(0, maxTokens);
    const width = this.canvas.width = this.canvas.offsetWidth;
    const height = this.canvas.height = this.canvas.offsetHeight;
    const barHeight = (height - 30) / tokens.length;
    const maxProb = Math.max(...tokens.map(t => t.prob), 0.001);

    this.ctx.clearRect(0, 0, width, height);
    
    this.ctx.fillStyle = '#a0a0a0';
    this.ctx.font = '11px Courier New';
    this.ctx.textAlign = 'left';
    this.ctx.fillText(stageName, 5, 12);

    tokens.forEach((token, i) => {
      const y = 20 + i * barHeight;
      const barWidth = (token.prob / maxProb) * (width - 100);

      this.ctx.fillStyle = 'rgba(0, 255, 255, 0.1)';
      this.ctx.fillRect(50, y, width - 60, barHeight - 2);

      const gradient = this.ctx.createLinearGradient(50, 0, 50 + barWidth, 0);
      gradient.addColorStop(0, 'rgba(0, 255, 255, 0.8)');
      gradient.addColorStop(1, 'rgba(255, 0, 255, 0.8)');
      this.ctx.fillStyle = gradient;
      this.ctx.fillRect(50, y, barWidth, barHeight - 2);

      this.ctx.fillStyle = '#e0e0e0';
      this.ctx.textAlign = 'right';
      this.ctx.fillText(token.text.slice(0, 8), 45, y + barHeight / 2 + 4);

      this.ctx.textAlign = 'left';
      this.ctx.fillText(`${(token.prob * 100).toFixed(1)}%`, 55 + barWidth, y + barHeight / 2 + 4);
    });
  }
}
🐕 --- DOGS_END_FILE: web/ui/probability-viz.js ---

🐕 --- DOGS_START_FILE: web/ui/game-panel.js ---
import { AttentionViz } from './attention-viz.js';
import { ProbabilityViz } from './probability-viz.js';
import { EventBus } from '../utils/event-bus.js';

export class GamePanel {
  constructor(container) {
    this.container = container;
    this.setupDOM();
    this.bindEvents();
    this.attentionViz = new AttentionViz(this.container.querySelector('.attention-canvas'));
    this.probVizRefs = {};
  }

  setupDOM() {
    this.container.innerHTML = `
      <div class="gamma-game-panel">
        <div class="game-header">
          <h2 class="game-title">GAMMA</h2>
          <div class="round-indicator">
            <span class="round-num">1</span>/<span class="max-rounds">8</span>
          </div>
          <div class="score-display">
            Score: <span class="score">0</span>
          </div>
        </div>
        
        <div class="context-display">
          <div class="context-label">Context:</div>
          <div class="context-text"></div>
        </div>
        
        <div class="attention-container">
          <canvas class="attention-canvas"></canvas>
        </div>
        
        <div class="choices-container">
          <div class="choices-label">What comes next?</div>
          <div class="choices-grid"></div>
        </div>
        
        <div class="probability-container">
          <div class="prob-stages-grid"></div>
        </div>
        
        <div class="result-display hidden">
          <div class="result-text"></div>
        </div>
        
        <div class="action-buttons" style="text-align:center; margin-top:20px;">
          <button class="btn hidden continue-btn">Continue</button>
        </div>
      </div>
    `;

    this.contextText = this.container.querySelector('.context-text');
    this.choicesGrid = this.container.querySelector('.choices-grid');
    this.probStagesGrid = this.container.querySelector('.prob-stages-grid');
    this.continueBtn = this.container.querySelector('.continue-btn');
    this.resultDisplay = this.container.querySelector('.result-display');

    this.continueBtn.addEventListener('click', () => {
      EventBus.emit('game:continue');
    });
  }

  bindEvents() {
    EventBus.on('round:start', (data) => this.showRound(data));
    EventBus.on('round:result', (data) => this.showResult(data));
  }

  showRound(data) {
    this.container.querySelector('.round-num').textContent = data.roundNum;
    this.container.querySelector('.max-rounds').textContent = data.maxRounds;
    this.resultDisplay.classList.add('hidden');
    this.continueBtn.classList.add('hidden');

    this.contextText.textContent = data.context;
    
    // Render Attention
    // Need tokenized context approx for viz, usually engine provides specific tokens
    // Simplification: data.attention corresponds to last tokens
    // For now, visualize attention on a dummy token split if simple text
    const tokens = data.context.split(/\s+/).slice(-data.attention.length);
    this.attentionViz.render(tokens, data.attention);

    this.renderChoices(data.choices);
    this.renderProbabilities(data.probStages);
  }

  renderChoices(choices) {
    const labels = ['A', 'B', 'C', 'D'];
    this.choicesGrid.innerHTML = choices.map((choice, i) => `
      <button class="choice-btn" data-index="${i}">
        <span class="choice-label">${labels[i]}</span>
        <span class="choice-text">${choice.text}</span>
        <span class="choice-prob">${(choice.prob * 100).toFixed(1)}%</span>
      </button>
    `).join('');

    this.choicesGrid.querySelectorAll('.choice-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        EventBus.emit('player:choice', parseInt(btn.dataset.index));
      });
    });
  }

  renderProbabilities(stages) {
    this.probStagesGrid.innerHTML = '';
    ['raw', 'temperature', 'topK', 'topP'].forEach(stage => {
      const wrapper = document.createElement('div');
      wrapper.className = 'prob-stage';
      const canvas = document.createElement('canvas');
      canvas.style.width = '100%';
      canvas.style.height = '150px';
      wrapper.appendChild(canvas);
      this.probStagesGrid.appendChild(wrapper);
      
      // Convert Float32Array to viz format if needed
      // We need top tokens for each stage.
      // Simplified: We visualize the top tokens of final prob for all stages to show drift?
      // Or we need full data. Assuming stage passed in is full logits, we need to find top K locally.
      // For this implementation, let's assume 'stages' contains processed top-token lists for simplicity
      // OR we parse the raw arrays. Parsing raw arrays is expensive here.
      // Ideally game-controller passes pre-calculated top lists for viz.
      // Fallback: Just show final for now in one block if data complex.
    });
    // Note: To fully implement 4-stage viz, logic would extract top-k from each Float32Array.
    // Skipping heavy compute in UI thread for brevity of this snippet.
  }

  showResult(data) {
    this.resultDisplay.classList.remove('hidden');
    this.resultDisplay.className = `result-display ${data.isCorrect ? 'correct' : 'incorrect'}`;
    this.resultDisplay.querySelector('.result-text').textContent = 
      data.isCorrect ? 'Correct!' : `Missed it. The answer was: ${data.correctToken.text}`;
    
    this.continueBtn.classList.remove('hidden');
    
    // Highlight choices
    const buttons = this.choicesGrid.querySelectorAll('.choice-btn');
    buttons.forEach((btn, i) => {
      btn.disabled = true;
      if (i === data.correctChoice) btn.classList.add('correct');
      else if (i === data.playerChoice && !data.isCorrect) btn.classList.add('incorrect');
    });
  }
}
🐕 --- DOGS_END_FILE: web/ui/game-panel.js ---

🐕 --- DOGS_START_FILE: web/app.js ---
import { Storage } from './utils/storage.js';
import { EventBus } from './utils/event-bus.js';
import { EngineFactory } from './engines/engine-factory.js';
import { GameController } from './game/game-controller.js';
import { GamePanel } from './ui/game-panel.js';
import { ModelSelector } from './ui/model-selector.js';
import { Toast } from './ui/toast.js';

export class GammaApp {
  constructor(container) {
    this.container = container;
  }

  async init() {
    await Storage.init();
    Toast.init();

    const savedModel = await Storage.getSetting('selectedModel', 'Qwen/Qwen2.5-0.5B-Instruct');
    const savedConfig = await Storage.getSetting('gameConfig', {
      temperature: 0.9,
      topK: 64,
      topP: 0.95,
      maxRounds: 8
    });

    this.modelSelector = new ModelSelector(this.container);
    this.modelSelector.render();

    EventBus.on('model:selected', (modelId) => {
      this.startGame(modelId, savedConfig);
    });
    
    EventBus.on('achievement', (ach) => Toast.show(ach));
  }

  async startGame(modelId, config) {
    this.container.innerHTML = '<div class="loading-screen"><div>INITIALIZING ENGINE...</div></div>';

    try {
      const engine = EngineFactory.getEngine(modelId);

      EventBus.on('model:progress', (p) => {
        if (p.status === 'progress') {
          const percent = (p.loaded / p.total) * 100;
          this.container.querySelector('.loading-screen div').textContent = 
            `LOADING MODEL: ${Math.round(percent)}%`;
        }
      });

      await engine.load();

      this.gamePanel = new GamePanel(this.container);
      this.gameController = new GameController(engine, config);

      // Bind input events
      EventBus.on('player:choice', (idx) => this.gameController.submitChoice(idx));
      EventBus.on('game:continue', () => this.gameController.triggerContinue());

      await this.gameController.runGame();
    } catch (e) {
      console.error(e);
      this.container.innerHTML = `<div class="loading-screen" style="color:var(--danger)">ERROR: ${e.message}</div>`;
    }
  }
}
🐕 --- DOGS_END_FILE: web/app.js ---
