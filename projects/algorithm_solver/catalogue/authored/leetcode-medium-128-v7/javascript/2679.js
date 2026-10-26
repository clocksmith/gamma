'use strict';

// 2679. Sum in a Matrix: sort copied rows and sum the maximum value at each removal rank.
// O(r * c log(c + 1)) time and O(r * c) auxiliary space; inputs are read-only.
function solve(nums) {
  const ordered = nums.map(row => row.slice().sort((left, right) => left - right));
  let score = 0;
  for (let column = 0; column < nums[0].length; column += 1) {
    let largest = 0;
    for (const row of ordered) largest = Math.max(largest, row[column]);
    score += largest;
  }
  return score;
}

const matrixSum = solve;
class Solution {
  matrixSum(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, matrixSum };
