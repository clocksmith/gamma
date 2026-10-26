'use strict';

// 2190. Most Frequent Number Following Key In an Array (Easy).
// Specification: https://leetcode.com/problems/most-frequent-number-following-key-in-an-array/description/
// O(n) expected time, O(n) space; count immediate successors; the public domain guarantees a unique answer.
function solve(nums, key) {
  const counts = new Map();
  let best = -1;
  let largestCount = 0;
  for (let index = 0; index + 1 < nums.length; index++) {
    if (nums[index] !== key) continue;
    const value = nums[index + 1];
    const count = (counts.get(value) || 0) + 1;
    counts.set(value, count);
    if (count > largestCount) {
      largestCount = count;
      best = value;
    }
  }
  return best;
}

const mostFrequent = solve;
class Solution {
  mostFrequent(nums, key) { return solve(nums, key); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, mostFrequent };
