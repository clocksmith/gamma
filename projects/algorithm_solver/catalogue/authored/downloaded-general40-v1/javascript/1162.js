'use strict';

// 1162. As Far from Land as Possible (Medium).
// Specification: https://leetcode.com/problems/as-far-from-land-as-possible/description/
function solve(grid) {
  const rows = grid.length; const cols = grid[0].length;
  const queue = [];
  const dist = grid.map((row) => row.map((value) => value === 1 ? 0 : -1));
  for (let r = 0; r < rows; r++) { for (let c = 0; c < cols; c++) { if (grid[r][c] === 1) queue.push([r, c]); else dist[r][c] = -1; } }
  if (queue.length === 0 || queue.length === rows * cols) return -1;
  let best = 0; let head = 0;
  const directions = [[1, 0], [-1, 0], [0, 1], [0, -1]];
  while (head < queue.length) {
    const [r, c] = queue[head++];
    for (const [dr, dc] of directions) {
      const nr = r + dr; const nc = c + dc;
      if (nr >= 0 && nr < rows && nc >= 0 && nc < cols && dist[nr][nc] === -1) { dist[nr][nc] = dist[r][c] + 1; best = Math.max(best, dist[nr][nc]); queue.push([nr, nc]); }
    }
  }
  return best;
}
const maxDistance = solve;
class Solution { maxDistance(grid) { return solve(grid); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxDistance };
