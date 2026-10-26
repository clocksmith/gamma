'use strict';

// 2999. Count the Number of Powerful Integers.
// Remove the fixed suffix and count bounded prefixes by digit DP; O(log finish + len(s)) time and space. Inputs are preserved.

function solve(start, finish, limit, s) {
  for (const char of s) if (Number(char) > limit) return 0;
  const suffix = BigInt(s), base = 10n ** BigInt(s.length);
  function count(bound) {
    if (bound < suffix) return 0n;
    const maximum = (bound - suffix) / base;
    let less = 0n, equal = 1n;
    for (const char of maximum.toString()) {
      const digit = Number(char);
      less = less * BigInt(limit + 1) + equal * BigInt(Math.min(digit, limit + 1));
      if (digit > limit) equal = 0n;
    }
    return less + equal - (s[0] === '0' ? 1n : 0n);
  }
  return Number(count(BigInt(finish)) - count(BigInt(start) - 1n));
}

const numberOfPowerfulInt = solve;
class Solution {
  numberOfPowerfulInt(start, finish, limit, s) { return solve(start, finish, limit, s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numberOfPowerfulInt };
