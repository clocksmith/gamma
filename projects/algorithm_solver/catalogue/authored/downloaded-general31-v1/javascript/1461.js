'use strict';

// 1461. Check If a String Contains All Binary Codes of Size K (Medium).
// Specification: https://leetcode.com/problems/check-if-a-string-contains-all-binary-codes-of-size-k/description/
function solve(s, k) {
  const seen = new Set();
  for (let i = 0; i + k <= s.length; i++) seen.add(s.slice(i, i + k));
  return seen.size === (1 << k);
}
const hasAllCodes = solve;
class Solution { hasAllCodes(s, k) { return solve(s, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, hasAllCodes };
