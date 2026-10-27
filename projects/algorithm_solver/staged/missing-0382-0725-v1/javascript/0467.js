'use strict';

// 467. Unique Substrings in Wraparound String.

function solve(s) {
  const best = Array(26).fill(0);
  let run = 0;
  for (let i = 0; i < s.length; i += 1) {
    const index = s.charCodeAt(i) - 97;
    if (i > 0 && (s.charCodeAt(i) - s.charCodeAt(i - 1) + 26) % 26 === 1) run += 1;
    else run = 1;
    best[index] = Math.max(best[index], run);
  }
  return best.reduce((sum, value) => sum + value, 0);
}

const findSubstringInWraproundString = solve;
class Solution {
  findSubstringInWraproundString(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findSubstringInWraproundString };
