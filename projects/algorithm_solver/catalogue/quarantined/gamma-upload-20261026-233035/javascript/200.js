'use strict';
// 200. Number of Islands.
function solve(grid) {
  const rows = grid.length; const columns = grid[0].length; let count = 0;
  for (let row = 0; row < rows; row += 1) for (let column = 0; column < columns; column += 1) {
    if (grid[row][column] !== '1') continue;
    count += 1; grid[row][column] = '0';
    const stack = [[row, column]];
    while (stack.length) {
      const [currentRow, currentColumn] = stack.pop();
      for (const [dr, dc] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const nr = currentRow + dr; const nc = currentColumn + dc;
        if (nr >= 0 && nr < rows && nc >= 0 && nc < columns && grid[nr][nc] === '1') {
          grid[nr][nc] = '0'; stack.push([nr, nc]);
        }
      }
    }
  }
  return count;
}
const numIslands = solve;
class Solution { numIslands(grid) { return solve(grid); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, numIslands };
