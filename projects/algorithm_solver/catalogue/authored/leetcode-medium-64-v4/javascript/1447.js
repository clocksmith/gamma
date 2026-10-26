'use strict';

// 1447. Simplified Fractions: enumerate proper fractions and retain only coprime numerator-denominator pairs.
// O(n^2 * log(n + 1)) time and O(1) auxiliary space excluding the result; inputs are read-only.
function solve(n) {
  function gcd(first, second) {
    while (second !== 0) {
      const remainder = first % second;
      first = second;
      second = remainder;
    }
    return first;
  }
  const result = [];
  for (let denominator = 2; denominator <= n; denominator += 1) {
    for (let numerator = 1; numerator < denominator; numerator += 1) {
      if (gcd(numerator, denominator) === 1) result.push(`${numerator}/${denominator}`);
    }
  }
  return result;
}

const simplifiedFractions = solve;
class Solution {
  simplifiedFractions(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, simplifiedFractions };
