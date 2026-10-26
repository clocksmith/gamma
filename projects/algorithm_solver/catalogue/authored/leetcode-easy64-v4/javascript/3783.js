'use strict';

// 3783. Mirror Distance of an Integer (Easy).
// Specification: https://leetcode.com/problems/mirror-distance-of-an-integer/description/
// O(d) time, O(1) space; d is the decimal digit count; use exact integer arithmetic.
function solve(n) {
  let remaining = n;
  let reversed = 0;
  while (remaining > 0) {
    reversed = reversed * 10 + remaining % 10;
    remaining = Math.floor(remaining / 10);
  }
  return Math.abs(n - reversed);
}

const mirrorDistance = solve;
class Solution {
  mirrorDistance(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, mirrorDistance };
