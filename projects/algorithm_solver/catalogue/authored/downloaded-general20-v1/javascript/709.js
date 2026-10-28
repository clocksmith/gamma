'use strict';

// 709. To Lower Case (Easy).
// Specification: https://leetcode.com/problems/to-lower-case/description/
function solve(s) {
  return s.toLowerCase();
}

const toLowerCase = solve;
class Solution {
  toLowerCase(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, toLowerCase };
