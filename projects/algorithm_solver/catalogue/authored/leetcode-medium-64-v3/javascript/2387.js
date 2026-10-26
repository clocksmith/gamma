'use strict';

// 2387. Median of a Row Wise Sorted Matrix: binary search values using upper bounds in each sorted row.
// O(r log(c + 1) log(V + 1)) time and O(1) auxiliary space for value range V; inputs are read-only.
function solve(grid) {
  let low = Infinity;
  let high = -Infinity;
  for (const row of grid) {
    low = Math.min(low, row[0]);
    high = Math.max(high, row[row.length - 1]);
  }
  const middleRank = Math.floor(grid.length * grid[0].length / 2);
  while (low < high) {
    const middle = Math.floor((low + high) / 2);
    let count = 0;
    for (const row of grid) {
      let left = 0;
      let right = row.length;
      while (left < right) {
        const index = Math.floor((left + right) / 2);
        if (row[index] <= middle) left = index + 1;
        else right = index;
      }
      count += left;
    }
    if (count <= middleRank) low = middle + 1;
    else high = middle;
  }
  return low;
}

const matrixMedian = solve;
class Solution {
  matrixMedian(grid) { return solve(grid); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, matrixMedian };
