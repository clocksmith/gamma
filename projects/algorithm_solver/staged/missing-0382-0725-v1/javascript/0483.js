'use strict';

// 483. Smallest Good Base. Search digit counts and bases using exact geometric-series comparisons.

function solve(n) {
  const number = BigInt(n), bits = number.toString(2).length;
  for (let exponent = bits - 1; exponent >= 2; exponent -= 1) {
    let low = 2n, high = 1n << BigInt(Math.ceil(bits / exponent));
    if (high >= number) high = number - 1n;
    while (low <= high) {
      const base = (low + high) / 2n;
      let total = 1n;
      for (let i = 0; i < exponent; i += 1) {
        total = total * base + 1n;
        if (total > number) break;
      }
      if (total === number) return String(base);
      if (total < number) low = base + 1n;
      else high = base - 1n;
    }
  }
  return String(number - 1n);
}

const smallestGoodBase = solve;
class Solution {
  smallestGoodBase(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, smallestGoodBase };
