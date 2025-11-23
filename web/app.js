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

    const savedModel = await Storage.getSetting('selectedModel', 'HuggingFaceTB/SmolLM2-360M-Instruct');
    const savedConfig = await Storage.getSetting('gameConfig', {
      temperature: 0.9,
      topK: 64,
      topP: 0.95,
      maxRounds: 16
    });

    this.modelSelector = new ModelSelector(this.container);
    this.modelSelector.render();

    EventBus.on('model:selected', (data) => {
      const config = { ...savedConfig, initialPrompt: data.prompt };
      this.startGame(data.modelId, config);
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