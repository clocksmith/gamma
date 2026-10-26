'use strict';

// 2897. Apply Operations on Array to Maximize Sum of Squares.
// Concentrate available bits into the k largest constructible values; O(30*(n+k)) time, O(30) space. Inputs are preserved.

const MOD = 1000000007;
// Split multiplication keeps every intermediate integer below 2^53.
function multiplyMod(a, b) {
  return (a * (b % 32768) + ((a * Math.floor(b / 32768)) % MOD) * 32768) % MOD;
}
function powerMod(base, exponent) {
  let result = 1;
  while (exponent > 0) {
    if (exponent % 2 === 1) result = multiplyMod(result, base);
    base = multiplyMod(base, base);
    exponent = Math.floor(exponent / 2);
  }
  return result;
}

function solve(nums, k) {
  const counts = Array(30).fill(0);
  for (const value of nums) for (let bit = 0; bit < 30; bit += 1) counts[bit] += (value >>> bit) & 1;
  let answer = 0;
  for (let index = 0; index < k; index += 1) {
    let value = 0;
    for (let bit = 0; bit < 30; bit += 1) if (counts[bit] > 0) { counts[bit] -= 1; value += 2 ** bit; }
    answer = (answer + multiplyMod(value, value)) % MOD;
  }
  return answer;
}

const maxSum = solve;
class Solution {
  maxSum(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxSum };
