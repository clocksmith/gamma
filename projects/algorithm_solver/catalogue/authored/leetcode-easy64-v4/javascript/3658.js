'use strict';

// 3658. GCD of Odd and Even Sums (Easy).
// Specification: https://leetcode.com/problems/gcd-of-odd-and-even-sums/description/
// O(1) time and space; gcd(n*n, n*(n+1)) = n.
function solve(n) {
  return n;
}

const gcdOfOddEvenSums = solve;
class Solution {
  gcdOfOddEvenSums(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, gcdOfOddEvenSums };
