'use strict';

// 1293. Shortest Path in a Grid with Obstacles Elimination: BFS with remaining-budget dominance; O(rows*columns*(k+1)) worst-case time and space.

function solve(grid, k) {
  const rows = grid.length;
  const columns = grid[0].length;
  if (k >= rows + columns - 2) return rows + columns - 2;
  const budget = Array.from({ length: rows }, () => Array(columns).fill(-1));
  budget[0][0] = k;
  const queue = [[0, 0, k, 0]];
  for (let head = 0; head < queue.length; head += 1) {
    const [row, column, remaining, distance] = queue[head];
    if (row === rows - 1 && column === columns - 1) return distance;
    for (const [dr, dc] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
      const nr = row + dr;
      const nc = column + dc;
      if (nr < 0 || nr >= rows || nc < 0 || nc >= columns) continue;
      const following = remaining - grid[nr][nc];
      if (following >= 0 && following > budget[nr][nc]) {
        budget[nr][nc] = following;
        queue.push([nr, nc, following, distance + 1]);
      }
    }
  }
  return -1;
}

const shortestPath = solve;
class Solution {
  shortestPath(grid, k) { return solve(grid, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, shortestPath };
