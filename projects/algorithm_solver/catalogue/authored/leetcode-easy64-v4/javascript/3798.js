'use strict';

// 3798. Largest Even Number (Easy).
// Specification: https://leetcode.com/problems/largest-even-number/description/
// O(n) time and output space; the input alphabet contains only 1 and 2.
function solve(s) {
  let end = s.length;
  while (end > 0 && s[end - 1] !== '2') end--;
  return s.slice(0, end);
}

const largestEven = solve;
class Solution {
  largestEven(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, largestEven };
