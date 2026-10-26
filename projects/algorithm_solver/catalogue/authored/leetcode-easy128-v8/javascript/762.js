'use strict';

// 762. Prime Number of Set Bits in Binary Representation (Easy).
// Specification: https://leetcode.com/problems/prime-number-of-set-bits-in-binary-representation/description/
// O((right - left + 1) * log right) time, O(1) space under the stated range up to 10^6.
function solve(left, right) {
  const primes = new Set([2, 3, 5, 7, 11, 13, 17, 19]);
  let result = 0;
  for (let value = left; value <= right; value++) {
    let remaining = value;
    let count = 0;
    while (remaining > 0) {
      count += remaining % 2;
      remaining = Math.floor(remaining / 2);
    }
    if (primes.has(count)) result++;
  }
  return result;
}

const countPrimeSetBits = solve;
class Solution {
  countPrimeSetBits(left, right) { return solve(left, right); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countPrimeSetBits };
