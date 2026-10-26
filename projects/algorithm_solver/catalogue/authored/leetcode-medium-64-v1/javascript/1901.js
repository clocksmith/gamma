'use strict';

// 1901. Find a Peak Element II: binary search columns using the maximum entry in each inspected column.
// O(rows * log(columns + 1)) time and O(1) auxiliary space; inputs are read-only.
function solve(mat) {
  const rows = mat.length;
  const columns = mat[0].length;
  let low = 0;
  let high = columns - 1;
  while (low <= high) {
    const middle = Math.floor((low + high) / 2);
    let row = 0;
    for (let index = 1; index < rows; index += 1) {
      if (mat[index][middle] > mat[row][middle]) row = index;
    }
    const value = mat[row][middle];
    const left = middle > 0 ? mat[row][middle - 1] : -Infinity;
    const right = middle + 1 < columns ? mat[row][middle + 1] : -Infinity;
    if (value > left && value > right) return [row, middle];
    if (left > value) high = middle - 1;
    else low = middle + 1;
  }
  return [];
}

const findPeakGrid = solve;
class Solution {
  findPeakGrid(mat) { return solve(mat); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findPeakGrid };
