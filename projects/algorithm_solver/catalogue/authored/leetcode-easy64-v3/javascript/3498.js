'use strict';

// 3498. Reverse Degree of a String (Easy).
// Specification: https://leetcode.com/problems/reverse-degree-of-a-string/description/
// O(n) time, O(1) space; multiply reverse-alphabet values by one-based positions.
function solve(s) {
  let total = 0;
  for (let index = 0; index < s.length; index++) {
    total += (123 - s.charCodeAt(index)) * (index + 1);
  }
  return total;
}

const reverseDegree = solve;
class Solution {
  reverseDegree(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, reverseDegree };
