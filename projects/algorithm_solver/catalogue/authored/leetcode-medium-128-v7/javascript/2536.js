'use strict';

// 2536. Increment Submatrices by One: record rectangle corners in a two-dimensional difference array.
// O(n * n + q) time and O(n * n) auxiliary space; inputs are read-only.
function solve(n, queries) {
  const changes = Array.from({ length: n + 1 }, () => new Int32Array(n + 1));
  for (const [top, left, bottom, right] of queries) {
    changes[top][left] += 1;
    changes[top][right + 1] -= 1;
    changes[bottom + 1][left] -= 1;
    changes[bottom + 1][right + 1] += 1;
  }
  const result = Array.from({ length: n }, () => new Array(n).fill(0));
  for (let row = 0; row < n; row += 1) {
    let running = 0;
    for (let column = 0; column < n; column += 1) {
      running += changes[row][column];
      result[row][column] = running + (row ? result[row - 1][column] : 0);
    }
  }
  return result;
}

const rangeAddQueries = solve;
class Solution {
  rangeAddQueries(n, queries) { return solve(n, queries); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, rangeAddQueries };
