'use strict';

// 2417. Closest Fair Integer (Medium).
// Specification: https://leetcode.com/problems/closest-fair-integer/description/
function solve(n) {
  const isFair = (x) => {
    const s = String(x);
    if (s.length % 2 === 1) return false;
    let odd = 0, even = 0;
    for (const ch of s) { if (Number(ch) % 2 === 1) odd++; else even++; }
    return odd === even;
  };
  let n0 = n;
  while (true) {
    if (isFair(n0)) return n0;
    const k = String(n0).length;
    if (k % 2 === 1) {
      const ones = '1'.repeat(k >> 1);
      return Math.pow(10, k) + (ones === '' ? 0 : Number(ones));
    }
    n0++;
  }
}
const closestFair = solve;
class Solution { closestFair(n) { return solve(n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, closestFair };
