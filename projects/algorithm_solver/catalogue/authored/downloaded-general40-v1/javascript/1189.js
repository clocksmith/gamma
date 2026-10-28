'use strict';

// 1189. Maximum Number of Balloons (Easy).
// Specification: https://leetcode.com/problems/maximum-number-of-balloons/description/
function solve(text) {
  const counts = {};
  for (const ch of text) counts[ch] = (counts[ch] || 0) + 1;
  return Math.min(counts['b'] || 0, counts['a'] || 0, Math.floor((counts['l'] || 0) / 2), Math.floor((counts['o'] || 0) / 2), counts['n'] || 0);
}
const maxNumberOfBalloons = solve;
class Solution { maxNumberOfBalloons(text) { return solve(text); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxNumberOfBalloons };
