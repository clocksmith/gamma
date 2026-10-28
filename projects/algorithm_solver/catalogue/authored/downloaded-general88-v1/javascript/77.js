'use strict';

// 77. Combinations (Medium).
// Specification: https://leetcode.com/problems/combinations/description/
function solve(n, k) {
  const result = [];
  function backtrack(start, current) {
    if (current.length === k) { result.push(current.slice()); return; }
    for (let i = start; i <= n; i++) { current.push(i); backtrack(i + 1, current); current.pop(); }
  }
  backtrack(1, []);
  return result;
}
const combine = solve;
class Solution { combine(n, k) { return solve(n, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, combine };
