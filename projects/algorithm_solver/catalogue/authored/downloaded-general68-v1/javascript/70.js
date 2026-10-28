'use strict';

// 70. Climbing Stairs (Easy).
// Specification: https://leetcode.com/problems/climbing-stairs/description/
function solve(n) {
  if (n <= 2) return n;
  let a = 1; let b = 2;
  for (let i = 3; i <= n; i++) { const c = a + b; a = b; b = c; }
  return b;
}
const climbStairs = solve;
class Solution { climbStairs(n) { return solve(n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, climbStairs };
