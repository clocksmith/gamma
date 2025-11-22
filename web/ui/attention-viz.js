export class AttentionViz {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
  }

  render(tokens, attentionWeights) {
    if (!attentionWeights || tokens.length === 0) return;

    const width = this.canvas.width = this.canvas.offsetWidth;
    const height = this.canvas.height = this.canvas.offsetHeight;
    
    const maxWeight = Math.max(...attentionWeights, 0.0001);
    const normalized = attentionWeights.map(w => w / maxWeight);

    this.ctx.clearRect(0, 0, width, height);
    const tokenWidth = Math.min(60, width / tokens.length);

    tokens.forEach((token, i) => {
      const x = i * tokenWidth;
      const intensity = normalized[i];
      const r = Math.floor(255 * intensity);
      const b = Math.floor(255 * intensity);
      
      this.ctx.fillStyle = `rgba(${r}, 0, ${b}, ${0.2 + intensity * 0.6})`;
      this.ctx.fillRect(x, 0, tokenWidth - 2, height);

      this.ctx.fillStyle = intensity > 0.5 ? '#ffffff' : '#a0a0a0';
      this.ctx.font = '10px Courier New';
      this.ctx.textAlign = 'center';
      
      this.ctx.save();
      this.ctx.translate(x + tokenWidth / 2, height - 5);
      this.ctx.rotate(-Math.PI / 4);
      this.ctx.fillText(token.length > 8 ? token.slice(0, 7) + '…' : token, 0, 0);
      this.ctx.restore();
    });
  }
}