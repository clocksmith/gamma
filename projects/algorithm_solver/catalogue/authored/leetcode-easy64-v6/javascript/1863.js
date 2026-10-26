'use strict';

// 1863. Sum of All Subset XOR Totals (Easy).
// Specification: https://leetcode.com/problems/sum-of-all-subset-xor-totals/description/
// O(n) time, O(1) space; OR is safe for the declared values 1..20; preserve nums.
function solve(nums) {
  let combined = 0;
  for (const value of nums) combined |= value;
  // Each bit present in the input is set in exactly half of all subset XORs.
  return combined * (2 ** (nums.length - 1));
}

const subsetXORSum = solve;
class Solution {
  subsetXORSum(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, subsetXORSum };
