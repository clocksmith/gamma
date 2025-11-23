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

    // Render context with attention highlighting
    const tokens = data.context.split(/\s+/);
    let attentionWeights;

    if (data.attention && data.attention.length > 0) {
      attentionWeights = data.attention;
    } else {
      // Generate synthetic attention based on position (recency bias)
      const numTokens = Math.min(tokens.length, 20);
      attentionWeights = tokens.slice(-numTokens).map((_, i) => {
        return Math.pow((i + 1) / numTokens, 2);
      });
    }

    this.renderAttentionText(tokens, attentionWeights);

    this.renderChoices(data.choices);
    // Hide probabilities until after guess
    this.probStagesGrid.innerHTML = '';
    // Store for later reveal
    this.pendingTopTokens = data.topTokens;
  }

  renderChoices(choices) {
    const labels = ['A', 'B', 'C', 'D'];
    this.choicesGrid.innerHTML = choices.map((choice, i) => `
      <button class="choice-btn" data-index="${i}" data-prob="${(choice.prob * 100).toFixed(1)}">
        <span class="choice-label">${labels[i]}</span>
        <div class="choice-content">
          <span class="choice-text">${choice.text}</span>
          <span class="choice-prob hidden"></span>
        </div>
      </button>
    `).join('');

    this.choicesGrid.querySelectorAll('.choice-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        EventBus.emit('player:choice', parseInt(btn.dataset.index));
      });
    });
  }

  renderProbabilities(stages, topTokens) {
    if (!topTokens || topTokens.length === 0) {
      this.probStagesGrid.innerHTML = '';
      return;
    }

    this.probStagesGrid.innerHTML = `
      <div class="top-tokens-list">
        ${topTokens.slice(0, 8).map(token => `
          <div class="top-token-item">
            <span class="top-token-text">${this.escapeHtml(token.text)}</span>
            <span class="top-token-prob">${(token.prob * 100).toFixed(1)}%</span>
          </div>
        `).join('')}
      </div>
    `;
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  // Viridis-like colorblind-friendly palette
  getHeatmapColor(t) {
    const colors = [
      [68, 1, 84],     // dark purple
      [59, 82, 139],   // blue-purple
      [33, 144, 140],  // teal
      [93, 201, 99],   // green
      [253, 231, 37]   // yellow
    ];

    const idx = t * (colors.length - 1);
    const i = Math.floor(idx);
    const f = idx - i;

    if (i >= colors.length - 1) return colors[colors.length - 1];

    const c1 = colors[i];
    const c2 = colors[i + 1];

    return [
      Math.round(c1[0] + f * (c2[0] - c1[0])),
      Math.round(c1[1] + f * (c2[1] - c1[1])),
      Math.round(c1[2] + f * (c2[2] - c1[2]))
    ];
  }

  renderAttentionText(tokens, weights) {
    const numWeights = weights.length;
    const displayTokens = tokens.slice(-numWeights);
    const maxWeight = Math.max(...weights, 0.0001);
    const normalized = weights.map(w => w / maxWeight);

    // Render tokens with colors and aligned numbers underneath
    const tokensHtml = displayTokens.map((token, i) => {
      const intensity = normalized[i];
      const [r, g, b] = this.getHeatmapColor(intensity);
      const textColor = intensity > 0.7 ? '#000' : '#fff';
      const value = normalized[i].toFixed(2);
      return `
        <div class="attn-item">
          <span class="attn-token" style="background:rgb(${r},${g},${b});color:${textColor}">${this.escapeHtml(token)}</span>
          <span class="attn-number" style="color:rgb(${r},${g},${b})">${value}</span>
        </div>
      `;
    }).join('');

    this.contextText.innerHTML = `<div class="attn-row">${tokensHtml}</div>`;
  }

  showResult(data) {
    this.resultDisplay.classList.remove('hidden');
    this.resultDisplay.className = `result-display ${data.isCorrect ? 'correct' : 'incorrect'}`;
    this.resultDisplay.querySelector('.result-text').textContent =
      data.isCorrect ? 'Correct!' : `Missed it. The answer was: ${data.correctToken.text}`;

    this.continueBtn.classList.remove('hidden');

    // Highlight choices and reveal probabilities
    const buttons = this.choicesGrid.querySelectorAll('.choice-btn');
    buttons.forEach((btn, i) => {
      btn.disabled = true;
      if (i === data.correctChoice) btn.classList.add('correct');
      else if (i === data.playerChoice && !data.isCorrect) btn.classList.add('incorrect');

      // Reveal probability
      const probEl = btn.querySelector('.choice-prob');
      probEl.textContent = btn.dataset.prob + '%';
      probEl.classList.remove('hidden');
    });

    // Reveal top tokens after guess
    this.renderProbabilities(null, this.pendingTopTokens);
  }
}