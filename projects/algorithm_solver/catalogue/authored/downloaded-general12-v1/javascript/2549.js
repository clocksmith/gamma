'use strict';

// 2549. Count Distinct Numbers on Board (Easy).
// Specification: https://leetcode.com/problems/count-distinct-numbers-on-board/description/
function solve(n) {
  // Starting from n, each step adds n-1, then n-2, and so on down to 2;
  // for n = 1 nothing new appears.
  return Math.max(n - 1, 1);
}
const distinctIntegers = solve;
class Solution { distinctIntegers(n) { return solve(n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, distinctIntegers };
