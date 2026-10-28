'use strict';

// 344. Reverse String (Easy).
// Specification: https://leetcode.com/problems/reverse-string/description/
function solve(s) {
  return s.slice().reverse();
}
const reverseString = solve;
class Solution { reverseString(s) { return solve(s); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, reverseString };
