'use strict';

// 861. Score After Flipping Matrix: account for row flips and select each column majority without modifying the grid.
// O(rows * columns) time and O(1) auxiliary space; inputs are read-only.
function solve(grid) {
  const rows = grid.length;
  let answer = 0;
  for (let column = 0; column < grid[0].length; column += 1) {
    let ones = 0;
    for (const row of grid) if (row[column] === row[0]) ones += 1;
    answer = answer * 2 + Math.max(ones, rows - ones);
  }
  return answer;
}

const matrixScore = solve;
class Solution {
  matrixScore(grid) { return solve(grid); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, matrixScore };
