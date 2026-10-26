'use strict';

// 3736. Minimum Moves to Equal Array Elements III (Easy).
// Specification: https://leetcode.com/problems/minimum-moves-to-equal-array-elements-iii/description/
// O(n) time, O(1) space; increasing every value to the existing maximum is optimal.
function solve(nums) {
  let largest = nums[0];
  let total = 0;
  for (const value of nums) {
    largest = Math.max(largest, value);
    total += value;
  }
  return largest * nums.length - total;
}

const minMoves = solve;
class Solution {
  minMoves(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minMoves };
