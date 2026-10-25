class Solution {
  gardenNoAdj(n, paths) {
    const neighbors = Array.from({length: n}, () => []);
    for (const [first, second] of paths) {
      neighbors[first - 1].push(second - 1);
      neighbors[second - 1].push(first - 1);
    }
    const colors = Array(n).fill(0);
    for (let garden = 0; garden < n; garden += 1) {
      const used = Array(5).fill(false);
      for (const neighbor of neighbors[garden]) {
        used[colors[neighbor]] = true;
      }
      for (let color = 1; color <= 4; color += 1) {
        if (!used[color]) {
          colors[garden] = color;
          break;
        }
      }
    }
    return colors;
  }
}
