'use strict';

// 2413. Smallest Even Multiple (Easy).
// Specification: https://leetcode.com/problems/smallest-even-multiple/description/
// O(1) time and space; compute lcm(n, 2) for positive n.
function solve(n) {
  return n % 2 === 0 ? n : 2 * n;
}

const smallestEvenMultiple = solve;
class Solution {
  smallestEvenMultiple(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, smallestEvenMultiple };
