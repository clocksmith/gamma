'use strict';

// 1175. Prime Arrangements (Easy).
// Specification: https://leetcode.com/problems/prime-arrangements/description/
// O(n log log n) time, O(n) space; multiply factorial factors individually to retain exact JS integers.
function solve(n) {
  const prime = new Array(n + 1).fill(true);
  prime[0] = false;
  prime[1] = false;
  for (let value = 2; value * value <= n; value++) {
    if (!prime[value]) continue;
    for (let multiple = value * value; multiple <= n; multiple += value) prime[multiple] = false;
  }
  let primeCount = 0;
  for (let value = 2; value <= n; value++) {
    if (prime[value]) primeCount++;
  }
  const modulus = 1000000007;
  let result = 1;
  for (let factor = 2; factor <= primeCount; factor++) result = (result * factor) % modulus;
  for (let factor = 2; factor <= n - primeCount; factor++) result = (result * factor) % modulus;
  return result;
}

const numPrimeArrangements = solve;
class Solution {
  numPrimeArrangements(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numPrimeArrangements };
