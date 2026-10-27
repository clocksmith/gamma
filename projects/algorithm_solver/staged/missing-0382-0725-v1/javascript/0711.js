'use strict';

// 711. Number of Distinct Islands II. Normalize all eight rotations/reflections after translation; preserve the grid.

function solve(grid) {
  const rows = grid.length, cols = grid[0].length, seen = new Set(), shapes = new Set();
  function canonical(cells) {
    const variants = Array.from({length: 8}, () => []);
    for (const [x, y] of cells) {
      const points = [[x, y], [x, -y], [-x, y], [-x, -y], [y, x], [y, -x], [-y, x], [-y, -x]];
      points.forEach((point, i) => variants[i].push(point));
    }
    return variants.map(points => {
      points.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
      const [ox, oy] = points[0];
      return points.map(([x, y]) => `${x - ox},${y - oy}`).join(';');
    }).sort()[0];
  }
  for (let row = 0; row < rows; row += 1) for (let col = 0; col < cols; col += 1) {
    const key = row * cols + col;
    if (!grid[row][col] || seen.has(key)) continue;
    const stack = [[row, col]], cells = [];
    seen.add(key);
    while (stack.length > 0) {
      const [r, c] = stack.pop(); cells.push([r, c]);
      for (const [dr, dc] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const nr = r + dr, nc = c + dc, next = nr * cols + nc;
        if (nr >= 0 && nr < rows && nc >= 0 && nc < cols && grid[nr][nc] && !seen.has(next)) {
          seen.add(next); stack.push([nr, nc]);
        }
      }
    }
    shapes.add(canonical(cells));
  }
  return shapes.size;
}

const numDistinctIslands2 = solve;
class Solution {
  numDistinctIslands2(grid) { return solve(grid); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numDistinctIslands2 };
