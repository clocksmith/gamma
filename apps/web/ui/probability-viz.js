export class ProbabilityViz {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
  }

  render(topTokens, stageName, maxTokens = 8) {
    const tokens = topTokens.slice(0, maxTokens);
    const width = this.canvas.width = this.canvas.offsetWidth;
    const height = this.canvas.height = this.canvas.offsetHeight;
    const barHeight = (height - 30) / tokens.length;
    const maxProb = Math.max(...tokens.map(t => t.prob), 0.001);

    this.ctx.clearRect(0, 0, width, height);
    
    this.ctx.fillStyle = '#a0a0a0';
    this.ctx.font = '11px Courier New';
    this.ctx.textAlign = 'left';
    this.ctx.fillText(stageName, 5, 12);

    tokens.forEach((token, i) => {
      const y = 20 + i * barHeight;
      const barWidth = (token.prob / maxProb) * (width - 100);

      this.ctx.fillStyle = 'rgba(0, 255, 255, 0.1)';
      this.ctx.fillRect(50, y, width - 60, barHeight - 2);

      const gradient = this.ctx.createLinearGradient(50, 0, 50 + barWidth, 0);
      gradient.addColorStop(0, 'rgba(0, 255, 255, 0.8)');
      gradient.addColorStop(1, 'rgba(255, 0, 255, 0.8)');
      this.ctx.fillStyle = gradient;
      this.ctx.fillRect(50, y, barWidth, barHeight - 2);

      this.ctx.fillStyle = '#e0e0e0';
      this.ctx.textAlign = 'right';
      this.ctx.fillText(token.text.slice(0, 8), 45, y + barHeight / 2 + 4);

      this.ctx.textAlign = 'left';
      this.ctx.fillText(`${(token.prob * 100).toFixed(1)}%`, 55 + barWidth, y + barHeight / 2 + 4);
    });
  }
}