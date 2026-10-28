'use strict';

// 647. Palindromic Substrings (Medium).
// Specification: https://leetcode.com/problems/palindromic-substrings/description/
function expand(s, left, right) {
  let count = 0;
  while (left >= 0 && right < s.length && s[left] === s[right]) { count++; left--; right++; }
  return count;
}
function solve(s) {
  let total = 0;
  for (let center = 0; center < s.length; center++) {
    total += expand(s, center, center);
    total += expand(s, center, center + 1);
  }
  return total;
}
const countSubstrings = solve;
class Solution { countSubstrings(s) { return solve(s); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, countSubstrings };
