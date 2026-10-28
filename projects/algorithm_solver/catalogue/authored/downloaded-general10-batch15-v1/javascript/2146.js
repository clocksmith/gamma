'use strict';

// 2146. K Highest Ranked Items Within a Price Range (Medium).
// Specification: https://leetcode.com/problems/k-highest-ranked-items-within-a-price-range/description/
function solve(grid, pricing, start, k) {
  const rows = grid.length; const cols = grid[0].length;
  const low = pricing[0]; const high = pricing[1];
  const visited = Array.from({ length: rows }, () => new Array(cols).fill(false));
  const queue = [[start[0], start[1], 0]];
  visited[start[0]][start[1]] = true;
  const items = [];
  const dirs = [[-1, 0], [1, 0], [0, -1], [0, 1]];
  for (let head = 0; head < queue.length; head++) {
    const [r, c, dist] = queue[head];
    const price = grid[r][c];
    if (price >= low && price <= high) items.push([dist, price, r, c]);
    for (const [dr, dc] of dirs) {
      const nr = r + dr; const nc = c + dc;
      if (nr < 0 || nr >= rows || nc < 0 || nc >= cols) continue;
      if (visited[nr][nc] || grid[nr][nc] === 0) continue;
      visited[nr][nc] = true;
      queue.push([nr, nc, dist + 1]);
    }
  }
  items.sort((a, b) => a[0] - b[0] || a[1] - b[1] || a[2] - b[2] || a[3] - b[3]);
  return items.slice(0, k).map((item) => [item[2], item[3]]);
}
const highestRankedKItems = solve;
class Solution { highestRankedKItems(grid, pricing, start, k) { return solve(grid, pricing, start, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, highestRankedKItems };
