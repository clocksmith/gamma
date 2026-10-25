'use strict';

// 1567. Maximum Length of Subarray With Positive Product: track positive and negative product suffix lengths.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(nums) {
  let positive = 0;
  let negative = 0;
  let best = 0;
  for (const value of nums) {
    if (value > 0) {
      positive += 1;
      negative = negative > 0 ? negative + 1 : 0;
    } else if (value < 0) {
      const nextPositive = negative > 0 ? negative + 1 : 0;
      negative = positive + 1;
      positive = nextPositive;
    } else {
      positive = 0;
      negative = 0;
    }
    best = Math.max(best, positive);
  }
  return best;
}

const getMaxLen = solve;
class Solution {
  getMaxLen(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, getMaxLen };
