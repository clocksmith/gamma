'use strict';

// 2831. Find the Longest Equal Subarray: slide over positions of each value while limiting intervening deletions.
// O(n) expected time and O(n) auxiliary space; inputs are read-only.
function solve(nums, k) {
  const positions = new Map();
  for (let index = 0; index < nums.length; index += 1) {
    if (!positions.has(nums[index])) positions.set(nums[index], []);
    positions.get(nums[index]).push(index);
  }
  let best = 0;
  for (const indices of positions.values()) {
    let left = 0;
    for (let right = 0; right < indices.length; right += 1) {
      while (indices[right] - indices[left] - (right - left) > k) left += 1;
      best = Math.max(best, right - left + 1);
    }
  }
  return best;
}

const longestEqualSubarray = solve;
class Solution {
  longestEqualSubarray(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestEqualSubarray };
