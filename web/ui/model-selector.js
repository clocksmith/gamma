import { MODEL_CATALOG, PROVIDER_COLORS, MODEL_SIZE_CATEGORIES } from '../core/model-registry.js';
import { EventBus } from '../utils/event-bus.js';
import { STARTING_PROMPTS, getRandomPrompt } from '../core/prompts.js';
import { SettingsPanel } from './settings-panel.js';

export class ModelSelector {
  constructor(container) {
    this.container = container;
    this.selectedPrompt = getRandomPrompt();
    this.selectedModelId = 'HuggingFaceTB/SmolLM2-360M-Instruct'; // default to second small model
    this.settingsPanel = null;
  }

  renderModelCard(id, info) {
    return `
      <div class="model-card ${info.recommended ? 'recommended' : ''}" data-model-id="${id}">
        <div class="model-header">
          <div class="model-name">${info.name}</div>
          <span class="provider-badge" style="color: ${PROVIDER_COLORS[info.provider] || '#888'}">${info.provider}</span>
        </div>
        <div class="model-specs">${info.size} • ${info.downloadSize || info.vram} • ${info.released}</div>
        <div class="model-caps">
          ${info.capabilities.map(c => `<span class="cap-badge">${c}</span>`).join('')}
        </div>
        <div class="download-progress hidden">
          <div class="progress-bar"></div>
          <div class="progress-text">0%</div>
        </div>
      </div>
    `;
  }

  async render() {
    const smallModels = MODEL_SIZE_CATEGORIES.small.map(id => [id, MODEL_CATALOG[id]]).filter(([_, m]) => m);
    const mediumModels = MODEL_SIZE_CATEGORIES.medium.map(id => [id, MODEL_CATALOG[id]]).filter(([_, m]) => m);

    this.container.innerHTML = `
      <div class="model-selector">
        <div class="start-section top">
          <button class="btn start-game-btn">Start Game</button>
        </div>

        <div class="prompt-section">
          <h4 class="section-title">Starting Text</h4>
          <div class="prompt-controls">
            <input type="text" class="prompt-input" value="${this.escapeHtml(this.selectedPrompt)}" placeholder="Enter starting text...">
            <button class="random-prompt-btn">Random</button>
            <select class="prompt-select">
              <option value="">Pick from list...</option>
              ${STARTING_PROMPTS.map(p => `<option value="${this.escapeHtml(p)}">${this.escapeHtml(p.length > 40 ? p.slice(0, 40) + '...' : p)}</option>`).join('')}
            </select>
          </div>
        </div>

        <!-- Settings Panel (collapsible) -->
        <div class="settings-container"></div>

        <div class="model-section">
          <h4 class="section-title">Small (Fast)</h4>
          <div class="model-grid">
            ${smallModels.map(([id, info]) => this.renderModelCard(id, info)).join('')}
          </div>
        </div>

        <div class="model-section">
          <h4 class="section-title">Medium</h4>
          <div class="model-grid">
            ${mediumModels.map(([id, info]) => this.renderModelCard(id, info)).join('')}
          </div>
        </div>
      </div>
    `;

    // Initialize settings panel
    const settingsContainer = this.container.querySelector('.settings-container');
    if (settingsContainer) {
      this.settingsPanel = new SettingsPanel(settingsContainer);
      await this.settingsPanel.loadSavedConfig();
      this.settingsPanel.render();
    } else {
      console.warn('Settings container not found in DOM');
    }

    // Prompt controls
    const promptInput = this.container.querySelector('.prompt-input');
    const randomBtn = this.container.querySelector('.random-prompt-btn');
    const promptSelect = this.container.querySelector('.prompt-select');

    promptInput.addEventListener('input', () => {
      this.selectedPrompt = promptInput.value;
    });

    randomBtn.addEventListener('click', () => {
      this.selectedPrompt = getRandomPrompt();
      promptInput.value = this.selectedPrompt;
      promptSelect.value = '';
    });

    promptSelect.addEventListener('change', () => {
      if (promptSelect.value) {
        this.selectedPrompt = promptSelect.value;
        promptInput.value = this.selectedPrompt;
      }
    });

    // Model selection
    this.container.querySelectorAll('.model-card').forEach(card => {
      card.addEventListener('click', () => {
        this.container.querySelectorAll('.model-card').forEach(c => c.classList.remove('selected'));
        card.classList.add('selected');
        this.selectedModelId = card.dataset.modelId;
      });
    });

    // Mark default as selected
    const defaultCard = this.container.querySelector(`[data-model-id="${this.selectedModelId}"]`);
    if (defaultCard) defaultCard.classList.add('selected');

    // Start game button
    const startBtn = this.container.querySelector('.start-game-btn');
    startBtn.addEventListener('click', () => {
      if (this.selectedModelId) {
        const config = this.settingsPanel ? this.settingsPanel.getConfig() : {};
        EventBus.emit('model:selected', {
          modelId: this.selectedModelId,
          prompt: this.selectedPrompt,
          config: config
        });
      }
    });
  }

  getConfig() {
    return this.settingsPanel ? this.settingsPanel.getConfig() : {};
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML.replace(/"/g, '&quot;');
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