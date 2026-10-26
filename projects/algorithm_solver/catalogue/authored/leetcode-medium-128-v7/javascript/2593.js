'use strict';

// 2593. Find Score of an Array After Marking All Elements: visit indices in value-and-index order and mark neighboring positions.
// O(n log n) time and O(n) auxiliary space; inputs are read-only.
function solve(nums) {
  const order = Array.from({ length: nums.length }, (_, index) => index)
    .sort((left, right) => nums[left] - nums[right] || left - right);
  const marked = new Uint8Array(nums.length);
  let score = 0;
  for (const index of order) {
    if (marked[index]) continue;
    score += nums[index];
    marked[index] = 1;
    if (index > 0) marked[index - 1] = 1;
    if (index + 1 < nums.length) marked[index + 1] = 1;
  }
  return score;
}

const findScore = solve;
class Solution {
  findScore(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findScore };
