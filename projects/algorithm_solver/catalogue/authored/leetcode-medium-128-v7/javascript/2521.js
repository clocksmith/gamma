'use strict';

// 2521. Distinct Prime Factors of Product of Array: factor each input separately and collect its distinct prime divisors.
// O(n * sqrt(M)) time and O(n log(M + 1)) auxiliary space, where M is the largest value; inputs are read-only.
function solve(nums) {
  const primes = new Set();
  for (const original of nums) {
    let value = original;
    for (let factor = 2; factor * factor <= value; factor += 1) {
      if (value % factor === 0) {
        primes.add(factor);
        while (value % factor === 0) value /= factor;
      }
    }
    if (value > 1) primes.add(value);
  }
  return primes.size;
}

const distinctPrimeFactors = solve;
class Solution {
  distinctPrimeFactors(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, distinctPrimeFactors };
