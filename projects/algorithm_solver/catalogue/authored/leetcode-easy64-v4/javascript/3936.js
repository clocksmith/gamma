'use strict';

// 3936. Minimum Swaps to Move Zeros to End (Easy).
// Specification: https://leetcode.com/problems/minimum-swaps-to-move-zeros-to-end/description/
// O(n) time, O(1) space; arbitrary index swaps are allowed; preserve nums.
function solve(nums) {
  let nonzeroCount = 0;
  for (const value of nums) {
    if (value !== 0) nonzeroCount++;
  }
  let swaps = 0;
  for (let index = 0; index < nonzeroCount; index++) {
    if (nums[index] === 0) swaps++;
  }
  return swaps;
}

const minimumSwaps = solve;
class Solution {
  minimumSwaps(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumSwaps };
