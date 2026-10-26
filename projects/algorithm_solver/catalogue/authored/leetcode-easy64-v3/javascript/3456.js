'use strict';

// 3456. Find Special Substring of Length K (Easy).
// Specification: https://leetcode.com/problems/find-special-substring-of-length-k/description/
// O(n) time, O(1) space; a maximal equal-character run must have length exactly k.
function solve(s, k) {
  let start = 0;
  while (start < s.length) {
    let end = start + 1;
    while (end < s.length && s[end] === s[start]) end++;
    if (end - start === k) return true;
    start = end;
  }
  return false;
}

const hasSpecialSubstring = solve;
class Solution {
  hasSpecialSubstring(s, k) { return solve(s, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, hasSpecialSubstring };
