'use strict';

// 2894. Divisible and Non-divisible Sums Difference (Easy).
// Specification: https://leetcode.com/problems/divisible-and-non-divisible-sums-difference/description/
// O(1) time and space; all arithmetic is exact in the declared integer domain.
function solve(n, m) {
  const multiples = Math.floor(n / m);
  return n * (n + 1) / 2 - m * multiples * (multiples + 1);
}

const differenceOfSums = solve;
class Solution {
  differenceOfSums(n, m) { return solve(n, m); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, differenceOfSums };
