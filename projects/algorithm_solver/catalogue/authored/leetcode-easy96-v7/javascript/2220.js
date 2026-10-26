'use strict';

// 2220. Minimum Bit Flips to Convert Number (Easy).
// Specification: https://leetcode.com/problems/minimum-bit-flips-to-convert-number/description/
// O(32) time, O(1) space; XOR identifies the bits that must change in the stated domain.
function solve(start, goal) {
  let difference = (start ^ goal) >>> 0;
  let flips = 0;
  while (difference !== 0) {
    difference = (difference & (difference - 1)) >>> 0;
    flips++;
  }
  return flips;
}

const minBitFlips = solve;
class Solution {
  minBitFlips(start, goal) { return solve(start, goal); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minBitFlips };
