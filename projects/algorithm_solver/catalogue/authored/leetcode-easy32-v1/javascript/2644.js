'use strict';

// 2644. Find the Maximum Divisibility Score (Easy).
// Specification: https://leetcode.com/problems/find-the-maximum-divisibility-score/description/
// O(nums.length * divisors.length) time, O(1) auxiliary space.
function solve(nums, divisors) {
  let bestDivisor = divisors[0];
  let bestScore = -1;
  for (const divisor of divisors) {
    let score = 0;
    for (const value of nums) {
      if (value % divisor === 0) score++;
    }
    if (score > bestScore || (score === bestScore && divisor < bestDivisor)) {
      bestScore = score;
      bestDivisor = divisor;
    }
  }
  return bestDivisor;
}

const maxDivScore = solve;
class Solution {
  maxDivScore(nums, divisors) { return solve(nums, divisors); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxDivScore };
