'use strict';

// 2200. Find All K-Distant Indices in an Array (Easy).
// Specification: https://leetcode.com/problems/find-all-k-distant-indices-in-an-array/description/
// O(n) time and output space; append each covered index once by merging increasing intervals.
function solve(nums, key, k) {
  const result = [];
  let nextIndex = 0;
  for (let index = 0; index < nums.length; index++) {
    if (nums[index] !== key) continue;
    const start = Math.max(nextIndex, index - k, 0);
    const end = Math.min(nums.length - 1, index + k);
    for (let covered = start; covered <= end; covered++) result.push(covered);
    nextIndex = end + 1;
  }
  return result;
}

const findKDistantIndices = solve;
class Solution {
  findKDistantIndices(nums, key, k) { return solve(nums, key, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findKDistantIndices };
