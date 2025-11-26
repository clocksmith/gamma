import { AttentionViz } from './attention-viz.js';
import { ProbabilityViz } from './probability-viz.js';
import { EventBus } from '../utils/event-bus.js';

// Shared color utility - Viridis-like colorblind-friendly palette
export function getViridisColor(t) {
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

export class GamePanel {
  constructor(container) {
    this.container = container;
    this.setupDOM();
    this.bindEvents();
    this.bindKeyboardNavigation();
    this.attentionHistory = [];
    this.selectedChoiceIndex = -1;
    this.choicesEnabled = false;
    this.isRealAttention = false; // Track if attention is real or synthetic
  }

  setupDOM() {
    this.container.innerHTML = `
      <div class="gamma-game-panel">
        <!-- Header with game info -->
        <header class="game-header">
          <div class="header-left">
            <h1 class="game-title">GAMMA</h1>
            <span class="model-badge"></span>
          </div>
          <div class="header-center">
            <div class="round-pill">
              <span class="round-label">Round</span>
              <span class="round-num">1</span>
              <span class="round-separator">/</span>
              <span class="max-rounds">16</span>
            </div>
          </div>
          <div class="header-right">
            <div class="score-pill">
              <span class="score-label">Score</span>
              <span class="score">0</span>
            </div>
            <div class="streak-indicator hidden">
              <span class="streak-fire">🔥</span>
              <span class="streak-count">0</span>
            </div>
          </div>
        </header>

        <!-- Main game area -->
        <main class="game-main">
          <!-- Context section with attention visualization -->
          <section class="context-section">
            <div class="section-header">
              <h2>Context</h2>
              <div class="attention-badge" title="Attention source">
                <span class="attention-icon">👁</span>
                <span class="attention-label">Real Attention</span>
              </div>
            </div>
            <div class="context-display">
              <div class="context-text"></div>
            </div>
          </section>

          <!-- Choices section -->
          <section class="choices-section">
            <div class="section-header">
              <h2>What comes next?</h2>
              <span class="keyboard-hint">Press 1-4 or A-D to select</span>
            </div>
            <div class="choices-grid"></div>
          </section>

          <!-- Result feedback -->
          <div class="result-display hidden">
            <div class="result-icon"></div>
            <div class="result-text"></div>
            <div class="result-explanation"></div>
          </div>

          <!-- Probability distribution (shown after guess) -->
          <section class="probability-section hidden">
            <div class="section-header">
              <h2>Token Probabilities</h2>
              <span class="prob-hint">Top predictions from the model</span>
            </div>
            <div class="probability-chart"></div>
          </section>
        </main>

        <!-- Sidebar with attention heatmap history -->
        <aside class="game-sidebar">
          <div class="sidebar-header">
            <h3>Attention History</h3>
            <button class="sidebar-toggle" aria-label="Toggle sidebar">◀</button>
          </div>
          <div class="attention-heatmap-container">
            <div class="attention-heatmap"></div>
          </div>
          <div class="heatmap-legend">
            <span class="legend-low">Low</span>
            <div class="legend-gradient"></div>
            <span class="legend-high">High</span>
          </div>
        </aside>

        <!-- Action buttons -->
        <footer class="game-footer">
          <button class="btn btn-primary hidden continue-btn">Continue</button>
          <div class="footer-hint hidden">Press <kbd>Space</kbd> to continue</div>
        </footer>
      </div>
    `;

    // Cache DOM references
    this.contextText = this.container.querySelector('.context-text');
    this.choicesGrid = this.container.querySelector('.choices-grid');
    this.probabilitySection = this.container.querySelector('.probability-section');
    this.probabilityChart = this.container.querySelector('.probability-chart');
    this.attentionHeatmap = this.container.querySelector('.attention-heatmap');
    this.continueBtn = this.container.querySelector('.continue-btn');
    this.resultDisplay = this.container.querySelector('.result-display');
    this.attentionBadge = this.container.querySelector('.attention-badge');
    this.streakIndicator = this.container.querySelector('.streak-indicator');
    this.footerHint = this.container.querySelector('.footer-hint');
    this.sidebar = this.container.querySelector('.game-sidebar');

    // Sidebar toggle
    this.container.querySelector('.sidebar-toggle').addEventListener('click', () => {
      this.sidebar.classList.toggle('collapsed');
    });

    this.continueBtn.addEventListener('click', () => {
      EventBus.emit('game:continue');
    });
  }

  bindEvents() {
    EventBus.on('round:start', (data) => this.showRound(data));
    EventBus.on('round:result', (data) => this.showResult(data));
  }

  bindKeyboardNavigation() {
    document.addEventListener('keydown', (e) => {
      // Number keys 1-4 for direct selection
      if (e.key >= '1' && e.key <= '4') {
        const choiceIndex = parseInt(e.key) - 1;
        if (this.choicesEnabled && this._isValidChoice(choiceIndex)) {
          EventBus.emit('player:choice', choiceIndex);
        }
        return;
      }

      // Letter keys A-D for selection
      const letterKeys = { 'a': 0, 'b': 1, 'c': 2, 'd': 3 };
      if (letterKeys.hasOwnProperty(e.key.toLowerCase())) {
        const choiceIndex = letterKeys[e.key.toLowerCase()];
        if (this.choicesEnabled && this._isValidChoice(choiceIndex)) {
          EventBus.emit('player:choice', choiceIndex);
        }
        return;
      }

      // Arrow key navigation
      if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') {
        e.preventDefault();
        this._navigateChoice(-1);
      } else if (e.key === 'ArrowDown' || e.key === 'ArrowRight') {
        e.preventDefault();
        this._navigateChoice(1);
      }

      // Enter to confirm selection
      if (e.key === 'Enter' && this.choicesEnabled) {
        e.preventDefault();
        if (this._isValidChoice(this.selectedChoiceIndex)) {
          EventBus.emit('player:choice', this.selectedChoiceIndex);
        }
      }

      // Space to continue
      if (e.key === ' ' && !this.continueBtn.classList.contains('hidden')) {
        e.preventDefault();
        EventBus.emit('game:continue');
      }

      // Escape to deselect
      if (e.key === 'Escape') {
        this._clearSelection();
      }
    });
  }

  _isValidChoice(index) {
    const buttons = this.choicesGrid.querySelectorAll('.choice-btn');
    return index >= 0 && index < buttons.length && !buttons[index].disabled;
  }

  _navigateChoice(delta) {
    if (!this.choicesEnabled) return;
    const buttons = this.choicesGrid.querySelectorAll('.choice-btn');
    const numChoices = buttons.length;
    if (numChoices === 0) return;

    // If no selection yet, start at first (for down/right) or last (for up/left)
    if (this.selectedChoiceIndex === -1) {
      this.selectedChoiceIndex = delta > 0 ? 0 : numChoices - 1;
    } else {
      this.selectedChoiceIndex = (this.selectedChoiceIndex + delta + numChoices) % numChoices;
    }
    this._updateChoiceHighlight();
  }

  _updateChoiceHighlight() {
    const buttons = this.choicesGrid.querySelectorAll('.choice-btn');
    buttons.forEach((btn, i) => {
      btn.classList.toggle('keyboard-selected', i === this.selectedChoiceIndex);
    });
  }

  _clearSelection() {
    const buttons = this.choicesGrid.querySelectorAll('.choice-btn');
    buttons.forEach(btn => btn.classList.remove('keyboard-selected'));
    this.selectedChoiceIndex = -1;
  }

  setModelName(modelId) {
    const shortName = modelId.split('/').pop();
    this.container.querySelector('.model-badge').textContent = shortName;
  }

  showRound(data) {
    // Update round info
    this.container.querySelector('.round-num').textContent = data.roundNum;
    this.container.querySelector('.max-rounds').textContent = data.maxRounds;

    // Hide result and probability sections
    this.resultDisplay.classList.add('hidden');
    this.continueBtn.classList.add('hidden');
    this.footerHint.classList.add('hidden');
    this.probabilitySection.classList.add('hidden');

    // Process attention
    const tokens = data.context.split(/\s+/);
    let attentionWeights;

    // Check if we have real attention data
    if (data.attention && data.attention.length > 0) {
      attentionWeights = data.attention;
      this.isRealAttention = true;
      this._updateAttentionBadge(true);
    } else {
      // Generate synthetic attention (recency bias)
      const numTokens = Math.min(tokens.length, 20);
      attentionWeights = tokens.slice(-numTokens).map((_, i) => {
        return Math.pow((i + 1) / numTokens, 2);
      });
      this.isRealAttention = false;
      this._updateAttentionBadge(false);
    }

    // Render context with attention highlighting
    this.renderAttentionText(tokens, attentionWeights);

    // Store attention for heatmap history
    this.attentionHistory.push({
      weights: attentionWeights,
      tokens: tokens.slice(-attentionWeights.length),
      roundNum: data.roundNum,
      isReal: this.isRealAttention
    });
    this.renderAttentionHeatmap();

    // Render choices
    this.renderChoices(data.choices);

    // Store top tokens for later probability reveal
    this.pendingTopTokens = data.topTokens;
  }

  _updateAttentionBadge(isReal) {
    const label = this.attentionBadge.querySelector('.attention-label');
    if (isReal) {
      this.attentionBadge.classList.remove('synthetic');
      this.attentionBadge.classList.add('real');
      label.textContent = 'Real Attention';
      this.attentionBadge.title = 'Showing actual transformer attention weights';
    } else {
      this.attentionBadge.classList.remove('real');
      this.attentionBadge.classList.add('synthetic');
      label.textContent = 'Synthetic';
      this.attentionBadge.title = 'Model does not support attention output - showing estimated attention';
    }
  }

  renderAttentionText(tokens, weights) {
    const numWeights = weights.length;
    const displayTokens = tokens.slice(-numWeights);
    const maxWeight = Math.max(...weights, 0.0001);
    const normalized = weights.map(w => w / maxWeight);

    const tokensHtml = displayTokens.map((token, i) => {
      const intensity = normalized[i];
      const [r, g, b] = getViridisColor(intensity);
      const textColor = intensity > 0.6 ? '#000' : '#fff';
      const size = 0.85 + (intensity * 0.3); // Scale font size slightly with attention

      return `
        <span class="attn-token"
              style="background:rgb(${r},${g},${b}); color:${textColor}; font-size:${size}em"
              data-attention="${intensity.toFixed(3)}"
              title="Attention: ${(intensity * 100).toFixed(1)}%">
          ${this.escapeHtml(token)}
        </span>
      `;
    }).join('');

    this.contextText.innerHTML = tokensHtml;
  }

  renderAttentionHeatmap() {
    if (this.attentionHistory.length === 0) {
      this.attentionHeatmap.innerHTML = '<div class="heatmap-empty">Attention history will appear here</div>';
      return;
    }

    // Limit display to last 10 rounds for performance
    const displayHistory = this.attentionHistory.slice(-10);

    let html = '<div class="heatmap-grid">';

    displayHistory.forEach((round, rowIdx) => {
      const actualRound = this.attentionHistory.length - displayHistory.length + rowIdx + 1;
      const maxWeight = Math.max(...round.weights, 0.0001);

      html += `<div class="heatmap-row" data-round="${actualRound}">`;
      html += `<span class="heatmap-round-label">R${actualRound}</span>`;

      // Limit tokens per row for readability
      const displayWeights = round.weights.slice(-15);
      const displayTokens = round.tokens.slice(-15);

      displayWeights.forEach((weight, colIdx) => {
        const normalized = weight / maxWeight;
        const [r, g, b] = getViridisColor(normalized);
        const token = displayTokens[colIdx] || '?';
        html += `
          <div class="heatmap-cell"
               style="background:rgb(${r},${g},${b})"
               title="${this.escapeHtml(token)}: ${(normalized * 100).toFixed(0)}%">
          </div>
        `;
      });

      // Add indicator if synthetic
      if (!round.isReal) {
        html += '<span class="heatmap-synthetic-indicator" title="Synthetic attention">*</span>';
      }

      html += '</div>';
    });

    html += '</div>';

    // Show scroll hint if more history exists
    if (this.attentionHistory.length > 10) {
      html += `<div class="heatmap-scroll-hint">Showing last 10 of ${this.attentionHistory.length} rounds</div>`;
    }

    this.attentionHeatmap.innerHTML = html;
  }

  renderChoices(choices) {
    const labels = ['A', 'B', 'C', 'D'];

    this.choicesGrid.innerHTML = choices.map((choice, i) => {
      const probPercent = (choice.prob * 100).toFixed(1);
      return `
        <button class="choice-btn"
                data-index="${i}"
                data-prob="${probPercent}"
                aria-label="Choice ${labels[i]}: ${choice.text}"
                tabindex="0">
          <div class="choice-key">
            <span class="choice-number">${i + 1}</span>
            <span class="choice-letter">${labels[i]}</span>
          </div>
          <div class="choice-content">
            <span class="choice-text">${this.escapeHtml(choice.text)}</span>
          </div>
          <div class="choice-prob-bar hidden">
            <div class="prob-fill" style="width: ${Math.min(probPercent, 100)}%"></div>
            <span class="prob-value">${probPercent}%</span>
          </div>
        </button>
      `;
    }).join('');

    this.choicesEnabled = true;
    this.selectedChoiceIndex = -1; // No selection until user navigates

    this.choicesGrid.querySelectorAll('.choice-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        if (this.choicesEnabled) {
          EventBus.emit('player:choice', parseInt(btn.dataset.index));
        }
      });
    });
  }

  renderProbabilities(topTokens) {
    if (!topTokens || topTokens.length === 0) {
      this.probabilitySection.classList.add('hidden');
      return;
    }

    this.probabilitySection.classList.remove('hidden');

    // Create horizontal bar chart
    const maxProb = Math.max(...topTokens.slice(0, 10).map(t => t.prob), 0.01);

    const barsHtml = topTokens.slice(0, 10).map((token, i) => {
      const widthPercent = (token.prob / maxProb) * 100;
      const probPercent = (token.prob * 100).toFixed(1);
      const isChoice = this.pendingTopTokens?.some(t => t.text === token.text);

      return `
        <div class="prob-bar-row ${isChoice ? 'was-choice' : ''}" style="--rank: ${i}">
          <span class="prob-rank">#${i + 1}</span>
          <span class="prob-token">${this.escapeHtml(token.text)}</span>
          <div class="prob-bar">
            <div class="prob-bar-fill" style="width: ${widthPercent}%"></div>
          </div>
          <span class="prob-percent">${probPercent}%</span>
        </div>
      `;
    }).join('');

    this.probabilityChart.innerHTML = barsHtml;
  }

  showResult(data) {
    this.choicesEnabled = false;
    this._clearSelection();

    // Show result feedback
    this.resultDisplay.classList.remove('hidden');
    this.resultDisplay.className = `result-display ${data.isCorrect ? 'correct' : 'incorrect'}`;

    const resultIcon = this.resultDisplay.querySelector('.result-icon');
    const resultText = this.resultDisplay.querySelector('.result-text');
    const resultExplanation = this.resultDisplay.querySelector('.result-explanation');

    if (data.isCorrect) {
      resultIcon.textContent = '✓';
      resultText.textContent = 'Correct!';
      resultExplanation.textContent = `You predicted what the model would say!`;
    } else {
      resultIcon.textContent = '✗';
      resultText.textContent = 'Not quite';
      resultExplanation.innerHTML = `The model chose: <strong>${this.escapeHtml(data.correctToken.text)}</strong>`;
    }

    // Update score
    this.container.querySelector('.score').textContent = data.score;

    // Update streak indicator
    if (data.streak && data.streak >= 2) {
      this.streakIndicator.classList.remove('hidden');
      this.streakIndicator.querySelector('.streak-count').textContent = data.streak;
    } else {
      this.streakIndicator.classList.add('hidden');
    }

    // Highlight choices and reveal probabilities
    const buttons = this.choicesGrid.querySelectorAll('.choice-btn');
    buttons.forEach((btn, i) => {
      btn.disabled = true;

      if (i === data.correctChoice) {
        btn.classList.add('correct');
      } else if (i === data.playerChoice && !data.isCorrect) {
        btn.classList.add('incorrect');
      }

      // Show probability bar
      const probBar = btn.querySelector('.choice-prob-bar');
      probBar.classList.remove('hidden');
    });

    // Show full probability distribution
    this.renderProbabilities(this.pendingTopTokens);

    // Show continue button
    if (data.isLastRound) {
      const percentage = Math.round((data.finalScore / data.maxRounds) * 100);
      resultText.innerHTML = `Game Over! Final Score: ${data.finalScore}/${data.maxRounds} (${percentage}%)`;
      resultExplanation.textContent = this._getEndGameMessage(percentage);
      this.continueBtn.textContent = 'Play Again';
      this.continueBtn.classList.remove('hidden');
      this.continueBtn.onclick = () => window.location.reload();
    } else {
      this.continueBtn.textContent = 'Continue';
      this.continueBtn.classList.remove('hidden');
      this.footerHint.classList.remove('hidden');
    }
  }

  _getEndGameMessage(percentage) {
    if (percentage >= 80) return '🏆 Amazing! You really understand this model!';
    if (percentage >= 60) return '👍 Great job! You have solid LLM intuition.';
    if (percentage >= 40) return '📚 Good effort! Keep practicing to improve.';
    return '💡 LLMs can be unpredictable. Try again!';
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
}
