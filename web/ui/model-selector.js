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