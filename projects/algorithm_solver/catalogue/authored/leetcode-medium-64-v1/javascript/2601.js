'use strict';

// 2601. Prime Subtraction Operation: greedily choose the smallest feasible next value using a sieve and predecessor search.
// O(M * log(log(M + 2)) + n * log(M + 1)) time and O(M) space for M = max(nums); inputs are read-only.
function solve(nums) {
  let maximum = 0;
  for (const value of nums) maximum = Math.max(maximum, value);
  const isPrime = new Uint8Array(maximum + 1).fill(1);
  isPrime[0] = 0;
  isPrime[1] = 0;
  for (let factor = 2; factor * factor <= maximum; factor += 1) {
    if (!isPrime[factor]) continue;
    for (let multiple = factor * factor; multiple <= maximum; multiple += factor) isPrime[multiple] = 0;
  }
  const primes = [];
  for (let value = 2; value <= maximum; value += 1) if (isPrime[value]) primes.push(value);
  let previous = 0;
  for (const original of nums) {
    const limit = original - previous;
    let low = 0;
    let high = primes.length;
    while (low < high) {
      const middle = Math.floor((low + high) / 2);
      if (primes[middle] < limit) low = middle + 1;
      else high = middle;
    }
    const value = low > 0 ? original - primes[low - 1] : original;
    if (value <= previous) return false;
    previous = value;
  }
  return true;
}

const primeSubOperation = solve;
class Solution {
  primeSubOperation(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, primeSubOperation };
