'use strict';

// 2036. Maximum Alternating Subarray Sum: track nonempty contiguous sums ending with a plus or minus sign.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(nums) {
  let plus = -Infinity;
  let minus = -Infinity;
  let best = nums[0];
  for (const value of nums) {
    const nextPlus = Math.max(value, minus + value);
    const nextMinus = plus - value;
    plus = nextPlus;
    minus = nextMinus;
    best = Math.max(best, plus, minus);
  }
  return best;
}

const maximumAlternatingSubarraySum = solve;
class Solution {
  maximumAlternatingSubarraySum(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumAlternatingSubarraySum };
