'use strict';

// 1551. Minimum Operations to Make Array Equal: sum the symmetric deficits of the arithmetic progression.
// O(1) time and O(1) auxiliary space on the bounded integer domain; inputs are read-only.
function solve(n) {
  return Math.floor(n / 2) * Math.ceil(n / 2);
}

const minOperations = solve;
class Solution {
  minOperations(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minOperations };
