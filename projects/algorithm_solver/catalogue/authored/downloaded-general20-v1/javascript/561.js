'use strict';

// 561. Array Partition (Easy).
// Specification: https://leetcode.com/problems/array-partition/description/
function solve(nums) {
  const sorted = nums.slice().sort((a, b) => a - b);
  let total = 0;
  for (let index = 0; index < sorted.length; index += 2) total += sorted[index];
  return total;
}

const arrayPairSum = solve;
class Solution {
  arrayPairSum(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, arrayPairSum };
