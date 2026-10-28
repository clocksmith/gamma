'use strict';

// 1763. Longest Nice Substring (Easy).
// Specification: https://leetcode.com/problems/longest-nice-substring/description/
function isNice(text) {
  const seen = new Set(text);
  for (const ch of text) {
    if (!seen.has(ch.toLowerCase()) || !seen.has(ch.toUpperCase())) return false;
  }
  return true;
}
function solve(s) {
  for (let length = s.length; length > 0; length--) {
    for (let start = 0; start + length <= s.length; start++) {
      const part = s.slice(start, start + length);
      if (isNice(part)) return part;
    }
  }
  return '';
}
const longestNiceSubstring = solve;
class Solution { longestNiceSubstring(s) { return solve(s); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestNiceSubstring };
