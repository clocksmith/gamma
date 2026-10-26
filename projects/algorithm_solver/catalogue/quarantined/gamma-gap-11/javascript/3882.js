'use strict';

// 3882. Minimum XOR Path in a Grid.
// O(rows*columns*2^10) time and O(columns*2^10) space; retain all reachable XOR states, not just local minima.
function solve(grid) {
  const rows = grid.length;
  const columns = grid[0].length;
  const paths = Array.from({ length: columns }, () => new Set());
  for (let row = 0; row < rows; row += 1) {
    for (let column = 0; column < columns; column += 1) {
      const value = grid[row][column];
      if (row === 0 && column === 0) {
        paths[column] = new Set([value]);
        continue;
      }
      const reachable = new Set();
      for (const state of paths[column]) reachable.add(state ^ value);
      if (column > 0) for (const state of paths[column - 1]) reachable.add(state ^ value);
      paths[column] = reachable;
    }
  }
  let answer = Infinity;
  for (const value of paths[columns - 1]) answer = Math.min(answer, value);
  return answer;
}

const minXor = solve;
class Solution {
  minXor(grid) { return solve(grid); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minXor };
