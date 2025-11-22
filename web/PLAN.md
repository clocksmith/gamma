# Web GAMMA - Detailed Implementation Plan

## Overview

Port GAMMA token prediction game to web with reploid's cyberpunk aesthetic, full feature parity including attention visualization and Mind Meld multi-model collaboration.

---

## Phase 1: Project Structure & Core Infrastructure

### 1.1 Directory Structure

```
gamma/web/
├── index.html                    # Entry point
├── styles/
│   └── gamma-theme.css           # GAMMA-specific styles (extends reploid theme)
├── core/
│   ├── engine-interface.js       # Abstract LLM engine (port of src/core/engine_interface.py)
│   ├── sampling-utils.js         # Logit processing pipeline (port of src/engines/sampling_utils.py)
│   ├── config.js                 # Constants & defaults (port of src/core/config.py)
│   └── model-registry.js         # Model catalog (port of src/core/models/model_registry.py)
├── engines/
│   ├── engine-factory.js         # Engine factory (port of src/engines/engine_factory.py)
│   ├── transformers-engine.js    # Transformers.js engine (primary)
│   └── webllm-engine.js          # WebLLM engine (fallback)
├── game/
│   ├── game-logic.js             # Choice generation (port of src/game/game_logic.py)
│   ├── game-session.js           # Session management (port of src/game/difficulty_levels.py)
│   ├── game-controller.js        # Main game loop (port of src/game/cli.py logic)
│   └── tutorial.js               # Tutorial mode (port of src/game/tutorial_mode.py)
├── mind-meld/
│   ├── meld-engine.js            # Multi-model orchestrator (port of src/mind_meld/core/meld_engine.py)
│   ├── swap-strategies.js        # Swap decision logic (port of src/mind_meld/strategies/)
│   ├── vocabulary-translator.js  # Vocab bridging (port of src/mind_meld/translators/)
│   ├── logit-blender.js          # Blending strategies (port of src/mind_meld/core/blending.py)
│   └── abe-ensemble.js           # Agreement-based ensemble (port of src/mind_meld/core/abe_ensemble.py)
├── ui/
│   ├── game-panel.js             # Main game UI component
│   ├── probability-viz.js        # Probability bar charts
│   ├── attention-viz.js          # Attention heatmap visualization
│   ├── model-selector.js         # Model download/selection UI
│   ├── progress-indicator.js     # Download progress
│   └── toast.js                  # Notifications (reuse reploid pattern)
└── utils/
    ├── storage.js                # IndexedDB for sessions/settings
    └── event-bus.js              # Event system
```

### 1.2 Core Configuration (core/config.js)

Port from `gamma/src/core/config.py`:

```javascript
// Sampling defaults
export const DEFAULT_TEMPERATURE = 0.9;
export const DEFAULT_TOP_K = 64;
export const DEFAULT_TOP_P = 0.95;
export const DEFAULT_MAX_ROUNDS = 8;
export const DEFAULT_NUM_CHOICES = 4;

// Display limits
export const MAX_TOKENS_FOR_PROB_DISPLAY = 10;
export const MAX_PROB_STAGES_TO_SHOW = 4;

// Color scheme (matching reploid theme)
export const COLORS = {
  PRIMARY: '#00ffff',      // Cyan
  SECONDARY: '#ff00ff',    // Magenta
  SUCCESS: '#00ff00',      // Green
  WARNING: '#ffd700',      // Gold
  DANGER: '#ff3333',       // Red
  BG_DARK: '#0a0a0a',
  TEXT_PRIMARY: '#e0e0e0'
};

// Attention visualization intensity levels
export const ATTENTION_LEVELS = {
  DIM: 'rgba(255, 0, 255, 0.2)',
  LIGHT: 'rgba(255, 0, 255, 0.4)',
  MEDIUM: 'rgba(255, 0, 255, 0.6)',
  BRIGHT: 'rgba(255, 0, 255, 0.8)',
  INTENSE: 'rgba(255, 0, 255, 1.0)'
};
```

---

## Phase 2: Engine System & Model Loading

### 2.1 Engine Interface (core/engine-interface.js)

Port abstract interface from `gamma/src/core/engine_interface.py`:

**Key Methods:**
- `load()` - Initialize model & tokenizer
- `encode(text)` - Tokenize text → token IDs
- `decode(tokenIds)` - Detokenize → text
- `predictNext(inputIds, options)` - Get logits, attention, probabilities
- `getVocabularySize()` - Return vocab size
- `getTokenText(tokenId)` - Get text for token
- `isSpecialToken(tokenId)` - Check if special token

**Return Structure from predictNext():**

```javascript
{
  nextTokenId: number,
  logitsRaw: Float32Array,           // Raw model output
  logitsTemp: Float32Array,          // After temperature
  logitsTopK: Float32Array,          // After top-k filter
  logitsProcessed: Float32Array,     // After top-p filter
  probabilities: Float32Array,        // Final softmax probs
  topTokens: [{id, text, prob}],     // Top-K tokens for display
  attention: Float32Array[] | null,   // Attention weights per layer
  hiddenStates: Float32Array | null   // Optional hidden states
}
```

### 2.2 Transformers.js Engine (engines/transformers-engine.js)

Primary engine using HuggingFace Transformers.js:

**Model Loading:**

```javascript
import { AutoModelForCausalLM, AutoTokenizer } from '@huggingface/transformers';

async load() {
  // Progress callback for UI
  const progressCallback = (progress) => {
    EventBus.emit('model:progress', {
      status: progress.status,
      file: progress.file,
      progress: progress.progress,
      loaded: progress.loaded,
      total: progress.total
    });
  };

  this.tokenizer = await AutoTokenizer.from_pretrained(this.modelId, {
    progress_callback: progressCallback
  });

  this.model = await AutoModelForCausalLM.from_pretrained(this.modelId, {
    dtype: 'q4',  // Quantized for browser
    device: 'webgpu',
    progress_callback: progressCallback
  });
}
```

**Inference with Attention:**

```javascript
async predictNext(inputIds, { temperature, topK, topP }) {
  const outputs = await this.model.generate(inputIds, {
    max_new_tokens: 1,
    do_sample: false,
    output_attentions: true,      // Critical: get attention weights
    output_hidden_states: true,   // Optional: hidden states
    return_dict_in_generate: true
  });

  // Extract logits from last position
  const logits = outputs.scores[0];  // [vocab_size]

  // Extract attention (if available)
  const attention = outputs.attentions ?
    this._processAttention(outputs.attentions) : null;

  // Apply sampling pipeline
  return this._processLogits(logits, { temperature, topK, topP, attention });
}
```

### 2.3 WebLLM Engine (engines/webllm-engine.js)

Fallback engine using MLC WebLLM:

**Note:** WebLLM doesn't expose raw logits through chat API. Need lower-level access:

```javascript
// Use MLCEngine directly for logits access
import { CreateMLCEngine } from '@mlc-ai/web-llm';

async predictNext(inputIds) {
  // WebLLM internal API for logits (may require custom build)
  const output = await this.engine.forwardTokens(inputIds);
  return output.logits;  // If exposed
}
```

### 2.4 Sampling Pipeline (core/sampling-utils.js)

Port from `gamma/src/engines/sampling_utils.py`:

```javascript
export function processLogitsPipeline(logits, { temperature, topK, topP, returnIntermediates = true }) {
  const stages = {};

  // Stage 1: Temperature scaling
  const logitsTemp = temperatureScale(logits, temperature);
  if (returnIntermediates) stages.temperature = logitsTemp.slice();

  // Stage 2: Top-K filtering
  const logitsTopK = topKFilter(logitsTemp, topK);
  if (returnIntermediates) stages.topK = logitsTopK.slice();

  // Stage 3: Top-P (nucleus) filtering
  const logitsTopP = topPFilter(logitsTopK, topP);
  if (returnIntermediates) stages.topP = logitsTopP.slice();

  // Stage 4: Softmax to probabilities
  const probs = softmax(logitsTopP);

  return { probs, stages };
}

function temperatureScale(logits, temp) {
  return logits.map(l => l / Math.max(temp, 1e-6));
}

function topKFilter(logits, k) {
  const sorted = [...logits].map((v, i) => [v, i]).sort((a, b) => b[0] - a[0]);
  const threshold = sorted[k - 1][0];
  return logits.map(l => l >= threshold ? l : -Infinity);
}

function topPFilter(logits, p) {
  const probs = softmax(logits);
  const sorted = [...probs].map((v, i) => [v, i]).sort((a, b) => b[0] - a[0]);

  let cumSum = 0;
  const mask = new Set();
  for (const [prob, idx] of sorted) {
    cumSum += prob;
    mask.add(idx);
    if (cumSum >= p) break;
  }

  return logits.map((l, i) => mask.has(i) ? l : -Infinity);
}
```

### 2.5 Model Registry (core/model-registry.js)

Port from `gamma/src/core/models/model_registry.py`:

```javascript
export const MODEL_CATALOG = {
  'Qwen/Qwen2.5-0.5B-Instruct': {
    name: 'Qwen 2.5 0.5B',
    size: '500M',
    vram: '600MB',
    capabilities: ['fast', 'multilingual'],
    recommended: true,
    engine: 'transformers'
  },
  'HuggingFaceTB/SmolLM2-360M-Instruct': {
    name: 'SmolLM2 360M',
    size: '360M',
    vram: '400MB',
    capabilities: ['fast', 'lightweight'],
    recommended: true,
    engine: 'transformers'
  },
  'Qwen/Qwen2.5-1.5B-Instruct': {
    name: 'Qwen 2.5 1.5B',
    size: '1.5B',
    vram: '1.8GB',
    capabilities: ['balanced', 'multilingual'],
    engine: 'transformers'
  },
  'google/gemma-2-2b-it': {
    name: 'Gemma 2 2B',
    size: '2B',
    vram: '2.5GB',
    capabilities: ['quality', 'reasoning'],
    engine: 'transformers'
  }
};
```

---

## Phase 3: Game Logic & State Management

### 3.1 Game Logic (game/game-logic.js)

Port from `gamma/src/game/game_logic.py`:

```javascript
export function generateChoices(topTokens, engine, numChoices = 4) {
  // Filter tokens
  const filtered = topTokens.filter(token => {
    const text = token.text;
    // Remove special tokens
    if (engine.isSpecialToken(token.id)) return false;
    // Remove code-like patterns
    if (/^[<>\[\]{}()=+*\/]/.test(text)) return false;
    // Remove non-printable
    if (!/\S/.test(text)) return false;
    return true;
  });

  if (filtered.length < numChoices) {
    // Pad with original tokens if needed
    return topTokens.slice(0, numChoices);
  }

  // Correct answer is top token
  const correct = filtered[0];
  const distractors = filtered.slice(1, numChoices);

  // Shuffle for display
  const choices = [correct, ...distractors];
  shuffleArray(choices);

  return {
    choices,
    correctIndex: choices.indexOf(correct),
    correctToken: correct
  };
}
```

### 3.2 Game Session (game/game-session.js)

Port from `gamma/src/game/difficulty_levels.py`:

```javascript
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
      context: result.context,
      choices: result.choices,
      playerChoice: result.playerChoice,
      correctChoice: result.correctChoice,
      isCorrect: result.isCorrect,
      probabilities: result.probabilities,
      attention: result.attention,
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
      EventBus.emit('achievement', { id: 'streak3', name: 'Hot Streak', desc: '3 correct in a row' });
    }
    // ... more achievements
  }

  async save() {
    await Storage.saveSession(this.toJSON());
  }
}
```

### 3.3 Game Controller (game/game-controller.js)

Main game loop orchestrator:

```javascript
export class GameController {
  constructor(engine, config) {
    this.engine = engine;
    this.config = config;
    this.session = new GameSession(config);
    this.context = config.initialPrompt || 'Once upon a time';
    this.isRunning = false;
  }

  async runRound() {
    // 1. Encode current context
    const inputIds = this.engine.encode(this.context);

    // 2. Get model prediction with full outputs
    const prediction = await this.engine.predictNext(inputIds, {
      temperature: this.config.temperature,
      topK: this.config.topK,
      topP: this.config.topP
    });

    // 3. Generate multiple choice options
    const { choices, correctIndex, correctToken } = generateChoices(
      prediction.topTokens,
      this.engine,
      this.config.numChoices
    );

    // 4. Emit round data to UI
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

    // 5. Wait for player choice
    const playerChoice = await this.waitForPlayerChoice();

    // 6. Record result
    const isCorrect = playerChoice === correctIndex;
    this.session.recordRound({
      context: this.context,
      choices,
      playerChoice,
      correctChoice: correctIndex,
      isCorrect,
      probabilities: prediction.probabilities,
      attention: prediction.attention
    });

    // 7. Emit result
    EventBus.emit('round:result', {
      isCorrect,
      correctToken,
      playerChoice,
      probabilities: prediction.topTokens
    });

    // 8. Update context with correct token
    this.context += correctToken.text;

    return isCorrect;
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
```

---

## Phase 4: Mind Meld Multi-Model System

### 4.1 Meld Engine (mind-meld/meld-engine.js)

Port from `gamma/src/mind_meld/core/meld_engine.py`:

```javascript
export class MeldEngine {
  constructor(engines, config) {
    this.engines = engines;  // Array of loaded engines
    this.config = config;
    this.activeIndex = 0;
    this.swapStrategy = this.createStrategy(config.swapStrategy);
    this.vocabTranslator = new VocabularyTranslator();
    this.blender = config.useBlending ? new LogitBlender(config.blendStrategy) : null;
    this.abeEnsemble = config.useABE ? new ABEEnsemble() : null;
    this.stats = new MeldStatistics();
    this.tokenHistory = [];
  }

  async generateToken(context) {
    // Get predictions from all models
    const predictions = await Promise.all(
      this.engines.map(engine => engine.predictNext(
        engine.encode(context),
        this.config
      ))
    );

    let finalLogits;

    if (this.blender) {
      // Soft blend: combine all logits
      finalLogits = this.blender.blend(
        predictions.map(p => p.logitsProcessed),
        this.engines.map(e => e.modelId)
      );
    } else {
      // Hard swap: use active model
      finalLogits = predictions[this.activeIndex].logitsProcessed;

      // Check if should swap
      const lastToken = this.tokenHistory[this.tokenHistory.length - 1];
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

    // ABE agreement check
    if (this.abeEnsemble) {
      const agreed = this.abeEnsemble.findAgreement(predictions);
      if (agreed) {
        finalLogits = agreed.logits;
      }
    }

    // Sample token
    const probs = softmax(finalLogits);
    const tokenId = this.sample(probs);
    const tokenText = this.engines[this.activeIndex].getTokenText(tokenId);

    this.tokenHistory.push(tokenText);
    this.stats.recordToken(tokenText, this.activeIndex);

    return {
      tokenId,
      tokenText,
      activeModel: this.activeIndex,
      allPredictions: predictions
    };
  }
}
```

### 4.2 Swap Strategies (mind-meld/swap-strategies.js)

Port from `gamma/src/mind_meld/strategies/`:

```javascript
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

export class PatternBasedStrategy extends SwapStrategyBase {
  constructor(patterns = ['.', '!', '?', '\n']) {
    super();
    this.patterns = patterns;
  }

  shouldSwap(lastToken) {
    if (this.patterns.some(p => lastToken.includes(p))) {
      this.lastReason = `Pattern match: ${lastToken}`;
      return true;
    }
    return false;
  }
}

export class ConfidenceBasedStrategy extends SwapStrategyBase {
  constructor(threshold = 0.3) {
    super();
    this.threshold = threshold;
  }

  shouldSwap(lastToken, predictions, activeIndex) {
    const activePred = predictions[activeIndex];
    const topProb = Math.max(...softmax(activePred.logitsProcessed));

    if (topProb < this.threshold) {
      this.lastReason = `Low confidence: ${(topProb * 100).toFixed(1)}%`;
      return true;
    }
    return false;
  }

  selectNext(predictions, currentIndex) {
    // Select model with highest confidence
    let maxConf = 0;
    let bestIdx = currentIndex;
    predictions.forEach((pred, idx) => {
      const conf = Math.max(...softmax(pred.logitsProcessed));
      if (conf > maxConf) {
        maxConf = conf;
        bestIdx = idx;
      }
    });
    return bestIdx;
  }
}

export class PerplexityStrategy extends SwapStrategyBase {
  constructor(threshold = 50) {
    super();
    this.threshold = threshold;
  }

  shouldSwap(lastToken, predictions, activeIndex) {
    const probs = softmax(predictions[activeIndex].logitsProcessed);
    const entropy = -probs.reduce((sum, p) => sum + (p > 0 ? p * Math.log(p) : 0), 0);
    const perplexity = Math.exp(entropy);

    if (perplexity > this.threshold) {
      this.lastReason = `High perplexity: ${perplexity.toFixed(1)}`;
      return true;
    }
    return false;
  }
}
```

### 4.3 Vocabulary Translator (mind-meld/vocabulary-translator.js)

Port from `gamma/src/mind_meld/translators/vocabulary_translator.py`:

```javascript
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

    // Map source logits to target vocabulary
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
```

### 4.4 Logit Blender (mind-meld/logit-blender.js)

Port from `gamma/src/mind_meld/core/blending.py`:

```javascript
export class LogitBlender {
  constructor(strategy = 'weighted_average') {
    this.strategy = strategy;
    this.weights = null;  // Dynamic weights
  }

  blend(logitsList, modelNames) {
    switch (this.strategy) {
      case 'weighted_average':
        return this.weightedAverage(logitsList);
      case 'confidence_weighted':
        return this.confidenceWeighted(logitsList);
      case 'max_pooling':
        return this.maxPooling(logitsList);
      default:
        return this.weightedAverage(logitsList);
    }
  }

  weightedAverage(logitsList) {
    const weights = this.weights || logitsList.map(() => 1 / logitsList.length);
    const result = new Float32Array(logitsList[0].length);

    for (let i = 0; i < result.length; i++) {
      result[i] = logitsList.reduce((sum, logits, idx) =>
        sum + logits[i] * weights[idx], 0);
    }

    return result;
  }

  confidenceWeighted(logitsList) {
    // Weight by inverse entropy (higher confidence = higher weight)
    const weights = logitsList.map(logits => {
      const probs = softmax(logits);
      const entropy = -probs.reduce((sum, p) => sum + (p > 0 ? p * Math.log(p) : 0), 0);
      return 1 / (entropy + 1e-6);
    });

    // Normalize weights
    const sum = weights.reduce((a, b) => a + b, 0);
    this.weights = weights.map(w => w / sum);

    return this.weightedAverage(logitsList);
  }

  maxPooling(logitsList) {
    const result = new Float32Array(logitsList[0].length);
    for (let i = 0; i < result.length; i++) {
      result[i] = Math.max(...logitsList.map(l => l[i]));
    }
    return result;
  }
}
```

### 4.5 ABE Ensemble (mind-meld/abe-ensemble.js)

Port from `gamma/src/mind_meld/core/abe_ensemble.py`:

```javascript
export class ABEEnsemble {
  constructor(threshold = 0.1) {
    this.threshold = threshold;
  }

  findAgreement(predictions) {
    // Get top tokens from each model
    const topTokensByModel = predictions.map(pred =>
      pred.topTokens.slice(0, 10)
    );

    // Find tokens where models agree (surface form match)
    const candidates = [];

    for (const token of topTokensByModel[0]) {
      const text = token.text.toLowerCase().trim();

      // Check if other models have similar token
      const matches = topTokensByModel.slice(1).map(tokens =>
        tokens.find(t => t.text.toLowerCase().trim() === text)
      );

      if (matches.every(m => m)) {
        // All models agree on this token
        const combinedProb = [token, ...matches].reduce((sum, t) => sum + t.prob, 0) / predictions.length;
        candidates.push({
          text,
          combinedProb,
          agreement: 1.0
        });
      }
    }

    if (candidates.length === 0) return null;

    // Return highest combined probability candidate
    candidates.sort((a, b) => b.combinedProb - a.combinedProb);
    return candidates[0];
  }
}
```

---

## Phase 5: UI Components & Visualizations

### 5.1 Main Game Panel (ui/game-panel.js)

Central UI component:

```javascript
export class GamePanel {
  constructor(container) {
    this.container = container;
    this.setupDOM();
    this.bindEvents();
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
          <div class="result-icon"></div>
          <div class="result-text"></div>
        </div>

        <div class="action-buttons">
          <button class="btn btn-primary continue-btn hidden">Continue</button>
        </div>
      </div>
    `;

    // Cache DOM references
    this.contextText = this.container.querySelector('.context-text');
    this.choicesGrid = this.container.querySelector('.choices-grid');
    this.probStagesGrid = this.container.querySelector('.prob-stages-grid');
    this.attentionCanvas = this.container.querySelector('.attention-canvas');
  }

  bindEvents() {
    EventBus.on('round:start', (data) => this.showRound(data));
    EventBus.on('round:result', (data) => this.showResult(data));
    EventBus.on('game:end', (data) => this.showGameEnd(data));
  }

  showRound(data) {
    // Update context with attention highlighting
    this.renderContextWithAttention(data.context, data.attention);

    // Render choices
    this.renderChoices(data.choices);

    // Render probability stages
    this.renderProbabilityStages(data.probStages);
  }

  renderChoices(choices) {
    const labels = ['A', 'B', 'C', 'D'];
    this.choicesGrid.innerHTML = choices.map((choice, i) => `
      <button class="choice-btn" data-index="${i}">
        <span class="choice-label">${labels[i]}</span>
        <span class="choice-text">${this.escapeHtml(choice.text)}</span>
        <span class="choice-prob">${(choice.prob * 100).toFixed(1)}%</span>
      </button>
    `).join('');

    // Animate entrance
    this.choicesGrid.querySelectorAll('.choice-btn').forEach((btn, i) => {
      btn.style.animation = `slideIn 0.3s ease ${i * 0.1}s both`;
    });
  }
}
```

### 5.2 Probability Visualization (ui/probability-viz.js)

Bar chart visualization for token probabilities:

```javascript
export class ProbabilityViz {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
  }

  render(topTokens, stageName, maxTokens = 8) {
    const tokens = topTokens.slice(0, maxTokens);
    const width = this.canvas.width;
    const height = this.canvas.height;
    const barHeight = (height - 40) / tokens.length;
    const maxProb = Math.max(...tokens.map(t => t.prob));

    this.ctx.clearRect(0, 0, width, height);

    // Title
    this.ctx.fillStyle = '#a0a0a0';
    this.ctx.font = '11px Courier New';
    this.ctx.fillText(stageName, 10, 15);

    // Bars
    tokens.forEach((token, i) => {
      const y = 25 + i * barHeight;
      const barWidth = (token.prob / maxProb) * (width - 120);

      // Bar background
      this.ctx.fillStyle = 'rgba(0, 255, 255, 0.1)';
      this.ctx.fillRect(60, y, width - 120, barHeight - 4);

      // Bar fill
      const gradient = this.ctx.createLinearGradient(60, 0, 60 + barWidth, 0);
      gradient.addColorStop(0, 'rgba(0, 255, 255, 0.8)');
      gradient.addColorStop(1, 'rgba(255, 0, 255, 0.8)');
      this.ctx.fillStyle = gradient;
      this.ctx.fillRect(60, y, barWidth, barHeight - 4);

      // Token text
      this.ctx.fillStyle = '#e0e0e0';
      this.ctx.textAlign = 'right';
      this.ctx.fillText(this.truncate(token.text, 6), 55, y + barHeight / 2 + 3);

      // Probability
      this.ctx.textAlign = 'left';
      this.ctx.fillText(`${(token.prob * 100).toFixed(1)}%`, width - 55, y + barHeight / 2 + 3);
    });
  }

  truncate(text, maxLen) {
    return text.length > maxLen ? text.slice(0, maxLen) + '…' : text;
  }
}
```

### 5.3 Attention Visualization (ui/attention-viz.js)

Heatmap for attention weights:

```javascript
export class AttentionViz {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
  }

  render(tokens, attentionWeights) {
    if (!attentionWeights || tokens.length === 0) return;

    const width = this.canvas.width;
    const height = this.canvas.height;

    // Normalize attention weights
    const maxWeight = Math.max(...attentionWeights);
    const normalized = attentionWeights.map(w => w / maxWeight);

    this.ctx.clearRect(0, 0, width, height);

    // Calculate token positions
    const tokenWidth = Math.min(60, width / tokens.length);

    tokens.forEach((token, i) => {
      const x = i * tokenWidth;
      const intensity = normalized[i];

      // Background color based on attention
      const r = Math.floor(255 * intensity);
      const g = 0;
      const b = Math.floor(255 * intensity);
      this.ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${0.2 + intensity * 0.6})`;
      this.ctx.fillRect(x, 0, tokenWidth - 2, height);

      // Token text
      this.ctx.fillStyle = intensity > 0.5 ? '#ffffff' : '#a0a0a0';
      this.ctx.font = '10px Courier New';
      this.ctx.textAlign = 'center';

      // Rotate text for narrow columns
      this.ctx.save();
      this.ctx.translate(x + tokenWidth / 2, height - 5);
      this.ctx.rotate(-Math.PI / 4);
      this.ctx.fillText(this.truncate(token, 8), 0, 0);
      this.ctx.restore();
    });
  }
}
```

### 5.4 Model Selector (ui/model-selector.js)

Model download and selection UI:

```javascript
export class ModelSelector {
  constructor(container) {
    this.container = container;
    this.selectedModels = [];
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
              <div class="model-size">${info.size} params</div>
              <div class="model-vram">${info.vram} VRAM</div>
              <div class="model-caps">
                ${info.capabilities.map(c => `<span class="cap-badge">${c}</span>`).join('')}
              </div>
              ${info.recommended ? '<div class="recommended-badge">RECOMMENDED</div>' : ''}
              <div class="download-progress hidden">
                <div class="progress-bar"></div>
                <div class="progress-text">0%</div>
              </div>
            </div>
          `).join('')}
        </div>

        <div class="mind-meld-section">
          <h4>Mind Meld (Multi-Model)</h4>
          <div class="selected-models"></div>
          <button class="btn btn-secondary add-model-btn">+ Add Model</button>
        </div>
      </div>
    `;

    this.bindEvents();
  }

  showDownloadProgress(modelId, progress) {
    const card = this.container.querySelector(`[data-model-id="${modelId}"]`);
    const progressEl = card.querySelector('.download-progress');
    const bar = progressEl.querySelector('.progress-bar');
    const text = progressEl.querySelector('.progress-text');

    progressEl.classList.remove('hidden');
    bar.style.width = `${progress}%`;
    text.textContent = `${Math.round(progress)}%`;
  }
}
```

---

## Phase 6: Styling (Reploid Theme)

### 6.1 GAMMA Theme (styles/gamma-theme.css)

```css
/* GAMMA Game Panel Styles - Extends Reploid Theme */

.gamma-game-panel {
  background: var(--bg-panel);
  border: 1px solid var(--border-default);
  padding: var(--space-lg);
  font-family: var(--font-mono);
}

/* Header with cyberpunk styling */
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
  text-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
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

/* Context display with attention support */
.context-display {
  background: var(--bg-element);
  padding: var(--space-md);
  margin-bottom: var(--space-lg);
  border-left: 2px solid var(--primary);
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

/* Attention-highlighted token */
.context-text .token {
  padding: 2px 4px;
  border-radius: 2px;
  transition: background 0.2s ease;
}

.context-text .token.attention-dim { background: rgba(255, 0, 255, 0.1); }
.context-text .token.attention-light { background: rgba(255, 0, 255, 0.25); }
.context-text .token.attention-medium { background: rgba(255, 0, 255, 0.4); }
.context-text .token.attention-bright { background: rgba(255, 0, 255, 0.6); }
.context-text .token.attention-intense { background: rgba(255, 0, 255, 0.8); color: #fff; }

/* Choice buttons */
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
}

.choice-btn:hover {
  border-color: var(--primary);
  background: var(--bg-hover);
  box-shadow: 0 0 10px rgba(0, 255, 255, 0.2);
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
  color: var(--text-primary);
  font-size: 14px;
}

.choice-prob {
  color: var(--text-muted);
  font-size: 11px;
}

/* Probability stages visualization */
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

.prob-stage-title {
  color: var(--text-muted);
  font-size: 10px;
  text-transform: uppercase;
  margin-bottom: var(--space-sm);
}

/* Attention canvas container */
.attention-container {
  margin-bottom: var(--space-lg);
  height: 80px;
  background: var(--bg-element);
  border: 1px solid var(--border-subtle);
  overflow: hidden;
}

.attention-canvas {
  width: 100%;
  height: 100%;
}

/* Model selector cards */
.model-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
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

.model-card.selected {
  border-color: var(--primary);
  box-shadow: 0 0 15px rgba(0, 255, 255, 0.3);
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

.model-size, .model-vram {
  color: var(--text-secondary);
  font-size: 11px;
}

.cap-badge {
  display: inline-block;
  background: rgba(0, 255, 255, 0.1);
  color: var(--primary);
  padding: 2px 6px;
  font-size: 9px;
  margin: 2px;
  text-transform: uppercase;
}

/* Download progress */
.download-progress {
  margin-top: var(--space-sm);
}

.progress-bar {
  height: 4px;
  background: var(--bg-panel);
  position: relative;
  overflow: hidden;
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

/* Mind Meld visualization */
.meld-indicator {
  display: flex;
  gap: var(--space-sm);
  margin-bottom: var(--space-md);
}

.model-indicator {
  padding: 4px 8px;
  font-size: 11px;
  border: 1px solid var(--border-default);
}

.model-indicator.active {
  border-color: var(--primary);
  background: rgba(0, 255, 255, 0.2);
  animation: pulse 1s ease infinite;
}

.model-indicator[data-model="0"] { color: #00bfff; }  /* Blue */
.model-indicator[data-model="1"] { color: #00ff00; }  /* Green */
.model-indicator[data-model="2"] { color: #ffd700; }  /* Yellow */
.model-indicator[data-model="3"] { color: #ff00ff; }  /* Magenta */

/* Result feedback */
.result-display {
  text-align: center;
  padding: var(--space-lg);
}

.result-icon {
  font-size: 48px;
  margin-bottom: var(--space-md);
}

.result-display.correct .result-icon::before { content: '✓'; color: var(--success); }
.result-display.incorrect .result-icon::before { content: '✗'; color: var(--danger); }

/* Achievement toast */
.achievement-toast {
  background: var(--bg-panel);
  border: 1px solid var(--warning);
  padding: var(--space-md);
  display: flex;
  align-items: center;
  gap: var(--space-md);
  animation: slideIn 0.3s ease;
}

.achievement-icon {
  font-size: 24px;
}

.achievement-name {
  color: var(--warning);
  font-weight: bold;
}

.achievement-desc {
  color: var(--text-secondary);
  font-size: 11px;
}

/* Animations */
@keyframes slideIn {
  from {
    transform: translateY(-12px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* Responsive */
@media (max-width: 768px) {
  .choices-grid {
    grid-template-columns: 1fr;
  }

  .prob-stages-grid {
    grid-template-columns: 1fr;
  }
}
```

---

## Phase 7: Integration & Storage

### 7.1 IndexedDB Storage (utils/storage.js)

```javascript
const DB_NAME = 'gamma-game';
const DB_VERSION = 1;

export const Storage = {
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

      request.onsuccess = () => {
        this.db = request.result;
        resolve();
      };

      request.onerror = reject;
    });
  },

  async saveSession(session) {
    const tx = this.db.transaction('sessions', 'readwrite');
    await tx.objectStore('sessions').add(session);
  },

  async getSessions() {
    const tx = this.db.transaction('sessions', 'readonly');
    return tx.objectStore('sessions').getAll();
  },

  async saveSetting(key, value) {
    const tx = this.db.transaction('settings', 'readwrite');
    await tx.objectStore('settings').put({ key, value });
  },

  async getSetting(key, defaultValue = null) {
    const tx = this.db.transaction('settings', 'readonly');
    const result = await tx.objectStore('settings').get(key);
    return result?.value ?? defaultValue;
  }
};
```

### 7.2 Event Bus (utils/event-bus.js)

```javascript
export const EventBus = {
  listeners: new Map(),

  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);

    return () => this.off(event, callback);
  },

  off(event, callback) {
    const callbacks = this.listeners.get(event);
    if (callbacks) {
      const index = callbacks.indexOf(callback);
      if (index > -1) callbacks.splice(index, 1);
    }
  },

  emit(event, data) {
    const callbacks = this.listeners.get(event) || [];
    callbacks.forEach(cb => cb(data));
  }
};
```

---

## Phase 8: Entry Point & Bootstrap

### 8.1 Main Entry (index.html)

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>GAMMA - Token Prediction Game</title>
  <link rel="stylesheet" href="../reploid/styles/theme.css">
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
```

### 8.2 App Bootstrap (app.js)

```javascript
import { Storage } from './utils/storage.js';
import { EventBus } from './utils/event-bus.js';
import { EngineFactory } from './engines/engine-factory.js';
import { GameController } from './game/game-controller.js';
import { MeldEngine } from './mind-meld/meld-engine.js';
import { GamePanel } from './ui/game-panel.js';
import { ModelSelector } from './ui/model-selector.js';

export class GammaApp {
  constructor(container) {
    this.container = container;
  }

  async init() {
    await Storage.init();

    // Load saved settings
    const savedModel = await Storage.getSetting('selectedModel', 'Qwen/Qwen2.5-0.5B-Instruct');
    const savedConfig = await Storage.getSetting('gameConfig', {
      temperature: 0.9,
      topK: 64,
      topP: 0.95,
      maxRounds: 8
    });

    // Show model selector first
    this.modelSelector = new ModelSelector(this.container);
    this.modelSelector.render();

    EventBus.on('model:selected', async (modelId) => {
      await this.startGame(modelId, savedConfig);
    });
  }

  async startGame(modelId, config) {
    // Show loading state
    this.container.innerHTML = '<div class="loading">Loading model...</div>';

    // Create engine
    const engine = EngineFactory.getEngine(modelId);

    EventBus.on('model:progress', (progress) => {
      this.container.querySelector('.loading').textContent =
        `Loading: ${progress.status} ${Math.round(progress.progress * 100)}%`;
    });

    await engine.load();

    // Create game UI
    this.gamePanel = new GamePanel(this.container);

    // Create and run game
    this.gameController = new GameController(engine, config);
    await this.gameController.runGame();
  }
}
```

---

## Summary

### Files to Create (30+ files)

- **Core**: 4 files (config, sampling, engine-interface, model-registry)
- **Engines**: 3 files (factory, transformers, webllm)
- **Game**: 4 files (logic, session, controller, tutorial)
- **Mind Meld**: 5 files (meld-engine, strategies, vocab-translator, blender, abe)
- **UI**: 6 files (game-panel, prob-viz, attention-viz, model-selector, progress, toast)
- **Utils**: 2 files (storage, event-bus)
- **Styles**: 1 file (gamma-theme.css)
- **Bootstrap**: 2 files (index.html, app.js)

### Key Features

1. **Full game loop** with token prediction, scoring, achievements
2. **Attention visualization** with color-coded heatmaps
3. **Probability pipeline visualization** showing all 4 stages
4. **Model download** with progress indicators
5. **Mind Meld** multi-model collaboration with swap strategies
6. **Reploid cyberpunk theme** (cyan/magenta, scanlines, glow effects)
7. **Persistent sessions** via IndexedDB
8. **Mobile responsive** design

### Limitations vs Native GAMMA

- Attention access depends on Transformers.js model support
- Smaller models only (500M-2B) due to browser memory
- No KV cache bridging (complex for web)
- Simplified vocabulary translation

### Reference Files (Original GAMMA)

| Web File | Source File |
|----------|-------------|
| core/config.js | src/core/config.py |
| core/engine-interface.js | src/core/engine_interface.py |
| core/sampling-utils.js | src/engines/sampling_utils.py |
| core/model-registry.js | src/core/models/model_registry.py |
| engines/engine-factory.js | src/engines/engine_factory.py |
| game/game-logic.js | src/game/game_logic.py |
| game/game-session.js | src/game/difficulty_levels.py |
| game/game-controller.js | src/game/cli.py |
| mind-meld/meld-engine.js | src/mind_meld/core/meld_engine.py |
| mind-meld/swap-strategies.js | src/mind_meld/strategies/*.py |
| mind-meld/vocabulary-translator.js | src/mind_meld/translators/*.py |
| mind-meld/logit-blender.js | src/mind_meld/core/blending.py |
| mind-meld/abe-ensemble.js | src/mind_meld/core/abe_ensemble.py |
