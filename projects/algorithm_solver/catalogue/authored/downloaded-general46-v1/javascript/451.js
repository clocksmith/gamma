'use strict';

// 451. Sort Characters By Frequency (Medium).
// Specification: https://leetcode.com/problems/sort-characters-by-frequency/description/
function solve(s) {
  const counts = {};
  for (const ch of s) counts[ch] = (counts[ch] || 0) + 1;
  const entries = Object.entries(counts).sort((a, b) => b[1] - a[1] || (a[0] < b[0] ? -1 : 1));
  let result = '';
  for (const [ch, count] of entries) result += ch.repeat(count);
  return result;
}
const frequencySort = solve;
class Solution { frequencySort(s) { return solve(s); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, frequencySort };
