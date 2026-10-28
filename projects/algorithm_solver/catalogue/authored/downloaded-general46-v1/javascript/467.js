'use strict';

// 467. Unique Substrings in Wraparound String (Medium).
// Specification: https://leetcode.com/problems/unique-substrings-in-wraparound-string/description/
function solve(s) {
  const best = {};
  let run = 0;
  for (let i = 0; i < s.length; i++) {
    if (i > 0 && (s.charCodeAt(i) - s.charCodeAt(i - 1) === 1 || (s[i - 1] === 'z' && s[i] === 'a'))) run++;
    else run = 1;
    best[s[i]] = Math.max(best[s[i]] || 0, run);
  }
  return Object.values(best).reduce((sum, value) => sum + value, 0);
}
const findSubstringInWraproundString = solve;
class Solution { findSubstringInWraproundString(s) { return solve(s); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, findSubstringInWraproundString };
