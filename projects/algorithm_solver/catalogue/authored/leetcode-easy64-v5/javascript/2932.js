'use strict';

// 2932. Maximum Strong Pair XOR I (Easy).
// Specification: https://leetcode.com/problems/maximum-strong-pair-xor-i/description/
// O(n^2) time, O(1) auxiliary space; values are at most 100; preserve nums.
function solve(nums) {
  let largest = 0;
  for (let left = 0; left < nums.length; left++) {
    for (let right = left + 1; right < nums.length; right++) {
      if (Math.abs(nums[left] - nums[right]) <= Math.min(nums[left], nums[right])) {
        largest = Math.max(largest, nums[left] ^ nums[right]);
      }
    }
  }
  return largest;
}

const maximumStrongPairXor = solve;
class Solution {
  maximumStrongPairXor(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumStrongPairXor };
