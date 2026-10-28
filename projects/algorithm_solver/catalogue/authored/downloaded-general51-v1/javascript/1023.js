'use strict';

// 1023. Camelcase Matching (Medium).
// Specification: https://leetcode.com/problems/camelcase-matching/description/
function matches(query, pattern) {
  let index = 0;
  for (const ch of query) {
    if (index < pattern.length && ch === pattern[index]) index++;
    else if (ch >= 'A' && ch <= 'Z') return false;
  }
  return index === pattern.length;
}
function solve(queries, pattern) {
  return queries.map((query) => matches(query, pattern));
}
const camelMatch = solve;
class Solution { camelMatch(queries, pattern) { return solve(queries, pattern); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, camelMatch };
