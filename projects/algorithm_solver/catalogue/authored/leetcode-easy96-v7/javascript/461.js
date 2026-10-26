'use strict';

// 461. Hamming Distance (Easy).
// Specification: https://leetcode.com/problems/hamming-distance/description/
// O(32) time, O(1) space; count differing bits of the declared nonnegative 31-bit inputs.
function solve(x, y) {
  let difference = (x ^ y) >>> 0;
  let count = 0;
  while (difference !== 0) {
    difference = (difference & (difference - 1)) >>> 0;
    count++;
  }
  return count;
}

const hammingDistance = solve;
class Solution {
  hammingDistance(x, y) { return solve(x, y); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, hammingDistance };
