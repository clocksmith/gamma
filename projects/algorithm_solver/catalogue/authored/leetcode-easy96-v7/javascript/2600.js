'use strict';

// 2600. K Items With the Maximum Sum (Easy).
// Specification: https://leetcode.com/problems/k-items-with-the-maximum-sum/description/
// O(1) time and space; take ones, then zeros, then negative ones; k does not exceed available items.
function solve(numOnes, numZeros, numNegOnes, k) {
  const positive = Math.min(k, numOnes);
  const negative = Math.max(0, k - numOnes - numZeros);
  return positive - negative;
}

const kItemsWithMaximumSum = solve;
class Solution {
  kItemsWithMaximumSum(numOnes, numZeros, numNegOnes, k) { return solve(numOnes, numZeros, numNegOnes, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, kItemsWithMaximumSum };
