'use strict';

// 3742. Maximum Path Score in a Grid.
// O(rows * columns * min(k + 1, rows + columns)) time and O(columns * min(k + 1, rows + columns)) space.
function solve(grid, k) {
  const rows = grid.length;
  const columns = grid[0].length;
  const limit = Math.min(k, rows + columns - 1);
  const previous = Array.from({ length: columns }, () => new Int32Array(limit + 1).fill(-1));
  for (let row = 0; row < rows; row += 1) {
    for (let column = 0; column < columns; column += 1) {
      const value = grid[row][column];
      const cost = value === 0 ? 0 : 1;
      const current = new Int32Array(limit + 1).fill(-1);
      if (row === 0 && column === 0) {
        current[0] = 0;
      } else {
        for (let spent = cost; spent <= limit; spent += 1) {
          let best = row > 0 ? previous[column][spent - cost] : -1;
          if (column > 0) best = Math.max(best, previous[column - 1][spent - cost]);
          if (best >= 0) current[spent] = best + value;
        }
      }
      previous[column] = current;
    }
  }
  let answer = -1;
  for (const score of previous[columns - 1]) answer = Math.max(answer, score);
  return answer;
}

const maxPathScore = solve;
class Solution {
  maxPathScore(grid, k) { return solve(grid, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxPathScore };
