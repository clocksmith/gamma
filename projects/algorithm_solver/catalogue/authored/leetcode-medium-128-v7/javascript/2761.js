'use strict';

// 2761. Prime Pairs With Target Sum: sieve primality once and enumerate the smaller endpoint of each pair.
// O(n log log(n + 2)) time and O(n) auxiliary space; inputs are read-only.
function solve(n) {
  const prime = new Uint8Array(n + 1).fill(1);
  prime[0] = 0;
  if (n >= 1) prime[1] = 0;
  for (let factor = 2; factor * factor <= n; factor += 1) {
    if (!prime[factor]) continue;
    for (let multiple = factor * factor; multiple <= n; multiple += factor) prime[multiple] = 0;
  }
  const result = [];
  for (let left = 2; left <= Math.floor(n / 2); left += 1) {
    if (prime[left] && prime[n - left]) result.push([left, n - left]);
  }
  return result;
}

const findPrimePairs = solve;
class Solution {
  findPrimePairs(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findPrimePairs };
