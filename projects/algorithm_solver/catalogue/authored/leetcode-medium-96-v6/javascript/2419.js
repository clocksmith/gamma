'use strict';

// 2419. Longest Subarray With Maximum Bitwise AND: find the longest run of the global maximum value.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(nums) {
  let maximum = 0;
  for (const value of nums) maximum = Math.max(maximum, value);
  let current = 0;
  let best = 0;
  for (const value of nums) {
    current = value === maximum ? current + 1 : 0;
    best = Math.max(best, current);
  }
  return best;
}

const longestSubarray = solve;
class Solution {
  longestSubarray(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestSubarray };
