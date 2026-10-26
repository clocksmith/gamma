'use strict';

// 2427. Number of Common Factors (Easy).
// Specification: https://leetcode.com/problems/number-of-common-factors/description/
// O(log(min(a,b)) + sqrt(gcd(a,b))) time, O(1) space; count divisors of the gcd.
function solve(a, b) {
  let first = a;
  let second = b;
  while (second !== 0) [first, second] = [second, first % second];
  let count = 0;
  for (let divisor = 1; divisor * divisor <= first; divisor++) {
    if (first % divisor === 0) count += divisor * divisor === first ? 1 : 2;
  }
  return count;
}

const commonFactors = solve;
class Solution {
  commonFactors(a, b) { return solve(a, b); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, commonFactors };
