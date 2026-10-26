'use strict';

// 1099. Two Sum Less Than K (Easy).
// Specification: https://leetcode.com/problems/two-sum-less-than-k/description/
// O(n log n) time, O(n) space; two pointers on a sorted copy with a strict sum limit.
function solve(nums, k) {
  const values = nums.slice().sort((a, b) => a - b);
  let left = 0;
  let right = values.length - 1;
  let best = -1;
  while (left < right) {
    const total = values[left] + values[right];
    if (total < k) {
      best = Math.max(best, total);
      left++;
    } else {
      right--;
    }
  }
  return best;
}

const twoSumLessThanK = solve;
class Solution {
  twoSumLessThanK(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, twoSumLessThanK };
