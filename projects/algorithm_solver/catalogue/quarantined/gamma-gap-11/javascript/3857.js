'use strict';

// 3857. Minimum Cost to Split into Ones.
// O(1) time and space; every split removes exactly a*b unordered pairs, telescoping to n choose 2.
function solve(n) {
  return n * (n - 1) / 2;
}

const minCost = solve;
class Solution {
  minCost(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minCost };
