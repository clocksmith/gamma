'use strict';

// 1758. Minimum Changes To Make Alternating Binary String (Easy).
// Specification: https://leetcode.com/problems/minimum-changes-to-make-alternating-binary-string/description/
// O(n) time, O(1) space; compare the two complementary alternating patterns.
function solve(s) {
  let mismatches = 0;
  for (let index = 0; index < s.length; index++) {
    const expected = index % 2 === 0 ? '0' : '1';
    if (s[index] !== expected) mismatches++;
  }
  return Math.min(mismatches, s.length - mismatches);
}

const minOperations = solve;
class Solution {
  minOperations(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minOperations };
