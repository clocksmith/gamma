'use strict';

// 1911. Maximum Alternating Subsequence Sum: track the best alternating sum for each final sign.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(nums) {
  let added = 0;
  let subtracted = 0;
  for (const value of nums) {
    const nextAdded = Math.max(added, subtracted + value);
    const nextSubtracted = Math.max(subtracted, added - value);
    added = nextAdded;
    subtracted = nextSubtracted;
  }
  return added;
}

const maxAlternatingSum = solve;
class Solution {
  maxAlternatingSum(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxAlternatingSum };
