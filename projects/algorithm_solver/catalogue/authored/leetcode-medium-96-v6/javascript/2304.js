'use strict';

// 2304. Minimum Path Cost in a Grid: compute each row from the cheapest complete suffix paths in the next row.
// O(m * n^2) time and O(n) auxiliary space for m rows and n columns; inputs are read-only.
function solve(grid, moveCost) {
  const columns = grid[0].length;
  let best = grid[grid.length - 1].slice();
  for (let row = grid.length - 2; row >= 0; row -= 1) {
    const current = new Array(columns);
    for (let column = 0; column < columns; column += 1) {
      const value = grid[row][column];
      let suffix = Infinity;
      for (let following = 0; following < columns; following += 1) {
        suffix = Math.min(suffix, moveCost[value][following] + best[following]);
      }
      current[column] = value + suffix;
    }
    best = current;
  }
  let answer = Infinity;
  for (const value of best) answer = Math.min(answer, value);
  return answer;
}

const minPathCost = solve;
class Solution {
  minPathCost(grid, moveCost) { return solve(grid, moveCost); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minPathCost };
