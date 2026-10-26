'use strict';

// 1304. Find N Unique Integers Sum up to Zero (Easy).
// Specification: https://leetcode.com/problems/find-n-unique-integers-sum-up-to-zero/description/
// O(n) time and result space; deterministic opposite pairs, then zero if needed.
function solve(n) {
  const result = [];
  for (let value = 1; value <= Math.floor(n / 2); value++) {
    result.push(-value, value);
  }
  if (n % 2 === 1) result.push(0);
  return result;
}

const sumZero = solve;
class Solution {
  sumZero(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, sumZero };
