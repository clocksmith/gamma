'use strict';

// 1881. Maximum Value after Insertion (Medium).
// Specification: https://leetcode.com/problems/maximum-value-after-insertion/description/
function solve(n, x) {
  const negative = n[0] === '-';
  const digit = String(x);
  for (let i = 0; i < n.length; i++) {
    const ch = n[i];
    if (ch === '-') continue;
    if (!negative && ch < digit) return n.slice(0, i) + digit + n.slice(i);
    if (negative && ch > digit) return n.slice(0, i) + digit + n.slice(i);
  }
  return n + digit;
}
const maxValue = solve;
class Solution { maxValue(n, x) { return solve(n, x); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxValue };
