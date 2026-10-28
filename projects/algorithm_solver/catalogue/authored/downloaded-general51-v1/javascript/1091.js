'use strict';

// 1091. Shortest Path in Binary Matrix (Medium).
// Specification: https://leetcode.com/problems/shortest-path-in-binary-matrix/description/
function solve(grid) {
  const n = grid.length;
  if (grid[0][0] !== 0 || grid[n - 1][n - 1] !== 0) return -1;
  const queue = [[0, 0, 1]];
  const visited = new Set(['0,0']);
  const directions = [[-1, -1], [-1, 0], [-1, 1], [0, -1], [0, 1], [1, -1], [1, 0], [1, 1]];
  while (queue.length > 0) {
    const [r, c, distance] = queue.shift();
    if (r === n - 1 && c === n - 1) return distance;
    for (const [dr, dc] of directions) {
      const nr = r + dr; const nc = c + dc;
      if (nr >= 0 && nr < n && nc >= 0 && nc < n && grid[nr][nc] === 0 && !visited.has(nr + ',' + nc)) { visited.add(nr + ',' + nc); queue.push([nr, nc, distance + 1]); }
    }
  }
  return -1;
}
const shortestPathBinaryMatrix = solve;
class Solution { shortestPathBinaryMatrix(grid) { return solve(grid); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, shortestPathBinaryMatrix };
