'use strict';

// 3098. Find the Sum of Subsequence Powers.
// Integrate counts of subsequences above each possible minimum gap; O(k*n^3) time, O(n^2) space. Inputs are preserved; no floating-point products.

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
  const values = nums.slice().sort((a, b) => a - b), n = values.length, distinct = new Set([0]);
  for (let i = 0; i < n; i += 1) for (let j = i + 1; j < n; j += 1) distinct.add(values[j] - values[i]);
  const gaps = [...distinct].sort((a, b) => a - b);
  let answer = 0, previousGap = 0;
  for (let g = 1; g < gaps.length; g += 1) {
    const gap = gaps[g], eligible = Array(n).fill(0);
    let left = 0;
    for (let index = 0; index < n; index += 1) {
      while (left < index && values[left] <= values[index] - gap) left += 1;
      eligible[index] = left;
    }
    let ways = Array(n).fill(1);
    for (let count = 2; count <= k; count += 1) {
      const prefix = [0];
      for (const value of ways) prefix.push((prefix[prefix.length - 1] + value) % MOD);
      ways = eligible.map(end => prefix[end]);
    }
    const total = ways.reduce((sum, value) => (sum + value) % MOD, 0);
    answer = (answer + multiplyMod((gap - previousGap) % MOD, total)) % MOD;
    previousGap = gap;
  }
  return answer;
}

const sumOfPowers = solve;
class Solution {
  sumOfPowers(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, sumOfPowers };
