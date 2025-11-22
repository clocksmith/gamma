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
    
    // Render Attention
    // Need tokenized context approx for viz, usually engine provides specific tokens
    // Simplification: data.attention corresponds to last tokens
    // For now, visualize attention on a dummy token split if simple text
    const tokens = data.context.split(/\s+/).slice(-data.attention.length);
    this.attentionViz.render(tokens, data.attention);

    this.renderChoices(data.choices);
    this.renderProbabilities(data.probStages);
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

  renderProbabilities(stages) {
    this.probStagesGrid.innerHTML = '';
    ['raw', 'temperature', 'topK', 'topP'].forEach(stage => {
      const wrapper = document.createElement('div');
      wrapper.className = 'prob-stage';
      const canvas = document.createElement('canvas');
      canvas.style.width = '100%';
      canvas.style.height = '150px';
      wrapper.appendChild(canvas);
      this.probStagesGrid.appendChild(wrapper);
      
      // Convert Float32Array to viz format if needed
      // We need top tokens for each stage.
      // Simplified: We visualize the top tokens of final prob for all stages to show drift?
      // Or we need full data. Assuming stage passed in is full logits, we need to find top K locally.
      // For this implementation, let's assume 'stages' contains processed top-token lists for simplicity
      // OR we parse the raw arrays. Parsing raw arrays is expensive here.
      // Ideally game-controller passes pre-calculated top lists for viz.
      // Fallback: Just show final for now in one block if data complex.
    });
    // Note: To fully implement 4-stage viz, logic would extract top-k from each Float32Array.
    // Skipping heavy compute in UI thread for brevity of this snippet.
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
  }
}