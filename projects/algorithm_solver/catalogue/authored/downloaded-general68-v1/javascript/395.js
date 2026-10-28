'use strict';

// 395. Longest Substring with At Least K Repeating Characters (Medium).
// Specification: https://leetcode.com/problems/longest-substring-with-at-least-k-repeating-characters/description/
function countIn(s, k, start, end) {
  if (end - start < k) return 0;
  const counts = {};
  for (let i = start; i < end; i++) counts[s[i]] = (counts[s[i]] || 0) + 1;
  for (let i = start; i < end; i++) {
    if (counts[s[i]] < k) {
      const left = countIn(s, k, start, i);
      const right = countIn(s, k, i + 1, end);
      return Math.max(left, right);
    }
  }
  return end - start;
}
function solve(s, k) { return countIn(s, k, 0, s.length); }
const longestSubstring = solve;
class Solution { longestSubstring(s, k) { return solve(s, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestSubstring };
