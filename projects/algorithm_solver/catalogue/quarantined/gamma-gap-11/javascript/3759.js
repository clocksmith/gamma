'use strict';

// 3759. Count Elements With at Least K Greater Values.
// O(n log n) time and O(n) space; count strictly smaller than the kth largest value.
function solve(nums, k) {
  if (k === 0) return nums.length;
  const ordered = nums.slice().sort((left, right) => left - right);
  const threshold = ordered[nums.length - k];
  let answer = 0;
  for (const value of nums) if (value < threshold) answer += 1;
  return answer;
}

const countElements = solve;
class Solution {
  countElements(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countElements };
