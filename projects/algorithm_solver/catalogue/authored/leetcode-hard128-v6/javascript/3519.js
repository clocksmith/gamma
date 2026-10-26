'use strict';

// 3519. Count Numbers with Non-Decreasing Digits.
// Convert decimal bounds exactly and count bounded non-decreasing base-b digits; O(L*b^2) digit-DP time and O(L+b) space, excluding big-integer conversion. Inputs are preserved.

function solve(l, r, b) {
  const modulus = 1000000007;
  function countThrough(bound) {
    if (bound < 0n) return 0;
    const digits = bound.toString(b).split('').map(Number);
    let ways = Array.from({ length: b }, () => [0, 0]);
    ways[0][1] = 1;
    for (const limitDigit of digits) {
      const following = Array.from({ length: b }, () => [0, 0]);
      for (let previous = 0; previous < b; previous += 1) {
        for (let tight = 0; tight < 2; tight += 1) {
          const count = ways[previous][tight];
          if (count === 0) continue;
          const limit = tight ? limitDigit : b - 1;
          for (let digit = previous; digit <= limit; digit += 1) {
            const nextTight = tight && digit === limitDigit ? 1 : 0;
            following[digit][nextTight] = (following[digit][nextTight] + count) % modulus;
          }
        }
      }
      ways = following;
    }
    return ways.reduce((sum, row) => (sum + row[0] + row[1]) % modulus, 0);
  }
  return (countThrough(BigInt(r)) - countThrough(BigInt(l) - 1n) + modulus) % modulus;
}

const countNumbers = solve;
class Solution {
  countNumbers(l, r, b) { return solve(l, r, b); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countNumbers };
