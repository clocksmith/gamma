'use strict';

// 1176. Diet Plan Performance (Easy).
// Specification: https://leetcode.com/problems/diet-plan-performance/description/
// O(n) time, O(1) space; score every overlapping k-day window with strict bounds.
function solve(calories, k, lower, upper) {
  let total = 0;
  for (let index = 0; index < k; index++) total += calories[index];
  let score = total < lower ? -1 : total > upper ? 1 : 0;
  for (let index = k; index < calories.length; index++) {
    total += calories[index] - calories[index - k];
    if (total < lower) score--;
    else if (total > upper) score++;
  }
  return score;
}

const dietPlanPerformance = solve;
class Solution {
  dietPlanPerformance(calories, k, lower, upper) { return solve(calories, k, lower, upper); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, dietPlanPerformance };
