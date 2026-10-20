function minCostII(costs) {
  if (!costs.length) return 0;
  const colors = costs[0].length;
  if (colors === 1) return costs.length === 1 ? costs[0][0] : -1;
  let previous = Array(colors).fill(0);
  for (const row of costs) {
    let smallest = Infinity, second = Infinity, smallestIndex = -1;
    for (let color = 0; color < colors; color++) {
      if (previous[color] < smallest) { second = smallest; smallest = previous[color]; smallestIndex = color; }
      else if (previous[color] < second) second = previous[color];
    }
    previous = row.map((cost, color) => cost + (color === smallestIndex ? second : smallest));
  }
  return Math.min(...previous);
}
