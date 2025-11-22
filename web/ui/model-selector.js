import { MODEL_CATALOG, PROVIDER_COLORS, MODEL_SIZE_CATEGORIES } from '../core/model-registry.js';
import { EventBus } from '../utils/event-bus.js';

export class ModelSelector {
  constructor(container) {
    this.container = container;
  }

  renderModelCard(id, info) {
    return `
      <div class="model-card ${info.recommended ? 'recommended' : ''}" data-model-id="${id}">
        <div class="model-header">
          <div class="model-name">${info.name}</div>
          <span class="provider-badge" style="color: ${PROVIDER_COLORS[info.provider] || '#888'}">${info.provider}</span>
        </div>
        <div class="model-specs">${info.size} • ${info.downloadSize || info.vram} • ${info.released}</div>
        ${info.warning ? `<div class="model-warning">${info.warning}</div>` : ''}
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

  render() {
    const smallModels = MODEL_SIZE_CATEGORIES.small.map(id => [id, MODEL_CATALOG[id]]).filter(([_, m]) => m);
    const mediumModels = MODEL_SIZE_CATEGORIES.medium.map(id => [id, MODEL_CATALOG[id]]).filter(([_, m]) => m);
    const largeModels = MODEL_SIZE_CATEGORIES.large.map(id => [id, MODEL_CATALOG[id]]).filter(([_, m]) => m);

    this.container.innerHTML = `
      <div class="model-selector">
        <h3>Select Model</h3>

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

        <div class="model-section">
          <h4 class="section-title">Large (Experimental)</h4>
          <div class="model-grid">
            ${largeModels.map(([id, info]) => this.renderModelCard(id, info)).join('')}
          </div>
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