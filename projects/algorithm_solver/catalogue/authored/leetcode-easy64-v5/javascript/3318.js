'use strict';

// 3318. Find X-Sum of All K-Long Subarrays I (Easy).
// Specification: https://leetcode.com/problems/find-x-sum-of-all-k-long-subarrays-i/description/
// O(n * k log(k + 1)) time, O(n + k) space; rank by descending frequency, then value.
function solve(nums, k, x) {
  const result = [];
  for (let start = 0; start + k <= nums.length; start++) {
    const counts = new Map();
    for (let index = start; index < start + k; index++) {
      counts.set(nums[index], (counts.get(nums[index]) || 0) + 1);
    }
    const ranked = Array.from(counts.entries());
    ranked.sort((left, right) => right[1] - left[1] || right[0] - left[0]);
    let total = 0;
    for (let index = 0; index < Math.min(x, ranked.length); index++) {
      total += ranked[index][0] * ranked[index][1];
    }
    result.push(total);
  }
  return result;
}

const findXSum = solve;
class Solution {
  findXSum(nums, k, x) { return solve(nums, k, x); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findXSum };
