'use strict';

// 1730. Shortest Path to Get Food (Medium).
// Specification: https://leetcode.com/problems/shortest-path-to-get-food/description/
function solve(grid) {
  const rows = grid.length; const cols = grid[0].length;
  let startRow = -1; let startCol = -1;
  for (let r = 0; r < rows; r++) { for (let c = 0; c < cols; c++) { if (grid[r][c] === '*') { startRow = r; startCol = c; } } }
  const queue = [[startRow, startCol, 0]];
  const visited = new Set([`${startRow},${startCol}`]);
  const directions = [[1, 0], [-1, 0], [0, 1], [0, -1]];
  while (queue.length > 0) {
    const [r, c, steps] = queue.shift();
    for (const [dr, dc] of directions) {
      const nr = r + dr; const nc = c + dc;
      if (nr < 0 || nr >= rows || nc < 0 || nc >= cols || visited.has(`${nr},${nc}`) || grid[nr][nc] === 'X') continue;
      if (grid[nr][nc] === '#') return steps + 1;
      visited.add(`${nr},${nc}`);
      queue.push([nr, nc, steps + 1]);
    }
  }
  return -1;
}
const getFood = solve;
class Solution { getFood(grid) { return solve(grid); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, getFood };
