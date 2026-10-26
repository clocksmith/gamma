'use strict';

// 1784. Check if Binary String Has at Most One Segment of Ones (Easy).
// Specification: https://leetcode.com/problems/check-if-binary-string-has-at-most-one-segment-of-ones/description/
// O(n) time, O(1) space; the problem guarantees s starts with 1.
function solve(s) {
  return !s.includes('01');
}

const checkOnesSegment = solve;
class Solution {
  checkOnesSegment(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, checkOnesSegment };
