'use strict';

// 424. Longest Repeating Character Replacement (Medium).
// Specification: https://leetcode.com/problems/longest-repeating-character-replacement/description/
function solve(s, k) {
  const counts = {};
  let left = 0; let maxCount = 0; let best = 0;
  for (let right = 0; right < s.length; right++) {
    counts[s[right]] = (counts[s[right]] || 0) + 1;
    maxCount = Math.max(maxCount, counts[s[right]]);
    while (right - left + 1 - maxCount > k) { counts[s[left]]--; left++; }
    best = Math.max(best, right - left + 1);
  }
  return best;
}
const characterReplacement = solve;
class Solution { characterReplacement(s, k) { return solve(s, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, characterReplacement };
