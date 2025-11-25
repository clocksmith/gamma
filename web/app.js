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

  _buildProgressBar(percent) {
    const filled = Math.round(percent / 5);
    const empty = 20 - filled;
    return '[' + '='.repeat(filled) + ' '.repeat(empty) + ']';
  }

  _formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  }

  async init() {
    await Storage.init();
    Toast.init();

    const savedModel = await Storage.getSetting('selectedModel', 'HuggingFaceTB/SmolLM2-360M-Instruct');

    this.modelSelector = new ModelSelector(this.container);
    await this.modelSelector.render();

    EventBus.on('model:selected', (data) => {
      // Merge config from settings panel with prompt
      const config = {
        ...data.config,
        initialPrompt: data.prompt
      };
      this.startGame(data.modelId, config);
    });

    EventBus.on('achievement', (ach) => Toast.show(ach));
  }

  async startGame(modelId, config) {
    this.container.innerHTML = '<div class="loading-screen"><div>INITIALIZING ENGINE...</div></div>';

    try {
      const engine = EngineFactory.getEngine(modelId);

      // Track loading state for detailed progress
      let loadingState = {
        tokenizerDone: false,
        modelPercent: 0,
        stage: 'initializing'
      };

      EventBus.on('model:progress', (p) => {
        const loadingEl = this.container.querySelector('.loading-screen');
        if (!loadingEl) return;

        // Update loading state
        if (p.type === 'tokenizer' && p.status === 'done') {
          loadingState.tokenizerDone = true;
        }
        if (p.status === 'progress' && p.total > 0) {
          loadingState.modelPercent = Math.round((p.loaded / p.total) * 100) || 0;
        }
        if (p.stage) {
          loadingState.stage = p.stage;
        }

        // Build detailed progress display
        const stageLabel = p.stageLabel || 'Loading...';
        const progressBar = this._buildProgressBar(loadingState.modelPercent);
        const sizeInfo = p.total ? this._formatBytes(p.loaded) + ' / ' + this._formatBytes(p.total) : '';

        loadingEl.innerHTML = `
          <div class="loading-content">
            <div class="loading-stage">${stageLabel}</div>
            <div class="loading-progress-bar">${progressBar}</div>
            <div class="loading-percent">${loadingState.modelPercent}%</div>
            <div class="loading-size">${sizeInfo}</div>
            <div class="loading-steps">
              <span class="${loadingState.tokenizerDone ? 'done' : 'pending'}">Tokenizer</span>
              <span class="${loadingState.modelPercent > 0 ? (loadingState.modelPercent >= 100 ? 'done' : 'active') : 'pending'}">Model</span>
              <span class="${p.stage === 'model_compile' ? 'active' : 'pending'}">Compile</span>
            </div>
          </div>
        `;
      });

      await engine.load();

      this.gamePanel = new GamePanel(this.container);
      this.gamePanel.setModelName(modelId);
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