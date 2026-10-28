'use strict';

// 786. K-th Smallest Prime Fraction (Medium).
// Specification: https://leetcode.com/problems/k-th-smallest-prime-fraction/description/
function solve(arr, k) {
  const fractions = [];
  for (let i = 0; i < arr.length; i++) {
    for (let j = i + 1; j < arr.length; j++) fractions.push([arr[i] / arr[j], arr[i], arr[j]]);
  }
  fractions.sort((a, b) => a[0] - b[0]);
  return [fractions[k - 1][1], fractions[k - 1][2]];
}
const kthSmallestPrimeFraction = solve;
class Solution { kthSmallestPrimeFraction(arr, k) { return solve(arr, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, kthSmallestPrimeFraction };
