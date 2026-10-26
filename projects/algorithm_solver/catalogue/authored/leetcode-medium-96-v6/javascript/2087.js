'use strict';

// 2087. Minimum Cost Homecoming of a Robot in a Grid: pay once for each required row and column entered on a monotone path.
// O(abs(dr) + abs(dc)) time and O(1) auxiliary space; inputs are read-only.
function solve(startPos, homePos, rowCosts, colCosts) {
  let [row, column] = startPos;
  let answer = 0;
  const rowStep = homePos[0] > row ? 1 : -1;
  while (row !== homePos[0]) {
    row += rowStep;
    answer += rowCosts[row];
  }
  const columnStep = homePos[1] > column ? 1 : -1;
  while (column !== homePos[1]) {
    column += columnStep;
    answer += colCosts[column];
  }
  return answer;
}

const minCost = solve;
class Solution {
  minCost(startPos, homePos, rowCosts, colCosts) { return solve(startPos, homePos, rowCosts, colCosts); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minCost };
