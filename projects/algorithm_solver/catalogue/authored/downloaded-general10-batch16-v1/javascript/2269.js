'use strict';

// 2269. Find the K-Beauty of a Number (Easy).
// Specification: https://leetcode.com/problems/find-the-k-beauty-of-a-number/description/
function solve(num, k) {
  const s = String(num);
  let count = 0;
  for (let i = 0; i + k <= s.length; i++) {
    const v = parseInt(s.slice(i, i + k), 10);
    if (v !== 0 && num % v === 0) count++;
  }
  return count;
}
const divisorSubstrings = solve;
class Solution { divisorSubstrings(num, k) { return solve(num, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, divisorSubstrings };
