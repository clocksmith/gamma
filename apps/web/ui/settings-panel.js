import { EventBus } from '../utils/event-bus.js';
import { Storage } from '../utils/storage.js';
import {
  DEFAULT_TEMPERATURE,
  DEFAULT_TOP_K,
  DEFAULT_TOP_P,
  DEFAULT_MAX_ROUNDS,
  DEFAULT_NUM_CHOICES
} from '../core/config.js';

/**
 * Settings Panel - Provides optional configuration for advanced users
 *
 * Features:
 * - Sampling parameters (temperature, top-k, top-p)
 * - Game settings (max rounds, number of choices)
 * - Display preferences (show probabilities, colorblind mode)
 * - Collapsible "Advanced Settings" section
 */
export class SettingsPanel {
  constructor(container) {
    this.container = container;
    this.isExpanded = false;
    this.config = {
      temperature: DEFAULT_TEMPERATURE,
      topK: DEFAULT_TOP_K,
      topP: DEFAULT_TOP_P,
      maxRounds: DEFAULT_MAX_ROUNDS,
      numChoices: DEFAULT_NUM_CHOICES,
      showProbabilities: true,
      showAttentionHistory: true,
      colorblindMode: false,
      keyboardShortcuts: true
    };
  }

  async loadSavedConfig() {
    const saved = await Storage.getSetting('gameConfig', {});
    this.config = { ...this.config, ...saved };
  }

  async saveConfig() {
    await Storage.saveSetting('gameConfig', this.config);
    EventBus.emit('config:updated', this.config);
  }

  getConfig() {
    return { ...this.config };
  }

  render() {
    this.container.innerHTML = `
      <div class="settings-panel ${this.isExpanded ? 'expanded' : 'collapsed'}">
        <button class="settings-toggle" aria-expanded="${this.isExpanded}" aria-controls="settings-content">
          <span class="settings-icon">⎈</span>
          <span class="settings-label">Settings</span>
          <span class="settings-chevron">${this.isExpanded ? '▼' : '▶'}</span>
        </button>

        <div class="settings-content" id="settings-content" ${this.isExpanded ? '' : 'hidden'}>
          <!-- Quick Settings (always visible when expanded) -->
          <div class="settings-section quick-settings">
            <h4 class="settings-section-title">Game Settings</h4>

            <div class="setting-row">
              <label for="setting-max-rounds">
                <span class="setting-name">Rounds</span>
                <span class="setting-hint">Number of rounds per game</span>
              </label>
              <div class="setting-control">
                <input type="range" id="setting-max-rounds"
                       min="5" max="30" step="1"
                       value="${this.config.maxRounds}">
                <span class="setting-value">${this.config.maxRounds}</span>
              </div>
            </div>

            <div class="setting-row">
              <label for="setting-num-choices">
                <span class="setting-name">Choices</span>
                <span class="setting-hint">Options per round (2-6)</span>
              </label>
              <div class="setting-control">
                <select id="setting-num-choices" class="border-default">
                  <option value="2" ${this.config.numChoices === 2 ? 'selected' : ''}>2 choices</option>
                  <option value="3" ${this.config.numChoices === 3 ? 'selected' : ''}>3 choices</option>
                  <option value="4" ${this.config.numChoices === 4 ? 'selected' : ''}>4 choices (default)</option>
                  <option value="5" ${this.config.numChoices === 5 ? 'selected' : ''}>5 choices</option>
                  <option value="6" ${this.config.numChoices === 6 ? 'selected' : ''}>6 choices</option>
                </select>
              </div>
            </div>
          </div>

          <!-- Advanced Settings (collapsible) -->
          <details class="settings-section advanced-settings">
            <summary class="advanced-toggle">
              <span>Advanced Sampling</span>
              <span class="advanced-hint">Temperature, Top-K, Top-P</span>
            </summary>

            <div class="advanced-content">
              <div class="setting-row">
                <label for="setting-temperature">
                  <span class="setting-name">Temperature</span>
                  <span class="setting-hint">Higher = more random</span>
                </label>
                <div class="setting-control">
                  <input type="range" id="setting-temperature"
                         min="0.1" max="2.0" step="0.1"
                         value="${this.config.temperature}">
                  <span class="setting-value">${this.config.temperature.toFixed(1)}</span>
                </div>
              </div>

              <div class="setting-row">
                <label for="setting-top-k">
                  <span class="setting-name">Top-K</span>
                  <span class="setting-hint">Limit to top K tokens</span>
                </label>
                <div class="setting-control">
                  <input type="range" id="setting-top-k"
                         min="1" max="200" step="1"
                         value="${this.config.topK}">
                  <span class="setting-value">${this.config.topK}</span>
                </div>
              </div>

              <div class="setting-row">
                <label for="setting-top-p">
                  <span class="setting-name">Top-P</span>
                  <span class="setting-hint">Nucleus sampling threshold</span>
                </label>
                <div class="setting-control">
                  <input type="range" id="setting-top-p"
                         min="0.1" max="1.0" step="0.05"
                         value="${this.config.topP}">
                  <span class="setting-value">${this.config.topP.toFixed(2)}</span>
                </div>
              </div>

              <div class="sampling-presets">
                <span class="presets-label">Presets:</span>
                <button class="preset-btn" data-preset="deterministic" title="Low randomness">Focused</button>
                <button class="preset-btn" data-preset="balanced" title="Balanced sampling">Balanced</button>
                <button class="preset-btn" data-preset="creative" title="High randomness">Creative</button>
              </div>
            </div>
          </details>

          <!-- Display Settings -->
          <details class="settings-section display-settings">
            <summary class="advanced-toggle">
              <span>Display Options</span>
              <span class="advanced-hint">UI preferences</span>
            </summary>

            <div class="advanced-content">
              <div class="setting-row checkbox-row">
                <label for="setting-show-probs">
                  <span class="setting-name">Show Probabilities</span>
                  <span class="setting-hint">Display token probabilities after guess</span>
                </label>
                <input type="checkbox" id="setting-show-probs"
                       ${this.config.showProbabilities ? 'checked' : ''}>
              </div>

              <div class="setting-row checkbox-row">
                <label for="setting-show-attention">
                  <span class="setting-name">Attention History</span>
                  <span class="setting-hint">Show sidebar attention heatmap</span>
                </label>
                <input type="checkbox" id="setting-show-attention"
                       ${this.config.showAttentionHistory ? 'checked' : ''}>
              </div>

              <div class="setting-row checkbox-row">
                <label for="setting-colorblind">
                  <span class="setting-name">High Contrast Mode</span>
                  <span class="setting-hint">Enhanced color accessibility</span>
                </label>
                <input type="checkbox" id="setting-colorblind"
                       ${this.config.colorblindMode ? 'checked' : ''}>
              </div>

              <div class="setting-row checkbox-row">
                <label for="setting-keyboard">
                  <span class="setting-name">Keyboard Shortcuts</span>
                  <span class="setting-hint">Use 1-4, A-D, Space keys</span>
                </label>
                <input type="checkbox" id="setting-keyboard"
                       ${this.config.keyboardShortcuts ? 'checked' : ''}>
              </div>
            </div>
          </details>

          <!-- Reset button -->
          <div class="settings-actions">
            <button class="btn btn-secondary reset-settings-btn">Reset to Defaults</button>
          </div>
        </div>
      </div>
    `;

    this._bindEvents();
  }

  _bindEvents() {
    // Toggle panel
    const toggleBtn = this.container.querySelector('.settings-toggle');
    toggleBtn.addEventListener('click', () => {
      this.isExpanded = !this.isExpanded;
      this.render();
    });

    if (!this.isExpanded) return;

    // Max rounds slider
    const maxRoundsInput = this.container.querySelector('#setting-max-rounds');
    maxRoundsInput.addEventListener('input', (e) => {
      this.config.maxRounds = parseInt(e.target.value);
      e.target.nextElementSibling.textContent = this.config.maxRounds;
      this.saveConfig();
    });

    // Num choices select
    const numChoicesSelect = this.container.querySelector('#setting-num-choices');
    numChoicesSelect.addEventListener('change', (e) => {
      this.config.numChoices = parseInt(e.target.value);
      this.saveConfig();
    });

    // Temperature slider
    const tempInput = this.container.querySelector('#setting-temperature');
    tempInput.addEventListener('input', (e) => {
      this.config.temperature = parseFloat(e.target.value);
      e.target.nextElementSibling.textContent = this.config.temperature.toFixed(1);
      this.saveConfig();
    });

    // Top-K slider
    const topKInput = this.container.querySelector('#setting-top-k');
    topKInput.addEventListener('input', (e) => {
      this.config.topK = parseInt(e.target.value);
      e.target.nextElementSibling.textContent = this.config.topK;
      this.saveConfig();
    });

    // Top-P slider
    const topPInput = this.container.querySelector('#setting-top-p');
    topPInput.addEventListener('input', (e) => {
      this.config.topP = parseFloat(e.target.value);
      e.target.nextElementSibling.textContent = this.config.topP.toFixed(2);
      this.saveConfig();
    });

    // Presets
    this.container.querySelectorAll('.preset-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        this._applyPreset(btn.dataset.preset);
      });
    });

    // Checkboxes
    const showProbsCheckbox = this.container.querySelector('#setting-show-probs');
    showProbsCheckbox.addEventListener('change', (e) => {
      this.config.showProbabilities = e.target.checked;
      this.saveConfig();
    });

    const showAttentionCheckbox = this.container.querySelector('#setting-show-attention');
    showAttentionCheckbox.addEventListener('change', (e) => {
      this.config.showAttentionHistory = e.target.checked;
      this.saveConfig();
      EventBus.emit('ui:toggleAttentionHistory', e.target.checked);
    });

    const colorblindCheckbox = this.container.querySelector('#setting-colorblind');
    colorblindCheckbox.addEventListener('change', (e) => {
      this.config.colorblindMode = e.target.checked;
      this.saveConfig();
      document.body.classList.toggle('high-contrast', e.target.checked);
    });

    const keyboardCheckbox = this.container.querySelector('#setting-keyboard');
    keyboardCheckbox.addEventListener('change', (e) => {
      this.config.keyboardShortcuts = e.target.checked;
      this.saveConfig();
      EventBus.emit('ui:toggleKeyboardShortcuts', e.target.checked);
    });

    // Reset button
    const resetBtn = this.container.querySelector('.reset-settings-btn');
    resetBtn.addEventListener('click', () => {
      this._resetToDefaults();
    });
  }

  _applyPreset(preset) {
    const presets = {
      deterministic: { temperature: 0.3, topK: 10, topP: 0.5 },
      balanced: { temperature: 0.9, topK: 64, topP: 0.95 },
      creative: { temperature: 1.5, topK: 150, topP: 0.98 }
    };

    if (presets[preset]) {
      Object.assign(this.config, presets[preset]);
      this.saveConfig();
      this.render(); // Re-render to update slider positions
    }
  }

  _resetToDefaults() {
    this.config = {
      temperature: DEFAULT_TEMPERATURE,
      topK: DEFAULT_TOP_K,
      topP: DEFAULT_TOP_P,
      maxRounds: DEFAULT_MAX_ROUNDS,
      numChoices: DEFAULT_NUM_CHOICES,
      showProbabilities: true,
      showAttentionHistory: true,
      colorblindMode: false,
      keyboardShortcuts: true
    };
    this.saveConfig();
    this.render();
    document.body.classList.remove('high-contrast');
  }
}
