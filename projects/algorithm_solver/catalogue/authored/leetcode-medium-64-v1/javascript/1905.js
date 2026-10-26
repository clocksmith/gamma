'use strict';

// 1905. Count Sub Islands: visit every second-grid island completely while checking first-grid coverage.
// O(rows * columns) time and O(rows * columns) auxiliary space; inputs are read-only.
function solve(grid1, grid2) {
  const rows = grid2.length;
  const columns = grid2[0].length;
  const seen = Array.from({ length: rows }, () => new Uint8Array(columns));
  const directions = [[1, 0], [-1, 0], [0, 1], [0, -1]];
  let answer = 0;
  for (let row = 0; row < rows; row += 1) {
    for (let column = 0; column < columns; column += 1) {
      if (!grid2[row][column] || seen[row][column]) continue;
      const stack = [[row, column]];
      seen[row][column] = 1;
      let covered = true;
      while (stack.length) {
        const [currentRow, currentColumn] = stack.pop();
        if (!grid1[currentRow][currentColumn]) covered = false;
        for (const [dr, dc] of directions) {
          const nr = currentRow + dr;
          const nc = currentColumn + dc;
          if (nr >= 0 && nr < rows && nc >= 0 && nc < columns && grid2[nr][nc] && !seen[nr][nc]) {
            seen[nr][nc] = 1;
            stack.push([nr, nc]);
          }
        }
      }
      if (covered) answer += 1;
    }
  }
  return answer;
}

const countSubIslands = solve;
class Solution {
  countSubIslands(grid1, grid2) { return solve(grid1, grid2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countSubIslands };
