'use strict';

// 2352. Equal Row and Column Pairs: count full row signatures and match each complete column against them.
// O(n^2) expected time and O(n^2) auxiliary space on the bounded integer domain; inputs are read-only.
function solve(grid) {
  const rows = new Map();
  for (const row of grid) {
    const signature = row.join(',');
    rows.set(signature, (rows.get(signature) || 0) + 1);
  }
  let answer = 0;
  for (let column = 0; column < grid.length; column += 1) {
    const values = [];
    for (let row = 0; row < grid.length; row += 1) values.push(grid[row][column]);
    answer += rows.get(values.join(',')) || 0;
  }
  return answer;
}

const equalPairs = solve;
class Solution {
  equalPairs(grid) { return solve(grid); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, equalPairs };
