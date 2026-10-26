'use strict';

// 2871. Split Array Into Maximum Number of Subarrays: cut as soon as the current bitwise AND is zero and otherwise keep one piece.
// O(n) time and O(1) auxiliary space on the bounded integer domain; inputs are read-only.
function solve(nums) {
  let current = -1;
  let pieces = 0;
  for (const value of nums) {
    current &= value;
    if (current === 0) {
      pieces += 1;
      current = -1;
    }
  }
  return Math.max(1, pieces);
}

const maxSubarrays = solve;
class Solution {
  maxSubarrays(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxSubarrays };
