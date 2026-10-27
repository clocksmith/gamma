'use strict';

// 3984. Divisible Game.
// Specification: https://leetcode.com/problems/divisible-game/description/
// O(V log log V + n log V) time and O(V) space; prime divisors dominate composite choices, sparse Kadane updates. Inputs are preserved.
function solve(nums) {
  let maximum = 1;
  for (const value of nums) maximum = Math.max(maximum, value);
  const smallest = new Int32Array(maximum + 1);
  for (let prime = 2; prime <= maximum; prime++) {
    if (smallest[prime] !== 0) continue;
    smallest[prime] = prime;
    if (prime * prime <= maximum) for (let multiple = prime * prime; multiple <= maximum; multiple += prime) {
      if (smallest[multiple] === 0) smallest[multiple] = prime;
    }
  }
  const state = new Map();
  let prefix = 0;
  let best = -1;
  let chosen = 2;
  for (const value of nums) {
    let remaining = value;
    while (remaining > 1) {
      const prime = smallest[remaining];
      const old = state.get(prime);
      const ending = old ? Math.max(value, old[0] - (prefix - old[1]) + value) : value;
      state.set(prime, [ending, prefix + value]);
      if (ending > best || (ending === best && prime < chosen)) { best = ending; chosen = prime; }
      while (remaining % prime === 0) remaining /= prime;
    }
    prefix += value;
  }
  const modulus = 1000000007n;
  return Number((BigInt(best) * BigInt(chosen) % modulus + modulus) % modulus);
}

if (typeof module !== 'undefined') module.exports = { solve };
