'use strict';

// 788. Rotated Digits (Medium).
// Specification: https://leetcode.com/problems/rotated-digits/description/
function solve(n) {
  const valid = new Set(['0', '1', '2', '5', '6', '8', '9']);
  const changing = new Set(['2', '5', '6', '9']);
  let count = 0;
  for (let value = 1; value <= n; value++) {
    const text = String(value);
    let ok = true; let changed = false;
    for (const ch of text) {
      if (!valid.has(ch)) { ok = false; break; }
      if (changing.has(ch)) changed = true;
    }
    if (ok && changed) count++;
  }
  return count;
}
const rotatedDigits = solve;
class Solution { rotatedDigits(n) { return solve(n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, rotatedDigits };
