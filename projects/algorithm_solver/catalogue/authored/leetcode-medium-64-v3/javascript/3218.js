'use strict';

// 3218. Minimum Cost for Cutting Cake I: take the most expensive remaining cut before it spans more pieces.
// O(m log m + n log n) time and O(m + n) auxiliary space; inputs are read-only.
function solve(m, n, horizontalCut, verticalCut) {
  const horizontal = [...horizontalCut].sort((left, right) => right - left);
  const vertical = [...verticalCut].sort((left, right) => right - left);
  let rowPieces = 1;
  let columnPieces = 1;
  let row = 0;
  let column = 0;
  let total = 0;
  while (row < horizontal.length || column < vertical.length) {
    if (column === vertical.length || (row < horizontal.length && horizontal[row] >= vertical[column])) {
      total += horizontal[row] * columnPieces;
      rowPieces += 1;
      row += 1;
    } else {
      total += vertical[column] * rowPieces;
      columnPieces += 1;
      column += 1;
    }
  }
  return total;
}

const minimumCost = solve;
class Solution {
  minimumCost(m, n, horizontalCut, verticalCut) { return solve(m, n, horizontalCut, verticalCut); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumCost };
