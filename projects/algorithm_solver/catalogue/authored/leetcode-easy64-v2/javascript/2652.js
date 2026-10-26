'use strict';

// 2652. Sum Multiples (Easy).
// Specification: https://leetcode.com/problems/sum-multiples/description/
// O(1) time and space; inclusion-exclusion over multiples of 3, 5, and 7.
function solve(n) {
  function sumDivisible(divisor) {
    const count = Math.floor(n / divisor);
    return divisor * count * (count + 1) / 2;
  }
  return sumDivisible(3) + sumDivisible(5) + sumDivisible(7)
    - sumDivisible(15) - sumDivisible(21) - sumDivisible(35)
    + sumDivisible(105);
}

const sumOfMultiples = solve;
class Solution {
  sumOfMultiples(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, sumOfMultiples };
