'use strict';

// 3917. Count Indices With Opposite Parity (Easy).
// Specification: https://leetcode.com/problems/count-indices-with-opposite-parity/description/
// O(n) time, O(1) auxiliary space beyond the output; count only later indices; preserve nums.
function solve(nums) {
  const result = new Array(nums.length);
  const counts = [0, 0];
  for (let index = nums.length - 1; index >= 0; index--) {
    const parity = nums[index] % 2;
    result[index] = counts[1 - parity];
    counts[parity]++;
  }
  return result;
}

const countOppositeParity = solve;
class Solution {
  countOppositeParity(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countOppositeParity };
