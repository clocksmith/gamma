'use strict';

// 2281. Sum of Total Strength of Wizards.
// Monotonic minimum boundaries and prefix-of-prefix sums; O(n) time and space. Inputs are preserved; modular products are exact.

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

function solve(strength) {
  const n = strength.length, left = Array(n).fill(-1), right = Array(n).fill(n), stack = [];
  for (let i = 0; i < n; i += 1) {
    while (stack.length > 0 && strength[stack[stack.length - 1]] >= strength[i]) right[stack.pop()] = i;
    if (stack.length > 0) left[i] = stack[stack.length - 1];
    stack.push(i);
  }
  const prefix = [0], twice = [0];
  for (const value of strength) prefix.push((prefix[prefix.length - 1] + value) % MOD);
  for (const value of prefix) twice.push((twice[twice.length - 1] + value) % MOD);
  let answer = 0;
  for (let i = 0; i < n; i += 1) {
    const a = left[i], b = right[i];
    const positive = multiplyMod(i - a, (twice[b + 1] - twice[i + 1] + MOD) % MOD);
    const negative = multiplyMod(b - i, (twice[i + 1] - twice[a + 1] + MOD) % MOD);
    answer = (answer + multiplyMod(strength[i], (positive - negative + MOD) % MOD)) % MOD;
  }
  return answer;
}

const totalStrength = solve;
class Solution {
  totalStrength(strength) { return solve(strength); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, totalStrength };
