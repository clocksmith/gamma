export class AttentionViz {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
  }

  // Viridis-like colorblind-friendly palette (purple -> teal -> yellow)
  getHeatmapColor(t) {
    // Interpolate through viridis colors
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
      const [r, g, b] = this.getHeatmapColor(intensity);

      this.ctx.fillStyle = `rgb(${r}, ${g}, ${b})`;
      this.ctx.fillRect(x, 0, tokenWidth - 2, height);

      // Text color: white for dark backgrounds, black for light
      this.ctx.fillStyle = intensity > 0.7 ? '#000000' : '#ffffff';
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