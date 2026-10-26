'use strict';

// 2829. Determine the Minimum Sum of a k-avoiding Array: take the smaller member of each forbidden-sum pair and continue from k.
// O(1) time and O(1) auxiliary space on the bounded integer domain; inputs are read-only.
function solve(n, k) {
  const small = Math.min(n, Math.floor(k / 2));
  const remaining = n - small;
  return small * (small + 1) / 2 + remaining * (2 * k + remaining - 1) / 2;
}

const minimumSum = solve;
class Solution {
  minimumSum(n, k) { return solve(n, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumSum };
