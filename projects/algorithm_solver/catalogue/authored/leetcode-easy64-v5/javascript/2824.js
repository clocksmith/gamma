'use strict';

// 2824. Count Pairs Whose Sum is Less than Target (Easy).
// Specification: https://leetcode.com/problems/count-pairs-whose-sum-is-less-than-target/description/
// O(n log n) time, O(n) space; sort a copy and preserve nums.
function solve(nums, target) {
  const ordered = nums.slice().sort((left, right) => left - right);
  let left = 0;
  let right = ordered.length - 1;
  let pairs = 0;
  while (left < right) {
    if (ordered[left] + ordered[right] < target) {
      pairs += right - left;
      left++;
    } else {
      right--;
    }
  }
  return pairs;
}

const countPairs = solve;
class Solution {
  countPairs(nums, target) { return solve(nums, target); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countPairs };
