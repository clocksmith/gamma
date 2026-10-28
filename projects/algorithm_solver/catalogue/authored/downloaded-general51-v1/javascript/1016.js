'use strict';

// 1016. Binary String With Substrings Representing 1 To N (Medium).
// Specification: https://leetcode.com/problems/binary-string-with-substrings-representing-1-to-n/description/
function solve(s, n) {
  for (let value = 1; value <= n; value++) {
    if (!s.includes(value.toString(2))) return false;
  }
  return true;
}
const queryString = solve;
class Solution { queryString(s, n) { return solve(s, n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, queryString };
