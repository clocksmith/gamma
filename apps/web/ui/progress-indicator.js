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