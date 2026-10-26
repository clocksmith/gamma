'use strict';

// 2523. Closest Prime Numbers in Range: sieve the interval ceiling and compare adjacent primes in increasing order.
// O(right log log(right + 2)) time and O(right) auxiliary space; inputs are read-only.
function solve(left, right) {
  const prime = new Uint8Array(right + 1).fill(1);
  prime[0] = 0;
  if (right >= 1) prime[1] = 0;
  for (let factor = 2; factor * factor <= right; factor += 1) {
    if (!prime[factor]) continue;
    for (let multiple = factor * factor; multiple <= right; multiple += factor) prime[multiple] = 0;
  }
  let previous = -1;
  let bestGap = right + 1;
  let answer = [-1, -1];
  for (let value = Math.max(left, 2); value <= right; value += 1) {
    if (!prime[value]) continue;
    if (previous !== -1 && value - previous < bestGap) {
      bestGap = value - previous;
      answer = [previous, value];
    }
    previous = value;
  }
  return answer;
}

const closestPrimes = solve;
class Solution {
  closestPrimes(left, right) { return solve(left, right); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, closestPrimes };
