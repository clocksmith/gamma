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

    // Render Attention heatmap
    const tokens = data.context.split(/\s+/);
    if (data.attention && data.attention.length > 0) {
      const displayTokens = tokens.slice(-data.attention.length);
      this.attentionViz.render(displayTokens, data.attention);
    } else {
      // Generate synthetic attention based on position (recency bias)
      // This shows typical LLM behavior where recent tokens get more attention
      const numTokens = Math.min(tokens.length, 20);
      const displayTokens = tokens.slice(-numTokens);
      const syntheticAttention = displayTokens.map((_, i) => {
        // Exponential increase towards end (recency bias)
        return Math.pow((i + 1) / numTokens, 2);
      });
      this.attentionViz.render(displayTokens, syntheticAttention);
    }

    this.renderChoices(data.choices);
    // Hide probabilities until after guess
    this.probStagesGrid.innerHTML = '';
    // Store for later reveal
    this.pendingTopTokens = data.topTokens;
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

  renderProbabilities(stages, topTokens) {
    if (!topTokens || topTokens.length === 0) {
      this.probStagesGrid.innerHTML = '';
      return;
    }

    this.probStagesGrid.innerHTML = `
      <div class="prob-label">Top Predictions</div>
      <div class="top-tokens-list">
        ${topTokens.slice(0, 10).map(token => `
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

    // Reveal top tokens after guess
    this.renderProbabilities(null, this.pendingTopTokens);
  }
}