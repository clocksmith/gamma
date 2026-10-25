'use strict';

// 2587. Rearrange Array to Maximize Prefix Score: put larger values first to maximize every prefix.
// O(n log n) time and O(n) auxiliary space; inputs are read-only.
function solve(nums) {
  const values = [...nums].sort((left, right) => right - left);
  let prefix = 0;
  let score = 0;
  for (const value of values) {
    prefix += value;
    if (prefix <= 0) break;
    score += 1;
  }
  return score;
}

const maxScore = solve;
class Solution {
  maxScore(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxScore };
