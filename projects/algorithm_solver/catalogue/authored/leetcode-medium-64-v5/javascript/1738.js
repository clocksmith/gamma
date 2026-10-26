'use strict';

// 1738. Find Kth Largest XOR Coordinate Value: accumulate column-prefix XOR values and sort the coordinate results.
// O(rows * columns * log(rows * columns + 1)) time and O(rows * columns) auxiliary space; inputs are read-only.
function solve(matrix, k) {
  const above = new Uint32Array(matrix[0].length);
  const values = new Uint32Array(matrix.length * matrix[0].length);
  let count = 0;
  for (const row of matrix) {
    let rowXor = 0;
    for (let column = 0; column < row.length; column += 1) {
      rowXor ^= row[column];
      above[column] ^= rowXor;
      values[count] = above[column];
      count += 1;
    }
  }
  values.sort();
  return values[values.length - k];
}

const kthLargestValue = solve;
class Solution {
  kthLargestValue(matrix, k) { return solve(matrix, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, kthLargestValue };
