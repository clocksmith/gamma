'use strict';

// 3702. Longest Subsequence With Non-Zero Bitwise XOR.
// O(n) time and O(1) auxiliary space; values fit the stated nonnegative 30-bit domain.
function solve(nums) {
  let combined = 0;
  let nonzero = false;
  for (const value of nums) {
    combined ^= value;
    nonzero = nonzero || value !== 0;
  }
  if (combined !== 0) return nums.length;
  return nonzero ? nums.length - 1 : 0;
}

const longestSubsequence = solve;
class Solution {
  longestSubsequence(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestSubsequence };
