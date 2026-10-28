'use strict';

// 313. Super Ugly Number (Medium).
// Specification: https://leetcode.com/problems/super-ugly-number/description/
function solve(n, primes) {
  const ugly = [1];
  const indices = new Array(primes.length).fill(0);
  while (ugly.length < n) {
    const next = Math.min(...primes.map((prime, i) => prime * ugly[indices[i]]));
    ugly.push(next);
    for (let i = 0; i < primes.length; i++) { if (primes[i] * ugly[indices[i]] === next) indices[i]++; }
  }
  return ugly[n - 1];
}
const nthSuperUglyNumber = solve;
class Solution { nthSuperUglyNumber(n, primes) { return solve(n, primes); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, nthSuperUglyNumber };
