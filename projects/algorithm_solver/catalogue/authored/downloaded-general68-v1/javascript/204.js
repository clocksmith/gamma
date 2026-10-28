'use strict';

// 204. Count Primes (Medium).
// Specification: https://leetcode.com/problems/count-primes/description/
function solve(n) {
  if (n <= 2) return 0;
  const isPrime = new Array(n).fill(true);
  isPrime[0] = false; isPrime[1] = false;
  for (let i = 2; i * i < n; i++) {
    if (isPrime[i]) { for (let j = i * i; j < n; j += i) isPrime[j] = false; }
  }
  return isPrime.filter(Boolean).length;
}
const countPrimes = solve;
class Solution { countPrimes(n) { return solve(n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, countPrimes };
