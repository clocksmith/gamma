'use strict';

// 1727. Largest Submatrix With Rearrangements: sort a copy of each row histogram while preserving column height identity.
// O(rows * columns * log(columns + 1)) time and O(columns) auxiliary space; inputs are read-only.
function solve(matrix) {
  const heights = new Array(matrix[0].length).fill(0);
  let answer = 0;
  for (const row of matrix) {
    for (let column = 0; column < row.length; column += 1) {
      heights[column] = row[column] ? heights[column] + 1 : 0;
    }
    const ordered = [...heights].sort((left, right) => right - left);
    for (let index = 0; index < ordered.length; index += 1) {
      answer = Math.max(answer, (index + 1) * ordered[index]);
    }
  }
  return answer;
}

const largestSubmatrix = solve;
class Solution {
  largestSubmatrix(matrix) { return solve(matrix); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, largestSubmatrix };
