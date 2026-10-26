'use strict';

// 3407. Substring Matching Pattern (Easy).
// Specification: https://leetcode.com/problems/substring-matching-pattern/description/
// O(|s| * |p|) worst-case time, O(|p|) space; the pattern contains one wildcard.
function solve(s, p) {
  const [prefix, suffix] = p.split('*');
  const start = s.indexOf(prefix);
  if (start === -1) return false;
  return s.indexOf(suffix, start + prefix.length) !== -1;
}

const hasMatch = solve;
class Solution {
  hasMatch(s, p) { return solve(s, p); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, hasMatch };
