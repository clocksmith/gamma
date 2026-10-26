'use strict';

// 3684. Maximize Sum of At Most K Distinct Elements (Easy).
// Specification: https://leetcode.com/problems/maximize-sum-of-at-most-k-distinct-elements/description/
// O(n + u * log(u + 1)) expected time, O(u) space; preserve nums; output descending values.
function solve(nums, k) {
  const values = Array.from(new Set(nums));
  values.sort((left, right) => right - left);
  return values.slice(0, k);
}

const maxKDistinct = solve;
class Solution {
  maxKDistinct(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxKDistinct };
