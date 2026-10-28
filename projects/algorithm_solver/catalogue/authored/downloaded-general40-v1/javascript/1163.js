'use strict';

// 1163. Last Substring in Lexicographical Order (Hard).
// Specification: https://leetcode.com/problems/last-substring-in-lexicographical-order/description/
// Straightforward suffix comparison: correct, O(n squared) worst case, not
// the optimal two-pointer algorithm.
function solve(s) {
  let best = 0;
  for (let i = 1; i < s.length; i++) {
    if (s.slice(i) > s.slice(best)) best = i;
  }
  return s.slice(best);
}
const lastSubstring = solve;
class Solution { lastSubstring(s) { return solve(s); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, lastSubstring };
