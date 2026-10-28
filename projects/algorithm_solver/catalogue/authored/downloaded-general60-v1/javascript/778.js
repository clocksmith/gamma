'use strict';

// 778. Swim in Rising Water (Hard).
// Specification: https://leetcode.com/problems/swim-in-rising-water/description/
function solve(grid) {
  const n = grid.length;
  const dist = Array.from({ length: n }, () => new Array(n).fill(Infinity));
  dist[0][0] = grid[0][0];
  const visited = new Set();
  const directions = [[1, 0], [-1, 0], [0, 1], [0, -1]];
  for (let step = 0; step < n * n; step++) {
    let best = Infinity; let br = -1; let bc = -1;
    for (let r = 0; r < n; r++) {
      for (let c = 0; c < n; c++) {
        if (!visited.has(r * n + c) && dist[r][c] < best) { best = dist[r][c]; br = r; bc = c; }
      }
    }
    if (br === -1) break;
    visited.add(br * n + bc);
    if (br === n - 1 && bc === n - 1) break;
    for (const [dr, dc] of directions) {
      const nr = br + dr; const nc = bc + dc;
      if (nr >= 0 && nr < n && nc >= 0 && nc < n) dist[nr][nc] = Math.min(dist[nr][nc], Math.max(dist[br][bc], grid[nr][nc]));
    }
  }
  return dist[n - 1][n - 1];
}
const swimInWater = solve;
class Solution { swimInWater(grid) { return solve(grid); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, swimInWater };
