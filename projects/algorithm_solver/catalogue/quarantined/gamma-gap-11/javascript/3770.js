'use strict';

// 3770. Largest Prime from Consecutive Prime Sum.
// O(n log log n) time and O(n) space; sum consecutive primes beginning at 2.
function solve(n) {
  if (n < 2) return 0;
  const prime = new Uint8Array(n + 1).fill(1);
  prime[0] = 0;
  prime[1] = 0;
  for (let divisor = 2; divisor * divisor <= n; divisor += 1) {
    if (!prime[divisor]) continue;
    for (let multiple = divisor * divisor; multiple <= n; multiple += divisor) prime[multiple] = 0;
  }
  let total = 0;
  let answer = 0;
  for (let value = 2; value <= n; value += 1) {
    if (!prime[value]) continue;
    total += value;
    if (total > n) break;
    if (prime[total]) answer = total;
  }
  return answer;
}

const largestPrime = solve;
class Solution {
  largestPrime(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, largestPrime };
