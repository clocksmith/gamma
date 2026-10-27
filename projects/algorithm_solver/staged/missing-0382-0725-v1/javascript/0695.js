'use strict';

// 695. Max Area of Island. Iterative flood fill with separate visitation state; input preserved.

function solve(grid) {
  const rows = grid.length, cols = grid[0].length, seen = new Set();
  let answer = 0;
  for (let row = 0; row < rows; row += 1) for (let col = 0; col < cols; col += 1) {
    const key = row * cols + col;
    if (!grid[row][col] || seen.has(key)) continue;
    const stack = [[row, col]];
    seen.add(key);
    let area = 0;
    while (stack.length > 0) {
      const [r, c] = stack.pop(); area += 1;
      for (const [dr, dc] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const nr = r + dr, nc = c + dc, next = nr * cols + nc;
        if (nr >= 0 && nr < rows && nc >= 0 && nc < cols && grid[nr][nc] && !seen.has(next)) {
          seen.add(next); stack.push([nr, nc]);
        }
      }
    }
    answer = Math.max(answer, area);
  }
  return answer;
}

const maxAreaOfIsland = solve;
class Solution {
  maxAreaOfIsland(grid) { return solve(grid); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxAreaOfIsland };
