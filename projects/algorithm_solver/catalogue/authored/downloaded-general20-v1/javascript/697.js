'use strict';

// 697. Degree of an Array (Easy).
// Specification: https://leetcode.com/problems/degree-of-an-array/description/
function solve(nums) {
  const first = new Map();
  const last = new Map();
  const count = new Map();
  let degree = 0;
  for (let index = 0; index < nums.length; index++) {
    const value = nums[index];
    if (!first.has(value)) first.set(value, index);
    last.set(value, index);
    count.set(value, (count.get(value) || 0) + 1);
    degree = Math.max(degree, count.get(value));
  }
  let shortest = nums.length;
  for (const [value, occurrences] of count) {
    if (occurrences === degree) shortest = Math.min(shortest, last.get(value) - first.get(value) + 1);
  }
  return shortest;
}

const findShortestSubArray = solve;
class Solution {
  findShortestSubArray(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findShortestSubArray };
